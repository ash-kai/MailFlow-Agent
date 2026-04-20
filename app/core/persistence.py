import os
import logging

logger = logging.getLogger(__name__)

class TokenStore:
    # TODO - Move away from file storage to something more secure and robust in production (e.g. encrypted vault, database, or OS keychain)
    """Handles the reading and writing of authentication tokens."""
    def __init__(self, filepath: str):
        self.filepath = os.path.abspath(filepath)

    def exists(self) -> bool:
        return os.path.exists(self.filepath)

    def read(self) -> str:
        logger.debug(f"Reading token from {self.filepath}")
        if not self.exists():
            return ""
        with open(self.filepath, 'r') as f:
            return f.read()

    def write(self, data: str):
        logger.debug(f"Writing token to {self.filepath}")
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, 'w') as f:
            f.write(data)