#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path

def parse_fastp(path):
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text())
        before = data.get("summary", {}).get("before_filtering", {})
        after = data.get("summary", {}).get("after_filtering", {})
        return {
            "fastp_status": "COMPLETE",
            "reads_before": before.get("total_reads", ""),
            "reads_after": after.get("total_reads", ""),
        }
    except Exception:
        return {"fastp_status": "PARSE_ERROR", "reads_before": "", "reads_after": ""}

def parse_quast(path):
    out = {}
    if not path.is_file():
        return out
    rows = {}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2:
                rows[parts[0]] = parts[1]
    mapping = {
        "# contigs": "contigs",
        "Total length": "genome_size",
        "Largest contig": "largest_contig",
        "N50": "n50",
        "L50": "l50",
        "GC (%)": "gc_percent",
    }
    for k, outk in mapping.items():
        out[outk] = rows.get(k, "")
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("samples_tsv")
    ap.add_argument("-o", "--output", default="summary/workflow_summary.tsv")
    args = ap.parse_args()

    fields = [
        "sample_id","input_type","r1","r2","long_reads","long_platform",
        "fastp_status","reads_before","reads_after","assembly_mode","assembler",
        "assembler_version","assembly_status","contigs","genome_size",
        "largest_contig","n50","l50","gc_percent","circular_contigs",
        "bakta_status","bakta_version","warning"
    ]

    rows_out = []
    with open(args.samples_tsv, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for r in reader:
            sid = r["sample_id"]
            long_reads = r.get("long_reads","").strip()
            out = {k:"" for k in fields}
            out.update({
                "sample_id": sid,
                "input_type": "HYBRID" if long_reads else "SHORT",
                "r1": r.get("r1",""),
                "r2": r.get("r2",""),
                "long_reads": long_reads,
                "long_platform": r.get("long_platform",""),
                "assembly_mode": "HYBRID" if long_reads else "SHORT",
                "assembler": "Unicycler" if long_reads else "SPAdes",
            })

            out.update(parse_fastp(Path(f"qc/fastp/{sid}_QC.json")))

            asm = Path(f"assembly/{sid}/{sid}.fasta")
            out["assembly_status"] = "COMPLETE" if asm.is_file() and asm.stat().st_size > 0 else "MISSING"

            out.update(parse_quast(Path(f"qc/quast/{sid}/report.tsv")))

            ann = Path(f"annotation/{sid}")
            anno_files = [ann / f"{sid}.{ext}" for ext in ("gff3", "gbff", "faa", "ffn", "fna", "tsv")]
            out["bakta_status"] = "COMPLETE" if all(p.is_file() and p.stat().st_size > 0 for p in anno_files) else "MISSING"

            warnings = []
            if out.get("fastp_status") != "COMPLETE":
                warnings.append("fastp_not_complete")
            if out["assembly_status"] != "COMPLETE":
                warnings.append("assembly_missing")
            if not out.get("n50") or not out.get("genome_size"):
                warnings.append("quast_missing_or_incomplete")
            if out["bakta_status"] != "COMPLETE":
                warnings.append("bakta_not_complete")
            out["warning"] = ";".join(warnings)
            rows_out.append(out)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows_out)

    print(f"Wrote {len(rows_out)} rows to {out_path}")

if __name__ == "__main__":
    main()
