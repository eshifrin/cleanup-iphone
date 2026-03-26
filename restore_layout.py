#!/usr/bin/env python3
"""Legacy wrapper: use `python3 src/cleanup_iphone.py restore <backup.plist>`."""

import sys
from src.cleanup_iphone import main


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 restore_layout.py <backup_file.plist>")
        sys.exit(1)
    main(["restore", sys.argv[1]])
