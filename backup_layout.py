#!/usr/bin/env python3
"""Legacy wrapper: use `python3 src/cleanup_iphone.py backup`."""

from src.cleanup_iphone import main


if __name__ == "__main__":
    main(["backup"])
