#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

PAIR_PATTERNS = [
    (re.compile(r"^(?P<sample>.+)_R1(?:_001)?\.(?:f(?:ast)?q)(?:\.gz)?$", re.I), "r1"),
    (re.compile(r"^(?P<sample>.+)_R2(?:_001)?\.(?:f(?:ast)?q)(?:\.gz)?$", re.I), "r2"),
    (re.compile(r"^(?P<sample>.+)_1\.(?:f(?:ast)?q)(?:\.gz)?$", re.I), "r1"),
    (re.compile(r"^(?P<sample>.+)_2\.(?:f(?:ast)?q)(?:\.gz)?$", re.I), "r2"),
]
LONG_HINTS = (
    "ont", "nanopore", "filtlong", "pacbio", "hifi", "longread", "long_read"
)

def classify_long(name: str):
    n = name.lower()
    if "hifi" in n or "pacbio" in n:
        return "PACBIO"
    if "ont" in n or "nanopore" in n or "filtlong" in n:
        return "ONT"
    return ""

def main():
    ap = argparse.ArgumentParser(description="Build a starter bacterial WGS samples.tsv")
    ap.add_argument("input_dir")
    ap.add_argument("-o", "--output", default="samples.tsv")
    args = ap.parse_args()

    indir = Path(args.input_dir).resolve()
    if not indir.is_dir():
        ap.error(f"input directory does not exist: {indir}")
    rec = {}

    def assign(sample, field, path):
        entry = rec.setdefault(sample, {"r1":"", "r2":"", "long_reads":"", "long_platform":""})
        if entry[field]:
            raise SystemExit(f"Ambiguous {field} for {sample}: {entry[field]} and {path}. Resolve lanes/duplicates manually.")
        entry[field] = str(path)

    files = [p for p in indir.rglob("*") if p.is_file()]
    for p in files:
        name = p.name
        matched = False
        for pat, mate in PAIR_PATTERNS:
            m = pat.match(name)
            if m:
                sample = m.group("sample")
                assign(sample, mate, p)
                matched = True
                break
        if matched:
            continue

        lname = name.lower()
        if any(h in lname for h in LONG_HINTS) and re.search(r"\.(f(?:ast)?q)(\.gz)?$", lname):
            stem = re.sub(r"\.(f(?:ast)?q)(\.gz)?$", "", name, flags=re.I)
            stem = re.sub(r"(?i)[._-](ont|nanopore|filtlong|pacbio|hifi|longreads?|long_reads?).*$", "", stem)
            sample = stem
            assign(sample, "long_reads", p)
            rec[sample]["long_platform"] = classify_long(name)

    if not rec:
        raise SystemExit("No recognized read files found; no manifest written.")
    with open(args.output, "x", encoding="utf-8") as out:
        out.write("sample_id\tr1\tr2\tlong_reads\tlong_platform\n")
        for sample in sorted(rec):
            r = rec[sample]
            out.write(f"{sample}\t{r['r1']}\t{r['r2']}\t{r['long_reads']}\t{r['long_platform']}\n")

    print(f"Wrote {len(rec)} records to {args.output}")
    print("Review the manifest manually before submission; filename inference is only a starting point.")

if __name__ == "__main__":
    main()
