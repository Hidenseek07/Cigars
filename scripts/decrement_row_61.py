from pathlib import Path
import re, html as htmlmod

p=Path('cigar_inventory.html')
s=p.read_text(encoding='utf-8')
row_re=re.compile(r'(<tr\b[^>]*\bid=["\']cigar-61["\'][^>]*>)(.*?)(</tr>)',re.I|re.S)
m=row_re.search(s)
if not m: raise SystemExit('row 61 not found')
open_tag,body,close=m.groups()
cells=list(re.finditer(r'<td\b([^>]*)>(.*?)</td>',body,re.I|re.S))
if len(cells)!=9: raise SystemExit(f'row 61 has {len(cells)} cells')

def clean(x):
    x=re.sub(r'<[^>]+>',' ',x)
    return ' '.join(htmlmod.unescape(x).split())
brand=clean(cells[2].group(2)); line=clean(cells[3].group(2)); vitola=clean(cells[4].group(2)); qty_text=clean(cells[5].group(2))
qm=re.search(r'\d+',qty_text)
if not qm: raise SystemExit(f'row 61 quantity is not numeric: {qty_text!r}')
old=int(qm.group()); new=3
# Set exact intended post-smoking quantity so reruns are idempotent.
if re.search(r'\bdata-quantity=["\'][^"\']*["\']',open_tag,re.I):
    open_tag=re.sub(r'\bdata-quantity=["\'][^"\']*["\']',f'data-quantity="{new}"',open_tag,count=1,flags=re.I)
else:
    open_tag=open_tag[:-1]+f' data-quantity="{new}">'
c=cells[5]
attrs=c.group(1)
newcell=f'<td{attrs}>{new}</td>'
newbody=body[:c.start()]+newcell+body[c.end():]
news=s[:m.start()]+open_tag+newbody+close+s[m.end():]
p.write_text(news,encoding='utf-8')
Path('row61_quantity_verification.txt').write_text(f"Entry 61: Brand={brand!r}; Line={line!r}; Vitola={vitola!r}; Quantity {old} -> {new}; intended net change from original 4 = -1\n",encoding='utf-8')
print(f'Entry 61 {brand} {line}: quantity {old} -> {new}')
