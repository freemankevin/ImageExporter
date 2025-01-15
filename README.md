# ImageExporter

A specialized tool for offline Docker image management and deployment.

## Supported Middleware

- Elasticsearch 
- Nginx
- Redis
- RabbitMQ
- MinIO
- Nacos
- GeoServer


## Structure
```
ImageExporter/
├── data/
│   ├── versions/     # Version info
│   └── images/       # Exported images
├── logs/             # Log files
├── src/              # Source code
└── tests/            # Test suite
```

## Usage

1. Place version files in `data/versions` (optional)
2. Run:
```bash
git clone https://github.com/FreemanKevin/ImageExporter
pip install -r requirements.txt
python main.py      # Normal mode
python main.py -D   # Debug mode
```

## Cleanup

```bash
python clean.py -a    # Clean all
python clean.py -c    # Clean cache
python clean.py -v    # Clean today's versions
```
