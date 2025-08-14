# Petlog - Pet Camera Monitoring System

A scalable, AI-powered pet monitoring system built for Raspberry Pi that detects and classifies pet activities using real-time video analysis and face recognition.

## Overview

Petlog is designed to monitor pets using a Raspberry Pi 4 and camera module, providing:
- **Real-time pet detection** with face recognition for identification
- **Event classification** (playing, sleeping, eating, etc.)
- **Automatic video recording** for dynamic activities
- **Remote access** via web dashboard
- **Smart alerts** for inactivity periods
- **Local storage management** with automatic cleanup

## Quick Start

### Prerequisites
- Raspberry Pi 4 with Camera Module V2
- Python 3.8+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/albertocutone/petlog.git
   cd petlog
   ```

2. **Set up Python environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python main.py
   ```

### Development Setup

For development work, please read the [development guidelines](context.md) first.

1. **Create a feature branch**
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Follow conventional commit format**
   ```bash
   git commit -m "feat(scope): description of changes"
   ```

3. **Run tests before committing**
   ```bash
   pytest tests/
   ```

## Project Structure

```
petlog/
├── docs/                    # Documentation
│   ├── design/             # System design and specifications
│   └── technical-decisions.md
├── src/                     # Source code (coming soon)
├── tests/                   # Test files (coming soon)
├── scripts/                 # Deployment scripts
├── context.md              # Development guidelines
└── main.py                 # Application entry point
```

## Key Features

- **AI-Powered Detection**: Uses OpenCV and face recognition for pet identification
- **Event Logging**: SQLite database for storing event metadata
- **Web API**: FastAPI backend with live video streaming
- **Remote Access**: Secure HTTPS access with authentication
- **Storage Management**: Automatic cleanup when storage exceeds 80%
- **Modular Architecture**: Scalable design supporting multiple cameras/pets

## Documentation

- **[Development Guidelines](context.md)** - Rules and practices for contributors
- **[Technical Decisions](docs/technical-decisions.md)** - Architecture and technology choices
- **[System Design](docs/design/petlog.md)** - Detailed system specification

## Contributing

1. Read the [development context](context.md) for coding standards
2. Create a feature branch following the naming convention
3. Use conventional commit messages for GitHub Actions compatibility
4. Ensure all tests pass before submitting PR
5. Include UML diagrams in `architectures/` folder for complex features

## Hardware Requirements

- **Raspberry Pi 4** (recommended) or compatible single-board computer
- **Camera Module V2** or USB camera
- **MicroSD card** (32GB+ recommended)
- **Stable internet connection** for remote access

## License

This project is licensed under the terms specified in the [LICENSE](LICENSE) file.

## Status

🚧 **In Development** - This project is currently in active development. Core features are being implemented following the system design specifications.
