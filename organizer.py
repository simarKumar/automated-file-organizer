import os
import shutil
import json
import time
import logging
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

DEBOUNCE_SECONDS = 5

class FileOrganizerHandler(FileSystemEventHandler):
    def __init__(self, source_dir, config_path):
        self.source_dir = source_dir
        self.config = self.load_config(config_path)
        self._pending_timers = {}

    def load_config(self, config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"Config file not found: {config_path}")
            return {}
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON in config file: {config_path}")
            return {}

    def get_category(self, extension):
        for category, extensions in self.config.items():
            if extension.lower() in extensions:
                return category
        return "Others"

    def _cancel_pending_timer(self, file_path):
        """Cancel a pending timer for a file if one exists."""
        if file_path in self._pending_timers:
            self._pending_timers[file_path].cancel()
            del self._pending_timers[file_path]

    def schedule_file(self, file_path):
        """
        Schedule a file to be processed after DEBOUNCE_SECONDS.
        If the file is renamed during that time, the old timer is cancelled
        and a new timer is started for the new filename automatically via on_moved.
        """
        if os.path.isdir(file_path):
            return

        filename = os.path.basename(file_path)

        if filename in ["config.json", "organizer.py", "requirements.txt"]:
            return

        self._cancel_pending_timer(file_path)

        logging.info(f"Detected: '{filename}' — waiting {DEBOUNCE_SECONDS}s before sorting...")

        timer = threading.Timer(DEBOUNCE_SECONDS, self.process_file, args=[file_path])
        self._pending_timers[file_path] = timer
        timer.start()

    def process_file(self, file_path):
        """Actually move the file to its category folder."""
        self._pending_timers.pop(file_path, None)

        if not os.path.exists(file_path):
            return

        if os.path.isdir(file_path):
            return

        filename = os.path.basename(file_path)
        _, extension = os.path.splitext(filename)

        category = self.get_category(extension) if extension else "Others"

        dest_dir = os.path.join(self.source_dir, category)

        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        dest_path = os.path.join(dest_dir, filename)

        if os.path.exists(dest_path):
            base_name, ext = os.path.splitext(filename)
            timestamp = int(time.time())
            dest_path = os.path.join(dest_dir, f"{base_name}_{timestamp}{ext}")

        try:
            shutil.move(file_path, dest_path)
            logging.info(f"Moved: '{filename}' -> '{category}/'")
        except PermissionError:
            logging.warning(f"Permission denied (file might be open): {filename}")
        except Exception as e:
            logging.error(f"Error moving '{filename}': {e}")

    def on_created(self, event):
        self.schedule_file(event.src_path)

    def on_moved(self, event):
        self._cancel_pending_timer(event.src_path)
        self.schedule_file(event.dest_path)


def organize_existing_files(source_dir, handler):
    logging.info("Scanning for existing files on startup...")
    for filename in os.listdir(source_dir):
        file_path = os.path.join(source_dir, filename)
        handler.process_file(file_path)


if __name__ == "__main__":
    source_directory = os.path.abspath("test_folder")

    if not os.path.exists(source_directory):
        os.makedirs(source_directory)

    config_file_path = os.path.abspath("config.json")

    event_handler = FileOrganizerHandler(source_directory, config_file_path)

    organize_existing_files(source_directory, event_handler)

    print(f"\nMonitoring directory: {source_directory}")
    print(f"New files will be sorted after a {DEBOUNCE_SECONDS}-second grace period.")
    print("Press Ctrl+C to stop.\n")

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
        print("\nStopping the file organizer.")

    observer.join()
