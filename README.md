# Automated File Organizer

A simple Python script I wrote to automate my daily file management. It watches a specific folder in real-time and automatically sorts incoming files into categorized subfolders (Images, Documents, Audio, etc.) based on their extensions.

## Features
- Real-time directory monitoring using `watchdog`.
- Configurable file categories using a `config.json` file.
- Handles duplicate files automatically by appending timestamps.
- Implements a 5-second debounce timer so you have time to rename files before they get moved.

## How to use
1. Clone the repo
2. Install the requirements: `pip install -r requirements.txt`
3. Run `python organizer.py`
4. Drop some files into the `test_folder` and watch them get sorted!

## Tech Stack
- Python 3
- watchdog (for file system events)
- built-in modules: os, shutil, json, threading
