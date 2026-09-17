from pathlib import Path
import re, html

s=Path('cigar_inventory.html').read_text(encoding='utf-8')
tm=re.search(r'<table\b[^>]*\bid=["\']inventory-table["\'][^>]*>(.*?)</table>',s,re.I|re.S)
bm=re.search(r'<tbody\b[^>]*>(.*?)</tbody>',tm.group(1),re.I|re.S)
rows=re.findall(r'<tr\b([^>]*)>(.*?)</tr>',bm.group(1),re.I|re.S)

def clean(x):
    x=re.sub(r'<br\s*/?>',' | ',x,flags=re.I)
    x=re.sub(r'<[^>]+>',' ',x)
    return ' '.join(html.unescape(x).split())

lines=[f'Total rows: {len(rows)}','Alignment anomalies:']
for idx,(attrs,row) in enumerate(rows,1):
    cells=re.findall(r'<td\b([^>]*)>(.*?)</td>',row,re.I|re.S)
    if len(cells) != 9:
        lines.append(f'{idx}: cell-count={len(cells)}')
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
        lines.append(f'{idx}: Brand={brand!r}; Line={line!r}; Vitola={size!r}; Quantity={qty!r}; Strength={strength!r}; Flags={" | ".join(flags)}')
Path('row39_column_diagnostic.txt').write_text('\n'.join(lines),encoding='utf-8')
