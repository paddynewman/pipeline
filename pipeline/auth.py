import hashlib
import hmac
import json
import os
import secrets

from .jsonio import write_json

_ITERATIONS = 260_000
_SESSION_BYTES = 32
_VALID_ROLES = {"admin", "user", "viewer"}


def _hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), _ITERATIONS
    )
    return salt, dk.hex()


def _verify_password(password, salt, stored_hash):
    _, candidate = _hash_password(password, salt)
    return hmac.compare_digest(candidate, stored_hash)


class AuthManager:
    def __init__(self, data_dir):
        self.users_path = os.path.join(data_dir, "users.json")
        self._sessions = {}  # token -> username

    # ── User management ──────────────────────────────────────────────────────

    def _load_users(self):
        if not os.path.isfile(self.users_path):
            return {}
        with open(self.users_path) as f:
            users = json.load(f)
        changed = False
        for username, entry in users.items():
            if not isinstance(entry, dict):
                continue
            role = entry.get("role")
            if role not in _VALID_ROLES:
                entry["role"] = "admin"
                changed = True
        if changed:
            self._save_users(users)
        return users

    def _save_users(self, users):
        write_json(self.users_path, users)

    def has_users(self):
        users = self._load_users()
        return bool(users)

    def add_user(self, username, password, role="user"):
        users = self._load_users()
        salt, hashed = _hash_password(password)
        if role not in _VALID_ROLES:
            role = "user"
        users[username] = {"salt": salt, "hash": hashed, "role": role}
        self._save_users(users)

    def verify_user(self, username, password):
        users = self._load_users()
        entry = users.get(username)
        if not entry:
            return False
        if entry.get("disabled"):
            return False
        return _verify_password(password, entry["salt"], entry["hash"])

    def list_users(self):
        return list(self._load_users().keys())

    def list_user_records(self):
        users = self._load_users()
        records = []
        for username in users:
            records.append(
                {
                    "username": username,
                    "role": users[username].get("role", "admin"),
                    "disabled": bool(users[username].get("disabled", False)),
                }
            )
        return records

    def get_user_role(self, username):
        users = self._load_users()
        entry = users.get(username) or {}
        role = entry.get("role")
        if role in _VALID_ROLES:
            return role
        return None

    def delete_user(self, username):
        users = self._load_users()
        users.pop(username, None)
        self._save_users(users)

    def change_password(self, username, new_password):
        users = self._load_users()
        if username not in users:
            return False
        salt, hashed = _hash_password(new_password)
        users[username] = {
            "salt": salt,
            "hash": hashed,
            "role": users[username].get("role", "admin"),
        }
        self._save_users(users)
        return True

    def get_user_disabled(self, username):
        users = self._load_users()
        entry = users.get(username) or {}
        return bool(entry.get("disabled", False))

    def set_user_disabled(self, username, disabled):
        users = self._load_users()
        if username not in users:
            return False
        users[username]["disabled"] = bool(disabled)
        self._save_users(users)
        return True

    def set_user_role(self, username, role):
        users = self._load_users()
        if username not in users:
            return False, "User not found."
        if role not in _VALID_ROLES:
            return False, "Invalid role."

        current_role = users[username].get("role", "admin")
        if current_role == role:
            return True, None

        if current_role == "admin" and role != "admin":
            admin_count = 0
            for entry in users.values():
                if isinstance(entry, dict) and entry.get("role", "admin") == "admin":
                    admin_count += 1
            if admin_count <= 1:
                return False, "At least one administrator is required."

        users[username]["role"] = role
        self._save_users(users)
        return True, None

    # ── Session management ───────────────────────────────────────────────────

    def create_session(self, username):
        token = secrets.token_hex(_SESSION_BYTES)
        self._sessions[token] = username
        return token

    def get_session_user(self, token):
        return self._sessions.get(token)

    def destroy_session(self, token):
        self._sessions.pop(token, None)
