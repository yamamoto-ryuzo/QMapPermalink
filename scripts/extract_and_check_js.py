import re
import sys
from pathlib import Path
p = Path(__file__).resolve().parent.parent / 'tmp_qmap_test.html'
if not p.exists():
    print('tmp html not found:', p)
    sys.exit(2)
s = p.read_text(encoding='utf-8')
m = re.search(r'<script>(.*?)</script>', s, flags=re.S|re.I)
if not m:
    print('no <script> block found')
    sys.exit(2)
js = m.group(1)
out = p.with_suffix('.js')
out.write_text(js, encoding='utf-8')
print('wrote', out)
# run node --check if available
import shutil, subprocess
node = shutil.which('node')
if not node:
    print('node not found in PATH; cannot run syntax check')
    sys.exit(0)
print('running node --check...')
try:
    r = subprocess.run([node, '--check', str(out)], capture_output=True, text=True)
    print('returncode', r.returncode)
    print(r.stdout)
    print(r.stderr)
except Exception as e:
    print('error running node:', e)
    sys.exit(1)
