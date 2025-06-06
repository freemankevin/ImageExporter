# ImageExporter 🐳

A specialized tool for offline Docker image management and deployment. 🚢

## Supported Software 📦

| Middleware         | Image Repository                          |
| ------------------ | ----------------------------------------- |
| Elasticsearch      | docker.io/library/elasticsearch           |
| Nginx              | docker.io/library/nginx                   |
| Redis              | docker.io/library/redis                   |
| RabbitMQ           | docker.io/library/rabbitmq                |
| MinIO              | docker.io/minio/minio                     |
| Nacos              | docker.io/nacos/nacos-server              |
| GeoServer          | docker.io/kartoza/geoserver               |
| PostgreSQL-PostGIS | docker.io/freelabspace/postgresql-postgis |


## Structure 🗂️

```
ImageExporter/
├── data/
│   ├── versions/     # Version info (e.g., latest-YYYYMMDD.txt, update-YYYYMMDD.txt) 📋
│   └── images/       # Exported images 🗃️
├── logs/             # Log files 📜
├── main.py           # Main script 🚀
```

## Usage 🛠️

1. Place historical version files in `data/versions` (optional, e.g., `latest-YYYYMMDD.txt`). 📥
2. Run the tool to check for updates and export images:

```bash
python main.py      # Normal mode 🌟
python main.py -D   # Debug mode 🐞
```

3. Check the generated version files (`latest-YYYYMMDD.txt` for all versions, `update-YYYYMMDD.txt` for updates needed) in `data/versions`. 🔍

## Cleanup 🧹

```bash
python main.py --clean      # Clean Python cache files 🗑️
python main.py --clean-all  # Clean all temporary files (cache, images, logs, today's versions) 🗑️🔥
```