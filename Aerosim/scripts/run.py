#!/usr/bin/env python3
import sys
from pathlib import Path

# Add src to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from aerosim.main import main

if __name__ == "__main__":
    main()
