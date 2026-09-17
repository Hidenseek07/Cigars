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

def rowvals(i):
    attrs,row=rows[i-1]
    cells=re.findall(r'<td\b([^>]*)>(.*?)</td>',row,re.I|re.S)
    vals=[clean(b) for _,b in cells]
    return vals

out=[]
for i in (10,22):
    vals=rowvals(i)
    out.append(f'ENTRY {i}')
    for n,v in enumerate(vals,1): out.append(f'col{n}: {v}')
    out.append('')

# reference correctly aligned rows near each target
for i in (9,11,21,23):
    vals=rowvals(i)
    out.append(f'REFERENCE {i}: brand={vals[2]!r}; line={vals[3]!r}; size={vals[4]!r}; qty={vals[5]!r}; strength={vals[6]!r}')

out.append('\nROWS WITH LIKELY BRAND/LINE SHIFT')
for i in range(1,len(rows)+1):
    vals=rowvals(i)
    if len(vals)!=9: continue
    brand,line,size,qty=vals[2],vals[3],vals[4],vals[5]
    # pattern: Brand contains delimiter + line, Line looks like vitola/size, Size looks numeric quantity
    line_looks_size = bool(re.search(r'\d+(?:[¼½¾⅛⅜⅝⅞.]*)?\s*[×x]\s*\d+', line))
    size_looks_qty = bool(re.fullmatch(r'\d+', size))
    brand_combined = (' — ' in brand or ' - ' in brand)
    if brand_combined and line_looks_size and size_looks_qty:
        out.append(f'{i}: brand={brand!r}; line={line!r}; size={size!r}; qty={qty!r}')

Path('brand_shift_10_22_report.txt').write_text('\n'.join(out),encoding='utf-8')
print('wrote brand_shift_10_22_report.txt')