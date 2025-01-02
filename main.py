from services.image_fetch import ImageFetcher
from api.docker_hub import DockerHubAPI
from utils.config import Config

def main():
    config = Config()
    fetcher = ImageFetcher()
    api = DockerHubAPI()

    repositories = ["library/elasticsearch", "library/redis"]
    for repo in repositories:
        latest_version = api.get_latest_version(repo)
        if latest_version:
            fetcher.fetch_image(repo, latest_version)
            fetcher.export_image(repo, latest_version, config.get("output_dir"))

if __name__ == "__main__":
    main()