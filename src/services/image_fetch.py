import subprocess
from utils.config import Config
from utils.logger import Logger

class ImageFetcher:
    def __init__(self):
        self.config = Config()
        self.logger = Logger().get_logger()

    def fetch_image(self, repository, tag):
        command = f"docker pull {repository}:{tag}"
        result = subprocess.run(command, shell=True, capture_output=True)
        if result.returncode == 0:
            self.logger.info(f"Successfully fetched {repository}:{tag}")
        else:
            self.logger.error(f"Failed to fetch {repository}:{tag}")

    def export_image(self, repository, tag, output_dir):
        command = f"docker save -o {output_dir}/{repository.replace('/', '_')}_{tag}.tar {repository}:{tag}"
        result = subprocess.run(command, shell=True, capture_output=True)
        if result.returncode == 0:
            self.logger.info(f"Successfully exported {repository}:{tag} to {output_dir}")
        else:
            self.logger.error(f"Failed to export {repository}:{tag}")