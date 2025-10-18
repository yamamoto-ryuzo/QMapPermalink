from pathlib import Path
import re

p = Path('tmp_qmap_test.js')
s = p.read_text(encoding='utf-8')

# Robust JS bracket matcher that ignores strings and comments (simple state machine)
pairs = {'{': '}', '(': ')', '[': ']'}
open_stack = []
issues = []

in_single = in_double = in_template = False
in_line_comment = in_block_comment = False
escaped = False

for i, ch in enumerate(s):
    # handle escapes inside strings
    if escaped:
        escaped = False
        continue

    # line comment end
    if in_line_comment:
        if ch == '\n':
            in_line_comment = False
        continue

    # block comment end
    if in_block_comment:
        if ch == '*' and i+1 < len(s) and s[i+1] == '/':
            in_block_comment = False
            # skip the '/'
            continue
        else:
            continue

    # string/template handling
    if in_single:
        if ch == "'":
            in_single = False
        elif ch == '\\':
            escaped = True
        continue
    if in_double:
        if ch == '"':
            in_double = False
        elif ch == '\\':
            escaped = True
        continue
    if in_template:
        if ch == '`':
            in_template = False
        elif ch == '\\':
            escaped = True
        continue

    # detect comment or string starts
    if ch == '/' and i+1 < len(s):
        nxt = s[i+1]
        if nxt == '/':
            in_line_comment = True
            continue
        if nxt == '*':
            in_block_comment = True
            continue

    if ch == "'":
        in_single = True
        continue
    if ch == '"':
        in_double = True
        continue
    if ch == '`':
        in_template = True
        continue

    # bracket handling
    if ch in pairs:
        open_stack.append((ch, i))
    elif ch in pairs.values():
        if not open_stack:
            issues.append(('unmatched_close', ch, i))
        else:
            last, pos = open_stack[-1]
            if pairs[last] == ch:
                open_stack.pop()
            else:
                issues.append(('mismatch', last, pos, ch, i))

# find stray 'catch' occurrences where preceding token isn't '}' at appropriate pos
for m in re.finditer(r"\bcatch\s*\(", s):
    start = m.start()
    j = start-1
    # skip whitespace/comments - approximate: skip spaces and newlines
    while j>=0 and s[j].isspace(): j-=1
    prev = s[j] if j>=0 else None
    if prev != '}':
        context = s[max(0,start-40):start+40].replace('\n','\\n')
        issues.append(('catch_without_closing_brace', start, context))

print('open_stack_remaining:', len(open_stack))
if open_stack:
    for ch,pos in open_stack[-10:]:
        ctx = s[max(0,pos-40):pos+40].replace('\n','\\n')
        print('  open', ch, 'at', pos, 'context:', ctx)

print('\nissues found:', len(issues))
for it in issues[:200]:
    print(it)

# Also print lines around earlier reported line ~77 (1-based)
lines = s.splitlines()
for i in range(70,86):
    if i-1 < len(lines):
        print(f"LINE {i}: "+lines[i-1])
