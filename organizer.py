import os
import shutil
import json
import time
import logging
import threading
import argparse
import hashlib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

DEBOUNCE_SECONDS = 5

def calculate_sha256(file_path, chunk_size=8192):
    """
    INDUSTRY STANDARD UPGRADE: Cryptographic Hashing
    Instead of assuming files are duplicates just because they have the same name,
    we calculate a SHA-256 hash of the file's contents. This is how Dropbox, 
    Google Drive, and Git detect actual duplicate files.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logging.error(f"Failed to hash {file_path}: {e}")
        return None

class FileOrganizerHandler(FileSystemEventHandler):
    def __init__(self, source_dir, dest_dir, config_path):
        self.source_dir = source_dir
        self.dest_dir = dest_dir
        self.config = self.load_config(config_path)
        self._pending_timers = {}

    def load_config(self, config_path):
        """Loads category rules from an external JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Failed to load config: {e}. Falling back to default 'Others'.")
            return {}

    def get_category(self, extension):
        for category, extensions in self.config.items():
            if extension.lower() in extensions:
                return category
        return "Others"

    def _cancel_pending_timer(self, file_path):
        if file_path in self._pending_timers:
            self._pending_timers[file_path].cancel()
            del self._pending_timers[file_path]

    def schedule_file(self, file_path):
        if os.path.isdir(file_path):
            return

        filename = os.path.basename(file_path)
        if filename in ["config.json", "organizer.py", "requirements.txt", "Dockerfile"] or filename.startswith('.'):
            return

        self._cancel_pending_timer(file_path)
        logging.info(f"Detected '{filename}' — Waiting {DEBOUNCE_SECONDS}s for potential renames...")

        timer = threading.Timer(DEBOUNCE_SECONDS, self.process_file, args=[file_path])
        self._pending_timers[file_path] = timer
        timer.start()

    def process_file(self, file_path):
        self._pending_timers.pop(file_path, None)

        if not os.path.exists(file_path) or os.path.isdir(file_path):
            return

        filename = os.path.basename(file_path)
        _, extension = os.path.splitext(filename)
        category = self.get_category(extension) if extension else "Others"
        
        target_folder = os.path.join(self.dest_dir, category)
        os.makedirs(target_folder, exist_ok=True)
        
        target_path = os.path.join(target_folder, filename)

        if os.path.exists(target_path):
            source_hash = calculate_sha256(file_path)
            target_hash = calculate_sha256(target_path)
            
            if source_hash and source_hash == target_hash:
                logging.info(f"Exact duplicate detected for '{filename}'. Deleting source to save space.")
                os.remove(file_path)
                return
            else:
                base_name, ext = os.path.splitext(filename)
                target_path = os.path.join(target_folder, f"{base_name}_{int(time.time())}{ext}")

        try:
            shutil.move(file_path, target_path)
            logging.info(f"Moved: '{filename}' -> '{category}/'")
        except PermissionError:
            logging.warning(f"File locked (still downloading or open): '{filename}'")
        except Exception as e:
            logging.error(f"Error processing '{filename}': {e}")

    def on_created(self, event):
        self.schedule_file(event.src_path)

    def on_moved(self, event):
        self._cancel_pending_timer(event.src_path)
        self.schedule_file(event.dest_path)

def organize_existing_files(source_dir, handler):
    """Processes any files that were dumped in the folder while the script was off."""
    logging.info("Scanning for pre-existing files...")
    for filename in os.listdir(source_dir):
        handler.process_file(os.path.join(source_dir, filename))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated File Organizer daemon.")
    parser.add_argument("--source", type=str, default="test_folder", help="Directory to monitor")
    parser.add_argument("--dest", type=str, default="test_folder", help="Directory to move files into")
    parser.add_argument("--config", type=str, default="config.json", help="Path to config.json")
    args = parser.parse_args()

    source_directory = os.path.abspath(args.source)
    dest_directory = os.path.abspath(args.dest)
    config_file_path = os.path.abspath(args.config)
    
    os.makedirs(source_directory, exist_ok=True)
    os.makedirs(dest_directory, exist_ok=True)
    
    event_handler = FileOrganizerHandler(source_directory, dest_directory, config_file_path)
    organize_existing_files(source_directory, event_handler)
    
    logging.info(f"Monitoring Directory : {source_directory}")
    logging.info(f"Destination Directory: {dest_directory}")
    logging.info("Press Ctrl+C to stop.")
    
    observer = Observer()
    observer.schedule(event_handler, source_directory, recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        for timer in event_handler._pending_timers.values():
            timer.cancel()
        logging.info("Gracefully shutting down file organizer.")
    
    observer.join()
