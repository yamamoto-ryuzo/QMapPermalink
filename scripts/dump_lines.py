from pathlib import Path
p = Path('tmp_qmap_test.js')
s = p.read_text(encoding='utf-8')
lines = s.splitlines()
for i in range(60, 90):
    print(f'{i+1:4d}:', lines[i] if i < len(lines) else '')
