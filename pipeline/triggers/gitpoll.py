import os
import time
import threading
import subprocess


class GitPollTrigger:
    def __init__(self, job_manager, poll_interval, job, callback):
        self.job_manager = job_manager
        self.poll_interval = poll_interval
        self.job = job
        self.callback = callback
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._last_hash = None

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join()

    def _log(self, message):
        path = self.job_manager._git_poll_log_path(self.job["name"])
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "a") as f:
                f.write(f"[{ts}] {message}\n")
            self._trim_log(path)
        except OSError:
            pass

    def _trim_log(self, path):
        try:
            with open(path, errors="replace") as f:
                lines = f.readlines()
        except OSError:
            return
        max_lines = self.job_manager.get_git_poll_log_max_lines()
        if len(lines) <= max_lines:
            return
        try:
            with open(path, "w") as f:
                f.writelines(lines[-max_lines:])
        except OSError:
            pass

    def _run(self):
        self._log("Git polling started (interval: %d seconds)." % self.poll_interval)
        while not self._stop_event.is_set():
            changed = self._check_for_changes()
            if changed:
                self._log("Triggering a new build.")
                self.callback(self.job)
            self._stop_event.wait(self.poll_interval)
        self._log("Git polling stopped.")

    def _check_for_changes(self):
        git_cfg = self.job.get("git")
        if not git_cfg or not git_cfg.get("url"):
            self._log("No Git repository configured; skipping poll.")
            return False
        branch = git_cfg.get("branch", "main")
        url = git_cfg["url"]
        git_env, ssh_key_path = self.job_manager._git_checkout_env(git_cfg)
        try:
            cmd = ["git", "ls-remote", url, f"refs/heads/{branch}"]
            self._log("$ " + " ".join(cmd))
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30, env=git_env
            )
            if result.returncode != 0:
                stderr = (result.stderr or "").strip()
                self._log(
                    "git ls-remote failed (exit %d): %s"
                    % (result.returncode, stderr or "no error output")
                )
                return False
            line = result.stdout.strip()
            if not line:
                self._log("Branch '%s' not found on remote." % branch)
                return False
            commit_hash = line.split()[0]
            self._log("Remote %s is at %s." % (branch, commit_hash))
            if self._last_hash is None:
                self._last_hash = commit_hash
                self._log("Recorded initial revision; no build triggered.")
            elif self._last_hash != commit_hash:
                self._log("Change detected: %s -> %s." % (self._last_hash, commit_hash))
                self._last_hash = commit_hash
                return True
            else:
                self._log("No changes since last poll.")
        except subprocess.TimeoutExpired:
            self._log("git ls-remote timed out after 30 seconds.")
            return False
        finally:
            if ssh_key_path and os.path.exists(ssh_key_path):
                os.remove(ssh_key_path)
        return False
