# Development Guide

English | [简体中文](DEVELOPMENT.md)

## Directory Structure

- `data/`: Data directory
  - `versions/`: Version information files
  - `images/`: Exported image files
- `logs/`: Log files directory
- `src/`: Source code directory
  - `config/`: Configuration related code
  - `services/`: Core service code
  - `utils/`: Utility functions
- `tests/`: Test code directory

## Development Environment Setup

1. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

## Directory Details

- `data/versions/`: Stores version history files, format: `latest-YYYYMMDD.txt`
- `data/images/`: Stores exported image files, organized by date and architecture
- `logs/`: Stores runtime logs, format: `image_exporter_YYYYMMDD.log`

## Development Tools

### Cleanup Tool (clean.py)

The project root provides a cleanup tool for managing temporary files and caches:

```bash
# Show help information
python clean.py

# Clean everything (preserves historical version files)
python clean.py -a

# Clean specific items
python clean.py -c    # Clean Python cache
python clean.py -s    # Clean state file
python clean.py -o    # Clean output directory
python clean.py -v    # Clean today's version files
python clean.py -l    # Clean log files

# Combine multiple cleanup options
python clean.py -c -s -l  # Clean cache, state and logs
```

Notes:
- Version file cleanup only removes today's files, preserving historical files for comparison
- Log cleanup automatically handles file locks
- Recommended to run cleanup before starting new operations

## Testing

Run all tests:
```bash
pytest
```

Run specific test:
```bash
pytest tests/test_version_utils.py
```

## Code Style

Project follows PEP 8 style guide. Use flake8 for code checking:
```bash
flake8 .
```

## Commit Guidelines

Commit message format:
```
<type>: <description>

[optional body]
```

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- style: Code style changes
- refactor: Code refactoring
- test: Testing related
- chore: Build process or auxiliary tool changes

## Project Structure

```
ImageExporter/
├── src/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── docker_hub.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── image_fetch.py
│   │   ├── image_pull.py
│   │   └── image_update.py
│   └── utils/
│       ├── __init__.py
│       ├── docker_utils.py
│       ├── file_utils.py
│       ├── logger.py
│       ├── paths.py
│       └── version_utils.py
├── config/
│   ├── __init__.py
│   └── config.py
├── tests/
│   └── ...
├── data/
│   ├── versions/     # Version files directory
│   └── images/       # Image files directory
├── logs/             # Log directory
├── clean.py          # Cleanup tool
├── main.py
├── requirements.txt
└── requirements-dev.txt
```

## Development Workflow

1. Create new branch
2. Run cleanup before development: `python clean.py -a`
3. Develop and test
4. Run code style check
5. Commit code (following commit guidelines)
6. Create pull request

## Debugging Tips

1. Use clean.py tool to clean environment
2. Check log files for detailed information
3. Use pytest -v flag for verbose test output
4. Use Python debugger (pdb) for breakpoint debugging 
