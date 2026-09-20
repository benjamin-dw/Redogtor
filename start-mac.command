#!/bin/bash
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is not installed."
  echo "Download it from https://www.python.org/downloads/ then run this again."
  read -n 1 -s -r -p "Press any key to close."
  exit 1
fi
python3 run.py
read -n 1 -s -r -p "Press any key to close."
