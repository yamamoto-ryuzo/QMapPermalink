import re
from pathlib import Path
p = Path(__file__).resolve().parent.parent / 'tmp_qmap_test.js'
s = p.read_text(encoding='utf-8')
# tokenize: find 'try{', 'catch(' and braces
tokens = []
for m in re.finditer(r"try\s*\{|catch\s*\(|[{}]", s):
    tokens.append((m.group(0), m.start()))

stack = []
issues = []
for tok, pos in tokens:
    if re.match(r"try\s*\{", tok):
        stack.append((tok, pos))
    elif tok == '{':
        # ignore plain brace
        pass
    elif tok == '}':
        # this may close a block; try blocks are closed by a '}' before catch; we don't pop here
        pass
    elif re.match(r"catch\s*\(", tok):
        if not stack:
            issues.append((pos, tok))
        else:
            stack.pop()

print('total try count:', len([t for t in tokens if t[0].startswith('try')]))
print('total catch count:', len([t for t in tokens if t[0].startswith('catch')]))
print('issues (catch without try):', len(issues))
for pos, tok in issues[:20]:
    # print context
    start = max(0, pos-80)
    end = min(len(s), pos+80)
    print('--- pos', pos)
    print(s[start:end].replace('\n','\\n'))
