#!/usr/bin/env python3
"""
VisJPEG - Direktstart ohne Installation.
Empfohlen: pip install -e . && visjpeg
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from visjpeg.__main__ import main

if __name__ == "__main__":
    main()
