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

thead=re.search(r'<thead\b[^>]*>(.*?)</thead>',tm.group(1),re.I|re.S)
headers=[clean(x) for x in re.findall(r'<th\b[^>]*>(.*?)</th>',thead.group(1),re.I|re.S)] if thead else []

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

lines.append('\nTABLE-WIDE ALIGNMENT ANOMALIES')
for idx,(attrs,row) in enumerate(rows,1):
    cells=re.findall(r'<td\b([^>]*)>(.*?)</td>',row,re.I|re.S)
    if len(cells) != 9:
        lines.append(f'{idx:02d}: cell-count={len(cells)}')
        continue
    vals=[clean(body) for _,body in cells]
    brand,line,size,qty,strength=vals[2],vals[3],vals[4],vals[5],vals[6]
    flags=[]
    if ' — ' in brand:
        flags.append('brand contains em-dash / likely combined brand+line')
    if re.search(r'\b\d+(?:\.\d+|[¼½¾⅛⅜⅝⅞])?\s*[×x]\s*\d+\b', line, re.I):
        flags.append('line contains dimensions / likely size shifted left')
    if re.fullmatch(r'\d+', size):
        flags.append('vitola/size is numeric-only / likely quantity shifted left')
    if qty and not re.search(r'\d', qty):
        flags.append('quantity has no number / likely strength shifted left')
    if flags:
        lines.append(f'{idx:02d}: brand={brand!r} | line={line!r} | size={size!r} | qty={qty!r} | strength={strength!r} | ' + '; '.join(flags))

Path('row39_column_diagnostic.txt').write_text('\n'.join(lines),encoding='utf-8')
print('wrote row39_column_diagnostic.txt')
