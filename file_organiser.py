"""
file_organiser.py  —  Automatically sort a messy folder by file type
Useful for organising your Downloads folder or project data folder.

Usage:
    python file_organiser.py --folder "C:/Users/YourName/Downloads" --dry-run
    python file_organiser.py --folder "C:/Users/YourName/Downloads"

Install:
    No extra libraries needed — uses Python standard library only.
"""

import argparse
import logging
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── File-type mapping ──────────────────────────────────────────────────────────
FOLDER_MAP: dict[str, str] = {
    # Data files (important for BCA — Superstore CSV goes here)
    ".csv":  "Data", ".xlsx": "Data", ".xls": "Data",
    ".json": "Data", ".xml":  "Data", ".sql": "Data",
    # Images
    ".jpg":  "Images", ".jpeg": "Images", ".png": "Images",
    ".gif":  "Images", ".webp": "Images", ".svg": "Images",
    # Documents
    ".pdf":  "Documents", ".docx": "Documents", ".doc": "Documents",
    ".txt":  "Documents", ".md":   "Documents", ".pptx": "Documents",
    # Videos
    ".mp4":  "Videos", ".mov": "Videos", ".avi": "Videos", ".mkv": "Videos",
    # Audio
    ".mp3":  "Audio",  ".wav": "Audio",  ".flac": "Audio",
    # Code
    ".py":   "Code",   ".js":  "Code",   ".ts":  "Code",
    ".html": "Code",   ".css": "Code",
    # Archives
    ".zip":  "Archives", ".tar": "Archives", ".gz": "Archives", ".rar": "Archives",
}
DEFAULT_FOLDER = "Misc"


# ── Core organiser ─────────────────────────────────────────────────────────────
def organise(folder: Path, dry_run: bool = False) -> dict[str, int]:
    stats: dict[str, int] = defaultdict(int)

    files = [f for f in folder.iterdir() if f.is_file()]
    log.info("Found %d files in: %s", len(files), folder)

    for file in files:
        dest_name = FOLDER_MAP.get(file.suffix.lower(), DEFAULT_FOLDER)
        dest_dir  = folder / dest_name
        dest_path = dest_dir / file.name

        # Avoid overwriting: append timestamp if name already exists
        if dest_path.exists():
            ts        = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_path = dest_dir / f"{file.stem}_{ts}{file.suffix}"

        if dry_run:
            log.info("[DRY RUN]  %-40s  →  %s/", file.name, dest_name)
        else:
            dest_dir.mkdir(exist_ok=True)
            shutil.move(str(file), dest_path)
            log.info("Moved  %-40s  →  %s/", file.name, dest_name)

        stats[dest_name] += 1

    return stats


# ── Report ─────────────────────────────────────────────────────────────────────
def print_report(stats: dict[str, int], dry_run: bool) -> None:
    label = "DRY-RUN PREVIEW" if dry_run else "ORGANISATION COMPLETE"
    print(f"\n{'=' * 50}")
    print(f"  {label}")
    print(f"{'=' * 50}")
    total = sum(stats.values())
    for folder_name, count in sorted(stats.items(), key=lambda x: -x[1]):
        bar = "▓" * count
        print(f"  {folder_name:<12}  {bar:<20}  {count} file{'s' if count != 1 else ''}")
    print(f"  {'─' * 46}")
    print(f"  Total : {total} files processed")
    print(f"{'=' * 50}\n")
    if dry_run:
        print("  Run without --dry-run to apply changes.\n")


# ── Main ───────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="Organise a folder by file type.")
    parser.add_argument(
        "--folder",  required=True,
        help='Folder to organise, e.g. "C:/Users/hp/Downloads"'
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview moves without actually moving any files"
    )
    args = parser.parse_args()

    folder = Path(args.folder).expanduser().resolve()

    if not folder.is_dir():
        log.error("Not a valid folder: %s", folder)
        raise SystemExit(1)

    stats = organise(folder, dry_run=args.dry_run)
    print_report(stats, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
