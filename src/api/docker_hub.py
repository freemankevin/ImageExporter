import requests
from utils.logger import Logger

class DockerHubAPI:
    def __init__(self):
        self.base_url = "https://hub.docker.com/v2"
        self.logger = Logger().get_logger()

    def get_latest_version(self, repository):
        url = f"{self.base_url}/repositories/{repository}/tags"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data['results'][0]['name']
        else:
            self.logger.error(f"Failed to fetch latest version for {repository}")
            return None