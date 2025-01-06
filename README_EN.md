## ImageExporter

English | [简体中文](README.md)

**ImageExporter** is an efficient tool designed specifically for offline installation and deployment scenarios. It can automatically check, download, and export the latest versions of Docker images, providing a convenient one-click solution for managing images of middleware and service environments.  
With this tool, you can quickly obtain the latest versions of middleware images and package them into offline-compatible image files for efficient deployment in network-isolated environments.

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
2. Run the program: `python main.py`.
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

### Features

- Multi-architecture support (AMD64/ARM64)
- Automatic version comparison
- Concurrent downloads
- Resume interrupted operations
- Detailed logging
- Flexible configuration
- Smart cleanup tool

### License

[MIT License](LICENSE)
