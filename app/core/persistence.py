import os

class TokenStore:
    """Handles the reading and writing of authentication tokens."""
    def __init__(self, filepath: str):
        # Ensure we use an absolute path or a consistent config directory
        self.filepath = os.path.abspath(filepath)

    def exists(self) -> bool:
        return os.path.exists(self.filepath)

    def read(self) -> str:
        if not self.exists():
            return ""
        with open(self.filepath, 'r') as f:
            return f.read()

    def write(self, data: str):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, 'w') as f:
            f.write(data)