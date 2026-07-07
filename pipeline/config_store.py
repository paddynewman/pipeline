import json
import os


class JsonStore:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _path(self, name):
        return os.path.join(self.base_dir, f"{name}.json")

    def load(self, name, default):
        path = self._path(name)
        if not os.path.exists(path):
            self.save(name, default)
            return default

        with open(path, "r", encoding="utf-8") as handle:
            try:
                return json.load(handle)
            except json.JSONDecodeError:
                # Recover safely from a corrupted local JSON file.
                self.save(name, default)
                return default

    def save(self, name, value):
        path = self._path(name)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
