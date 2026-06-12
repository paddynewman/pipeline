import os
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

    def _run(self):
        while not self._stop_event.is_set():
            changed = self._check_for_changes()
            if changed:
                self.callback(self.job)
            self._stop_event.wait(self.poll_interval)

    def _check_for_changes(self):
        git_cfg = self.job.get("git")
        if not git_cfg or not git_cfg.get("url"):
            return False
        branch = git_cfg.get("branch", "main")
        url = git_cfg["url"]
        git_env, ssh_key_path = self.job_manager._git_checkout_env(git_cfg)
        try:
            cmd = ["git", "ls-remote", url, f"refs/heads/{branch}"]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30, env=git_env
            )
            if result.returncode != 0:
                return False
            line = result.stdout.strip()
            if not line:
                return False
            commit_hash = line.split()[0]
            if self._last_hash is None:
                self._last_hash = commit_hash
            elif self._last_hash != commit_hash:
                self._last_hash = commit_hash
                return True
        except subprocess.TimeoutExpired:
            return False
        finally:
            if ssh_key_path and os.path.exists(ssh_key_path):
                os.remove(ssh_key_path)
        return False
