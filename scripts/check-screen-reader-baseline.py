"""Offline frozen-source/fixture integrity, no provider calls or user-session access."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
manifest=json.loads((ROOT/'docs/baselines/screen-reader-v1.manifest.json').read_text(encoding='utf-8'))
for path,expected in manifest['python_screen_files_sha256'].items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected,path
for path,expected in manifest['hosted_files_sha256'].items():
    data=(ROOT/manifest['hosted_snapshot']/path).read_bytes()
    if path=='.gitignore':
        suffix=b'\n.openai/hosting.json\n';assert data.endswith(suffix);data=data[:-len(suffix)]
    assert hashlib.sha256(data).hexdigest()==expected,path
fixtures=json.loads((ROOT/'fixtures/screen-reader-baseline/manifest.json').read_text(encoding='utf-8'))
for case in fixtures['cases']:
    assert case['synthetic'] is True
    assert hashlib.sha256((ROOT/case['image']).read_bytes()).hexdigest()==case['sha256'],case['id']
from prototypes.lab_tracking.guided import POLICY
from prototypes.lab_tracking.definition import DEFINITION
host=ROOT/manifest['hosted_snapshot']/'data'
assert POLICY==json.loads((host/'guided-policy.json').read_text(encoding='utf-8'))
assert DEFINITION==json.loads((host/'experiment.json').read_text(encoding='utf-8'))
print('PASS: 31 frozen Python screen files, 43 hosted files, four synthetic fixtures; definition/policy parity')
