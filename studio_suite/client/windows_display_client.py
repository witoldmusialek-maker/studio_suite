#!/usr/bin/env python3
"""
Windows display/content client entrypoint.

Uses the existing DigitalSignageClient pipeline from main.py:
- register as display
- heartbeat
- download and play scheduled content (image/pdf/excel/video)
"""

from main import DigitalSignageClient


if __name__ == "__main__":
    DigitalSignageClient().run()
