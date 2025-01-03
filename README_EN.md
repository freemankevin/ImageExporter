# Docker Image Auto-Update Tool

English | [简体中文](README.md)

A tool for automatically checking, downloading and exporting the latest versions of Docker images.

## Directory Structure

```
ImageExporter/
├── data/
│   ├── versions/     # Version information files
│   └── images/       # Exported image files
├── logs/            # Log files
├── src/             # Source code
└── tests/           # Test files
```

## Usage

1. Place historical version file in `data/versions` directory (optional)
2. Run the program: `python main.py`
3. Exported image files will be saved in `data/images/date/arch/` directory

## Development

1. Clone repository: `git clone <repository_url>`
2. Install dependencies: `pip install -r requirements.txt`
3. Run tests: `python -m pytest tests/`

## Cleanup Tool

Use `clean.py` for cleanup:
```bash
python clean.py -a    # Clean everything
python clean.py -c    # Clean cache only
python clean.py -v    # Clean today's version files
```

## Requirements

- Python 3.8+
- Docker
- See requirements.txt for detailed dependencies

## Features

- Multi-architecture support (AMD64/ARM64)
- Automatic version comparison
- Concurrent downloads
- Resume interrupted operations
- Detailed logging
- Flexible configuration
- Smart cleanup tool

## License

[Apache License 2.0](LICENSE) 