import os
import logging
import keyring

logger = logging.getLogger(__name__)

class TokenStore:
    """Handles the secure reading and writing of authentication tokens using system keyring."""
    def __init__(self, service_name: str, account_name: str, fallback_path: str):
        self.service_name = service_name
        self.account_name = account_name
        self.filepath = os.path.abspath(fallback_path)

    def exists(self) -> bool:
        if keyring.get_password(self.service_name, self.account_name):
            return True
        return os.path.exists(self.filepath)

    def read(self) -> str:
        # Try keyring first (Industry Standard)
        token = keyring.get_password(self.service_name, self.account_name)
        if token:
            logger.debug(f"Retrieved token from keyring for {self.service_name}")
            return token
            
        logger.debug(f"Keyring empty, checking fallback file: {self.filepath}")
        if not self.exists():
            return ""
        with open(self.filepath, 'r') as f:
            return f.read()

    def write(self, data: str):
        try:
            keyring.set_password(self.service_name, self.account_name, data)
            logger.debug(f"Successfully stored token in keyring for {self.service_name}")
        except Exception as e:
            logger.warning(f"Could not write to keyring: {e}. Falling back to file.")
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            with open(self.filepath, 'w') as f:
                f.write(data)