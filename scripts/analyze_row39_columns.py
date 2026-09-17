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

lines=[]
lines.append(f'Total rows: {len(rows)}')
for idx in range(34,46):
    attrs,row=rows[idx-1]
    cells=re.findall(r'<td\b([^>]*)>(.*?)</td>',row,re.I|re.S)
    lines.append(f'\nENTRY {idx}')
    lines.append(f'row attrs: {attrs.strip()}')
    lines.append(f'cell count: {len(cells)}')
    for ci,(cattrs,body) in enumerate(cells,1):
        if ci in (4,7):
            lines.append(f'  col {ci} attrs: {cattrs.strip()}')
            lines.append(f'  col {ci} text: {clean(body)}')
            lines.append(f'  col {ci} html: {body[:1200]}')

for label,start,end in [('before39',1,38),('from39',39,len(rows))]:
    patterns={4:{},7:{}}
    for idx in range(start,end+1):
        _,row=rows[idx-1]
        cells=re.findall(r'<td\b([^>]*)>(.*?)</td>',row,re.I|re.S)
        if len(cells)<7: continue
        for ci in (4,7):
            cattrs,body=cells[ci-1]
            structure=re.sub(r'>[^<]+<','><',body)
            structure=re.sub(r'\s+',' ',structure).strip()
            key=(cattrs.strip(), structure[:300])
            patterns[ci][key]=patterns[ci].get(key,0)+1
    lines.append(f'\nPATTERNS {label}')
    for ci in (4,7):
        lines.append(f' column {ci}:')
        for (a,st),count in sorted(patterns[ci].items(), key=lambda kv:-kv[1])[:20]:
            lines.append(f'   count={count} attrs={a!r} structure={st!r}')

Path('row39_column_diagnostic.txt').write_text('\n'.join(lines),encoding='utf-8')
print('wrote row39_column_diagnostic.txt')
