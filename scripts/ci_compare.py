#!/usr/bin/env python3
"""Compare UF2 bytes from two successful independent clean build jobs."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

FILENAMES = ("toucan-v1-selenium-left.uf2", "toucan-v1-selenium-right.uf2", "toucan-v1-settings-reset.uf2")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pass1", type=Path, required=True)
    parser.add_argument("--pass2", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    result = {"schema_version": 1, "status": "fail", "physical_tests_performed": False,
              "scope": "UF2 byte comparison for one source commit in two clean CI jobs", "files": []}
    try:
        a = json.loads((args.pass1 / "provenance/build-summary.json").read_text(encoding="utf-8"))
        b = json.loads((args.pass2 / "provenance/build-summary.json").read_text(encoding="utf-8"))
        if a["status"] != "pass" or b["status"] != "pass" or {a["clean_pass"], b["clean_pass"]} != {1, 2}:
            raise ValueError("Two successful distinct clean passes are required")
        for name in ("source_commit", "source_date_epoch", "container_image"):
            if a.get(name) != b.get(name) or a.get(name) is None:
                raise ValueError("Build input mismatch: " + name)
            result[name] = a[name]
        for directory in (args.pass1, args.pass2):
            if {p.name for p in (directory / "firmware").iterdir() if p.is_file()} != set(FILENAMES):
                raise ValueError("Each pass must contain exactly the three expected firmware files")
        for filename in FILENAMES:
            first = (args.pass1 / "firmware" / filename).read_bytes()
            second = (args.pass2 / "firmware" / filename).read_bytes()
            result["files"].append({"filename": filename, "sha256_pass1": hashlib.sha256(first).hexdigest(),
                                    "sha256_pass2": hashlib.sha256(second).hexdigest(), "bytes_identical": first == second,
                                    "bytes": len(first)})
        if not all(item["bytes_identical"] for item in result["files"]):
            raise ValueError("Clean builds produced different UF2 bytes")
        destination = args.output / "firmware"
        destination.mkdir(exist_ok=True)
        for filename in FILENAMES:
            shutil.copy2(args.pass1 / "firmware" / filename, destination / filename)
        (destination / "SHA256SUMS.txt").write_text(
            "".join(item["sha256_pass1"] + "  " + item["filename"] + "\n" for item in result["files"]), encoding="utf-8")
        result["status"] = "pass"
    except (OSError, ValueError, KeyError, TypeError) as error:
        result["error"] = str(error)
    (args.output / "reproducibility.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
