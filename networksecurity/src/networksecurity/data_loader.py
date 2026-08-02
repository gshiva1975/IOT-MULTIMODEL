"""
data_loader.py -- discover classes/files from a data directory.

Expected layout: one subfolder per class, each containing one or more CSV
part files, e.g.:

    data/CSV/BenignTraffic/BenignTraffic.pcap.csv
    data/CSV/DDoS-TCP_Flood/DDoS-TCP_Flood.pcap.csv
    data/CSV/DDoS-SynonymousIP_Flood/DDoS-SynonymousIP_Flood.pcap.csv
    data/CSV/DDoS-SynonymousIP_Flood/DDoS-SynonymousIP_Flood1.pcap.csv
    ...

Every subfolder becomes a class; every *.csv inside it is treated as one
part of that class's traffic (files are loaded one at a time downstream,
not all concatenated in memory, so this scales to many large files).
"""

import glob
import os
import sys

from .config import BENIGN_CLASS_NAME


def discover_classes(data_dir, only_classes=None):
    """Returns {class_name: [sorted list of csv paths]}."""
    if not os.path.isdir(data_dir):
        sys.exit(f"Data directory not found: {data_dir}")

    classes = {}
    for entry in sorted(os.listdir(data_dir)):
        class_dir = os.path.join(data_dir, entry)
        if not os.path.isdir(class_dir):
            continue
        if only_classes and entry not in only_classes:
            continue
        csv_files = sorted(glob.glob(os.path.join(class_dir, "*.csv")))
        if csv_files:
            classes[entry] = csv_files

    if not classes:
        sys.exit(f"No class subfolders with .csv files found under {data_dir}")
    return classes


def find_benign_class(class_files):
    for name in class_files:
        if BENIGN_CLASS_NAME.lower() in name.lower():
            return name
    return None
