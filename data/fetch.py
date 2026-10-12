"""Fetch the input bytes recorded in sources.json, or verify existing files.

Uses only the standard library. Run from any directory. Source URLs can change;
the recorded digest must still match before a downloaded file is installed.
"""
import argparse
import hashlib
import json
import socket
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent


def prefer_ipv4():
    """Try IPv4 addresses before IPv6 ones.

    urllib tries each resolved address in turn and waits out the full timeout on
    every one that does not answer, so a host with IPv6 configured but not routed
    spends minutes per file before reaching an address that works.
    """
    resolve = socket.getaddrinfo

    def ipv4_first(*args, **kwargs):
        return sorted(resolve(*args, **kwargs), key=lambda info: info[0] != socket.AF_INET)

    socket.getaddrinfo = ipv4_first


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", choices=("sharma", "hersh", "all"), default="all", nargs="?")
    parser.add_argument("--verify", action="store_true", help="Check local files without downloading")
    args = parser.parse_args()
    prefer_ipv4()
    sources = json.loads((ROOT / "data/sources.json").read_text(encoding="utf-8"))
    for source in sources["files"]:
        if args.dataset not in ("all", source["dataset"]):
            continue
        path = ROOT / source["path"]
        if args.verify or path.exists():
            data = path.read_bytes()
        else:
            with urlopen(source["url"], timeout=30) as response:
                data = response.read()
        if hashlib.sha256(data).hexdigest() != source["sha256"]:
            raise SystemExit(f"Checksum mismatch: {source['path']}; file was not replaced")
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        print(f"verified {source['path']}")


if __name__ == "__main__":
    main()
