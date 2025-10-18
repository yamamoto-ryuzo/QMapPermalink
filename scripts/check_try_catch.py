import re
p = r"c:\\github\\QMapPermalink\\tmp_qmap_test.html"
s = open(p, 'r', encoding='utf-8').read()
lines = s.splitlines()

try_lines = [i for i,l in enumerate(lines, start=1) if 'try{' in l]
catch_lines = [i for i,l in enumerate(lines, start=1) if 'catch(' in l or l.strip().startswith('}catch') or 'catch ' in l]
print('try count:', len(try_lines), 'catch count:', len(catch_lines))
print('\ntry lines sample:', try_lines[:20])
print('\ncatch lines sample:', catch_lines[:20])

for ln in catch_lines:
    print('\n--- catch around line', ln, '---')
    start = max(1, ln-3)
    end = min(len(lines), ln+3)
    for j in range(start, end+1):
        marker = '>' if j==ln else ' '
        print(f"{marker}{j:4}: {lines[j-1]}")

print('\nScanning for suspicious sequences (}}catch or similar)')
for i,l in enumerate(lines, start=1):
    if '}}catch' in l or '} }catch' in l or '} } catch' in l:
        print('\nPossible malformed sequence at line', i, "->", l)

print('\nDone')
