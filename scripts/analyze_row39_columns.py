from pathlib import Path
import re, html

p=Path('cigar_inventory.html')
s=p.read_text(encoding='utf-8')
tm=re.search(r'<table\b[^>]*\bid=["\']inventory-table["\'][^>]*>(.*?)</table>',s,re.I|re.S)
if not tm: raise SystemExit('inventory-table not found')
bm=re.search(r'<tbody\b[^>]*>(.*?)</tbody>',tm.group(1),re.I|re.S)
if not bm: raise SystemExit('tbody not found')
rows=re.findall(r'<tr\b([^>]*)>(.*?)</tr>',bm.group(1),re.I|re.S)

def clean(x):
    x=re.sub(r'<br\s*/?>',' | ',x,flags=re.I)
    x=re.sub(r'<[^>]+>',' ',x)
    return ' '.join(html.unescape(x).split())

# Capture table headers for column mapping.
thead=re.search(r'<thead\b[^>]*>(.*?)</thead>',tm.group(1),re.I|re.S)
headers=[]
if thead:
    headers=[clean(x) for x in re.findall(r'<th\b[^>]*>(.*?)</th>',thead.group(1),re.I|re.S)]

lines=[f'Total rows: {len(rows)}', f'Headers: {headers}']
for idx in [8,9,10,11,12,20,21,22,23,24]:
    attrs,row=rows[idx-1]
    cells=re.findall(r'<td\b([^>]*)>(.*?)</td>',row,re.I|re.S)
    lines.append(f'\nENTRY {idx}')
    lines.append(f'row attrs: {attrs.strip()}')
    lines.append(f'cell count: {len(cells)}')
    for ci,(cattrs,body) in enumerate(cells,1):
        h=headers[ci-1] if ci-1 < len(headers) else f'col{ci}'
        lines.append(f'  {ci}. {h}: attrs={cattrs.strip()!r} text={clean(body)!r}')

# Compare brand/line cells across all rows and flag likely merged brand+line patterns
lines.append('\nALL ROWS BRAND / LINE SNAPSHOT')
for idx,(attrs,row) in enumerate(rows,1):
    cells=re.findall(r'<td\b([^>]*)>(.*?)</td>',row,re.I|re.S)
    if len(cells) < 5: continue
    brand=clean(cells[2][1])
    line=clean(cells[3][1])
    size=clean(cells[4][1])
    lines.append(f'{idx:02d}: brand={brand!r} | line={line!r} | size={size!r}')

Path('row39_column_diagnostic.txt').write_text('\n'.join(lines),encoding='utf-8')
print('wrote row39_column_diagnostic.txt')
