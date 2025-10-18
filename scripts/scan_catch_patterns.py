from pathlib import Path
s = Path('tmp_qmap_test.js').read_text(encoding='utf-8')
import re
for m in re.finditer(r"\)\s*catch\b", s):
    print('match at', m.start(), 'context:', s[max(0,m.start()-40):m.start()+40].replace('\n','\\n'))
for m in re.finditer(r"\}\)\s*catch\b", s):
    print('match brace ) catch at', m.start())
# patterns where )() is directly followed by catch
for m in re.finditer(r"\)\s*\)\s*catch\b", s):
    print('match )()catch at', m.start(), s[max(0,m.start()-40):m.start()+40].replace('\n','\\n'))

# print nearby area around earlier reported pos ~line 77: approximate char position of that line
lines = s.splitlines()
for i,l in enumerate(lines, start=1):
    if i>=70 and i<=85:
        print(i, l)
