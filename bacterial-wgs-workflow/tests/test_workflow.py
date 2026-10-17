import csv
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='wgs-review-')
        self.addCleanup(self.tmp.cleanup)
        self.p = Path(self.tmp.name)
        self.env = os.environ.copy()
        self.env.update(WGS_SKILL=str(ROOT), SLURM_SUBMIT_DIR=str(self.p),
                        SLURM_ARRAY_TASK_ID='1', SLURM_CPUS_PER_TASK='1',
                        SLURM_MEM_PER_NODE='32768')
        self.r1 = self.p / 'isolate_R1.fastq'
        self.r2 = self.p / 'isolate_R2.fastq'
        for p in (self.r1, self.r2):
            p.write_text('@read\nACGT\n+\nIIII\n')
        self.manifest = self.p / 'samples.tsv'
        self.write_manifest()

    def write_manifest(self, sid='isolate', long='', platform=''):
        self.manifest.write_text('sample_id\tr1\tr2\tlong_reads\tlong_platform\n'
                                 f'{sid}\t{self.r1}\t{self.r2}\t{long}\t{platform}\n')

    def run_script(self, name, *args, ok=True):
        p = subprocess.run([sys.executable, str(ROOT/'scripts'/name), *map(str,args)],
                           cwd=self.p, env=self.env, text=True, capture_output=True)
        if ok:
            self.assertEqual(p.returncode, 0, p.stdout+p.stderr)
        else:
            self.assertNotEqual(p.returncode, 0, p.stdout+p.stderr)
        return p

    def shell(self, code, ok=True):
        p = subprocess.run(['bash','-c',code], cwd=self.p, env=self.env,
                           text=True,capture_output=True)
        if ok:
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        else:
            self.assertNotEqual(p.returncode,0,p.stdout+p.stderr)
        return p

    def test_manifest(self):
        self.run_script('validate_samplesheet.py', self.manifest)
        for sid,long,platform in [('../escape','',''),('isolate','','ONT'),('isolate',str(self.r1),'')]:
            self.write_manifest(sid,long,platform)
            self.run_script('validate_samplesheet.py', self.manifest,ok=False)
        self.write_manifest()
        self.manifest.write_text(self.manifest.read_text()+'\n')
        self.run_script('validate_samplesheet.py',self.manifest,ok=False)
        self.write_manifest()
        self.r2.write_text('')
        self.run_script('validate_samplesheet.py',self.manifest,ok=False)

    def test_discovery_duplicates_and_overwrite(self):
        data=self.p/'raw'; data.mkdir()
        (data/'isolate_R1.fastq').write_text('read')
        (data/'isolate_R2.fastq').write_text('read')
        out=self.p/'inferred.tsv'
        self.run_script('build_samplesheet.py',data,'-o',out)
        self.run_script('build_samplesheet.py',data,'-o',out,ok=False)
        (data/'duplicate').mkdir()
        (data/'duplicate'/'isolate_R1.fastq').write_text('read')
        self.run_script('build_samplesheet.py',data,'-o',self.p/'new.tsv',ok=False)
        self.assertFalse((self.p/'new.tsv').exists())

    def test_shell_field_preservation(self):
        code='set -euo pipefail; SAMPLES=samples.tsv; source "$WGS_SKILL/scripts/array_common.sh"; printf "%s|%s|%s" "$sample" "$long_reads" "$long_platform"'
        self.assertEqual(self.shell(code).stdout,'isolate||')
        self.write_manifest(long=str(self.r1),platform='ONT')
        self.assertEqual(self.shell(code).stdout,f'isolate|{self.r1}|ONT')
        self.write_manifest(platform='ONT')
        self.shell(code,ok=False)
        self.env['SLURM_ARRAY_TASK_ID']='2'
        self.shell(code,ok=False)

    def test_stage_routing_memory_and_bakta_outputs(self):
        # Mock executables test wrapper contracts, not biological algorithms.
        bin=self.p/'bin'; bin.mkdir()
        mock=bin/'mock'
        mock.write_text('''#!/bin/bash
set -eu
if [[ "$0" == *bakta || "$0" == *quast.py ]]; then
  [[ "$1" == *.fasta && -s "$1" ]] || exit 89
fi
out=''; prefix=''
while (($#)); do
  case "$1" in
    -o|--output) out="$2"; shift 2;;
    --prefix) prefix="$2"; shift 2;;
    -m) echo "$2" > memory.txt; shift 2;;
    *) shift;;
  esac
done
[[ ! -e "$out" ]] || exit 88
mkdir -p "$out"
if [[ "$0" == *spades.py ]]; then
  printf '>contig\\nACGT\\n' > "$out/contigs.fasta"
elif [[ "$0" == *unicycler ]]; then
  printf '>contig\\nACGT\\n' > "$out/assembly.fasta"
elif [[ "$0" == *quast.py ]]; then
  printf 'Assembly\\tisolate\\nTotal length\\t4\\nN50\\t4\\n' > "$out/report.tsv"
else
  for ext in ${MOCK_EXTS:-gff3 gbff faa ffn fna tsv}; do echo output > "$out/$prefix.$ext"; done
fi
''')
        mock.chmod(0o755)
        for name in ('spades.py','unicycler','bakta','quast.py'):
            (bin/name).symlink_to(mock)
        self.env['PATH']=str(bin)+os.pathsep+self.env['PATH']
        for mate in ('R1','R2'):
            clean=self.p/f'data/clean/isolate/isolate_HQ_{mate}.fq.gz'
            clean.parent.mkdir(parents=True,exist_ok=True); clean.write_text('mock')
        self.shell('bash "$WGS_SKILL/scripts/run_unicycler_array.sh" samples.tsv')
        self.assertFalse((self.p/'assembly/isolate/unicycler').exists())
        self.env['SPADES_MEM_GB']='32'
        self.shell('bash "$WGS_SKILL/scripts/run_spades_array.sh" samples.tsv',ok=False)
        del self.env['SPADES_MEM_GB']
        self.shell('bash "$WGS_SKILL/scripts/run_spades_array.sh" samples.tsv')
        self.assertEqual((self.p/'memory.txt').read_text().strip(),'28')
        self.assertTrue((self.p/'assembly/isolate/isolate.fasta').is_file())
        self.shell('bash "$WGS_SKILL/scripts/run_quast_array.sh" samples.tsv')
        self.run_script('summarize_workflow.py', self.manifest, '-o', self.p/'summary.tsv')
        with (self.p/'summary.tsv').open() as fh:
            self.assertEqual(next(csv.DictReader(fh, delimiter='\t'))['assembly_status'], 'COMPLETE')
        self.shell('bash "$WGS_SKILL/scripts/run_spades_array.sh" samples.tsv',ok=False)
        db=self.p/'db'; db.mkdir(); self.env['BAKTA_DB']=str(db)
        self.shell('bash "$WGS_SKILL/scripts/run_bakta_array.sh" samples.tsv')
        self.shell('bash "$WGS_SKILL/scripts/run_bakta_array.sh" samples.tsv',ok=False)
        self.write_manifest(sid='hybrid', long=str(self.r1), platform='ONT')
        for mate in ('R1','R2'):
            clean=self.p/f'data/clean/hybrid/hybrid_HQ_{mate}.fq.gz'
            clean.parent.mkdir(parents=True,exist_ok=True); clean.write_text('mock')
        self.shell('bash "$WGS_SKILL/scripts/run_unicycler_array.sh" samples.tsv')
        self.assertEqual((self.p/'assembly/hybrid/hybrid.fasta').read_text(), '>contig\nACGT\n')
        self.assertTrue((self.p/'assembly/hybrid/unicycler/assembly.fasta').is_file())
        self.write_manifest(sid='partial')
        asm=self.p/'assembly/partial/partial.fasta'; asm.parent.mkdir(); asm.write_text('>contig\nACGT\n')
        self.env['MOCK_EXTS']='gff3'
        self.shell('bash "$WGS_SKILL/scripts/run_bakta_array.sh" samples.tsv',ok=False)

    def test_summary_partial_annotation(self):
        ann=self.p/'annotation/isolate'; ann.mkdir(parents=True)
        (ann/'isolate.gff3').write_text('partial')
        out=self.p/'summary.tsv'
        self.run_script('summarize_workflow.py',self.manifest,'-o',out)
        with out.open() as fh:
            row=next(csv.DictReader(fh,delimiter='\t'))
        self.assertEqual(row['bakta_status'],'MISSING')
        self.assertIn('quast_missing_or_incomplete',row['warning'])

    def test_syntax(self):
        for path in (ROOT/'scripts').glob('*.sh'):
            p=subprocess.run(['bash','-n',str(path)],text=True,capture_output=True)
            self.assertEqual(p.returncode,0,p.stderr)
        for path in (ROOT/'scripts').glob('*.py'):
            compile(path.read_text(),str(path),'exec')

if __name__=='__main__':
    unittest.main(verbosity=2)
