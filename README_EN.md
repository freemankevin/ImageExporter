## ImageExporter

English | [简体中文](README.md)

A tool designed for offline deployment that automatically downloads and exports Docker images.

### Supported Middleware

- Elasticsearch
- Nginx
- Redis
- RabbitMQ
- MinIO
- Nacos
- GeoServer

### Key Features

- Automatic version detection and comparison
- Multi-architecture support (AMD64/ARM64)
- Automatic offline image package export
- Resume downloads and concurrent processing
- Version history and update list generation
- Debug mode with detailed logging
- Smart cleanup tool

### Directory Structure

```
ImageExporter/
├── data/
│   ├── versions/     # Version information files
│   └── images/       # Exported image files
├── logs/             # Log files
├── src/              # Source code
└── tests/            # Test code
```

### Usage

1. Place the historical version files in the `data/versions` directory (optional).
2. Run the program:
   ```bash
   python main.py      # Normal mode
   python main.py -D   # Debug mode (show detailed logs)
   ```
3. The exported image files will be saved in the `data/images/DATE/ARCHITECTURE/` directory.

### Development Instructions

1. Clone the repository: `git clone <repository_url>`.
2. Install dependencies: `pip install -r requirements.txt`.
3. Run tests: `python -m pytest tests/`.

### Cleaning Tool

Use `clean.py` to clean up:
```bash
python clean.py -a    # Clean everything
python clean.py -c    # Clean only cache
python clean.py -v    # Clean version files from today
```

### Dependency Requirements

- Python 3.8+
- Docker
- For detailed dependencies, see `requirements.txt`.

### License

[MIT License](LICENSE)
