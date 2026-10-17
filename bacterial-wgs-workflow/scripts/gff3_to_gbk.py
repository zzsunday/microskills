#!/usr/bin/env python3
"""Optional GFF3 + FASTA -> GenBank converter.

Use only when a downstream tool requires this conversion and Bakta native
GenBank-compatible output is insufficient.

Usage:
    gff3_to_gbk.py annotation.gff3 [assembly.fasta [molecule_type]]
"""
import os
import sys
from Bio import SeqIO
from BCBio import GFF

def _flatten_features(rec):
    out = []
    stack = list(rec.features)
    while stack:
        cur = stack.pop(0)
        out.append(cur)
        subs = getattr(cur, "sub_features", None) or []
        stack[0:0] = subs
    rec.features = out
    return rec

def _ensure_annotations(gff_iterator, molecule_type):
    for rec in gff_iterator:
        rec.annotations.setdefault("molecule_type", molecule_type)
        yield _flatten_features(rec)

def main(gff_file, fasta_file=None, molecule_type="DNA"):
    out_file = f"{os.path.splitext(gff_file)[0]}.gb"
    fasta_input = SeqIO.to_dict(SeqIO.parse(fasta_file, "fasta")) if fasta_file else {}
    gff_iter = GFF.parse(gff_file, fasta_input)
    SeqIO.write(_ensure_annotations(gff_iter, molecule_type), out_file, "genbank")
    print(out_file)

if __name__ == "__main__":
    main(*sys.argv[1:])
