# Long-read reference

Supported hybrid inputs:

- ONT
- PacBio

Before hybrid assembly, determine whether reads have already been basecalled,
adapter/barcode trimmed, or quality filtered.

Do not automatically re-run Filtlong on a file already documented as filtered.

Do not send ONT/PacBio through ordinary Illumina fastp preprocessing.

Long-read-only datasets are outside the default path; evaluate a long-read-only
assembler such as Flye separately.
