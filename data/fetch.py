"""Fetch the input bytes recorded in sources.json, or verify existing files.

Uses only the standard library. Run from any directory. Source URLs can change;
the recorded digest must still match before a downloaded file is installed.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", choices=("sharma", "hersh", "all"), default="all", nargs="?")
    parser.add_argument("--verify", action="store_true", help="Check local files without downloading")
    args = parser.parse_args()
    sources = json.loads((ROOT / "data/sources.json").read_text(encoding="utf-8"))
    for source in sources["files"]:
        if args.dataset not in ("all", source["dataset"]):
            continue
        path = ROOT / source["path"]
        if args.verify or path.exists():
            data = path.read_bytes()
        else:
            with urlopen(source["url"], timeout=120) as response:
                data = response.read()
        if hashlib.sha256(data).hexdigest() != source["sha256"]:
            raise SystemExit(f"Checksum mismatch: {source['path']}; file was not replaced")
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        print(f"verified {source['path']}")


if __name__ == "__main__":
    main()
