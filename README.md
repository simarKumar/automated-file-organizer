# Automated File Organizer daemon

An enterprise-ready, event-driven Python daemon that monitors a designated directory in real-time and categorizes incoming files based on their extensions and content.

## Key Technical Features
- **Event-Driven Architecture**: Utilizes `watchdog` to respond to file system events in real-time, eliminating the overhead of constant directory polling.
- **Content-Addressable Deduplication**: Implements **SHA-256 cryptographic hashing** (`hashlib`) to identify true duplicate files by content rather than just filename collisions, preventing data loss and saving storage space.
- **Debouncing Mechanism**: Uses `threading.Timer` to implement a 5-second grace period on newly detected files, allowing users time to rename or modify files before they are processed.
- **Dynamic Configuration**: File routing rules are decoupled from the core logic using an external `config.json` map.
- **Containerized**: Includes a `Dockerfile` for seamless deployment across environments.
- **CI/CD Pipeline**: GitHub Actions integration for automated `flake8` linting and Docker build verification on every push.

## Usage (Local Daemon)

```bash
# Clone the repository
git clone https://github.com/simarKumar/automated-file-organizer.git
cd automated-file-organizer

# Create a virtual environment and install dependencies
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt

# Run the daemon with custom arguments
python organizer.py --source /path/to/downloads --dest /path/to/sorted_files
```

## Usage (Docker)

```bash
docker build -t file-organizer .
docker run -v /your/local/folder:/app/test_folder file-organizer
```
