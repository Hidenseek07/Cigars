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

out=[f'Total rows: {len(rows)}']
for idx in list(range(7,14))+list(range(19,26)):
    attrs,row=rows[idx-1]
    cells=re.findall(r'<td\b([^>]*)>(.*?)</td>',row,re.I|re.S)
    out.append(f'\nENTRY {idx}')
    out.append(f'row attrs: {attrs.strip()}')
    out.append(f'cell count: {len(cells)}')
    for ci,(cattrs,body) in enumerate(cells,1):
        out.append(f'  col {ci} attrs: {cattrs.strip()}')
        out.append(f'  col {ci} text: {clean(body)}')

# Summarize all rows where col3 (Brand) appears to contain separator/dimensions or duplicate col4 content.
issues=[]
for idx,(attrs,row) in enumerate(rows,1):
    cells=re.findall(r'<td\b([^>]*)>(.*?)</td>',row,re.I|re.S)
    if len(cells)!=9:
        issues.append((idx,'cell-count',len(cells),''))
        continue
    texts=[clean(b) for _,b in cells]
    brand=texts[2]
    line=texts[3]
    size=texts[4]
    reasons=[]
    if ' — ' in brand or re.search(r'\b\d+(?:[¼½¾⅛⅜⅝⅞.]*)\s*[×x]\s*\d+\b',brand):
        reasons.append('brand contains dash/size-like content')
    if line and line.lower() in brand.lower() and line.lower()!=brand.lower():
        reasons.append('brand contains line/cigar text')
    if not line:
        reasons.append('line/cigar empty')
    if not size:
        reasons.append('size empty')
    if reasons:
        issues.append((idx,'; '.join(reasons),brand,line+' | '+size))

out.append('\nPOTENTIAL STRUCTURAL ISSUES')
for item in issues:
    out.append(repr(item))

Path('rows_10_22_diagnostic.txt').write_text('\n'.join(out),encoding='utf-8')
print('wrote rows_10_22_diagnostic.txt')