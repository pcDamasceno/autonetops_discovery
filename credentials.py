
class Credentials:
    """
    Class to manage credentials for AutoNetOps.
    """
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    def get_credentials(self) -> dict:
        """
        Returns the credentials as a dictionary.
        """
        return {
            'username': self.username,
            'password': self.password
        }