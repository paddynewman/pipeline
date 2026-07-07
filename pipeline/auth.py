import hashlib
import hmac
import secrets


class AuthService:
    def __init__(self, store):
        self.store = store
        self.store.load("users", {"users": []})

    def _users_payload(self):
        return self.store.load("users", {"users": []})

    def has_users(self):
        payload = self.store.load("users", {"users": []})
        return bool(payload.get("users", []))

    def list_users(self):
        payload = self._users_payload()
        users = []
        for item in payload.get("users", []):
            users.append({"username": item.get("username", "")})
        return sorted(users, key=lambda item: item.get("username", ""))

    def _new_salt(self):
        return secrets.token_hex(16)

    def _hash_password(self, password, salt):
        value = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            200000,
        )
        return value.hex()

    def user_exists(self, username):
        payload = self._users_payload()
        for item in payload.get("users", []):
            if item.get("username") == username:
                return True
        return False

    def create_user(self, username, password):
        username = (username or "").strip()
        if not username:
            raise ValueError("Username is required.")
        if not password:
            raise ValueError("Password is required.")
        if self.user_exists(username):
            raise ValueError("Username already exists.")

        payload = self._users_payload()
        users = payload.get("users", [])
        salt = self._new_salt()
        users.append(
            {
                "username": username,
                "salt": salt,
                "password_hash": self._hash_password(password, salt),
            }
        )
        users = sorted(users, key=lambda item: item.get("username", ""))
        self.store.save("users", {"users": users})

    def set_password(self, username, password):
        username = (username or "").strip()
        if not username:
            raise ValueError("Username is required.")
        if not password:
            raise ValueError("Password is required.")

        payload = self._users_payload()
        users = payload.get("users", [])
        updated = False

        for item in users:
            if item.get("username") == username:
                salt = self._new_salt()
                item["salt"] = salt
                item["password_hash"] = self._hash_password(password, salt)
                updated = True
                break

        if not updated:
            raise ValueError("User does not exist.")

        self.store.save("users", {"users": users})

    def delete_user(self, username):
        username = (username or "").strip()
        payload = self._users_payload()
        users = payload.get("users", [])

        filtered = [item for item in users if item.get("username") != username]
        if len(filtered) == len(users):
            raise ValueError("User does not exist.")
        if not filtered:
            raise ValueError("At least one user must remain.")

        self.store.save("users", {"users": filtered})

    def verify(self, username, password):
        payload = self._users_payload()
        for item in payload.get("users", []):
            if item.get("username") != username:
                continue

            salt = item.get("salt", "")
            expected = item.get("password_hash", "")
            actual = self._hash_password(password, salt)
            return hmac.compare_digest(actual, expected)

        return False
