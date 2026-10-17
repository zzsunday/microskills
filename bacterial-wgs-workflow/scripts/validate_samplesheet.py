#!/usr/bin/env python3
import argparse
import csv
import re
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("samples_tsv")
    args = ap.parse_args()

    required = ["sample_id", "r1", "r2", "long_reads", "long_platform"]
    errors = []
    seen = set()
    used_paths = {}
    raw = Path(args.samples_tsv).read_bytes()
    if b"\r" in raw or not raw.endswith(b"\n"):
        raise SystemExit("Use Unix LF line endings and a final newline.")

    with open(args.samples_tsv, newline="", encoding="utf-8") as fh:
        records = list(csv.reader(fh, delimiter="\t", quoting=csv.QUOTE_NONE))
        if not records or records[0] != required:
            raise SystemExit("Header must be exactly: " + "\t".join(required))
        rows = records[1:]
    if not rows:
        errors.append("Manifest contains no samples")

    for i, values in enumerate(rows, start=2):
        if len(values) != 5:
            errors.append(f"line {i}: expected exactly five tab-separated fields; no blank lines")
            continue
        row = dict(zip(required, values))
        if any(v != v.strip() or any(ord(c) < 32 for c in v) for v in values):
            errors.append(f"line {i}: whitespace/control characters in fields")
        sid = row["sample_id"]
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", sid):
            errors.append(f"line {i}: unsafe sample_id: {sid!r}")
        if sid in seen:
            errors.append(f"line {i}: duplicate sample_id: {sid}")
        seen.add(sid)

        for key in ("r1", "r2", "long_reads"):
            p = row[key]
            if not p:
                if key != "long_reads":
                    errors.append(f"line {i} {sid}: missing {key}")
                continue
            path = Path(p)
            if not path.is_file() or path.stat().st_size == 0:
                errors.append(f"line {i} {sid}: {key} missing/empty: {p}")
            resolved = path.resolve()
            if resolved in used_paths:
                errors.append(f"line {i} {sid}: {key} reuses input from {used_paths[resolved]}")
            used_paths[resolved] = f"{sid}/{key}"

        lp = row["long_reads"].strip()
        platform = row["long_platform"]
        if lp:
            if not Path(lp).is_file():
                errors.append(f"line {i} {sid}: long_reads does not exist: {lp}")
            if platform not in {"ONT", "PACBIO"}:
                errors.append(f"line {i} {sid}: unsupported long_platform={platform}")
        elif platform:
            errors.append(f"line {i} {sid}: long_platform set but long_reads empty")

    if errors:
        print("\n".join(errors))
        raise SystemExit(1)

    print(f"OK: {len(rows)} samples validated (paths/layout only; FASTQ integrity not checked).")

if __name__ == "__main__":
    main()
