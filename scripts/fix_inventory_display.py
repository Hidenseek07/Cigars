from pathlib import Path
import re

p = Path('cigar_inventory.html')
html = p.read_text(encoding='utf-8')

tm = re.search(r'<table\b[^>]*\bid=["\']inventory-table["\'][^>]*>(.*?)</table>', html, re.I | re.S)
if not tm:
    raise SystemExit('inventory-table not found')
bm = re.search(r'<tbody\b[^>]*>(.*?)</tbody>', tm.group(1), re.I | re.S)
if not bm:
    raise SystemExit('tbody not found')

rows = re.findall(r'<tr\b[^>]*>(.*?)</tr>', bm.group(1), re.I | re.S)
entries = len(rows)
if not entries:
    raise SystemExit('no inventory rows found')

qtys = []
for row in rows:
    m = re.search(r'<td\b[^>]*\bclass=["\'][^"\']*\bqty\b[^"\']*["\'][^>]*>(.*?)</td>', row, re.I | re.S)
    if m:
        txt = re.sub(r'<[^>]+>', '', m.group(1))
        n = re.search(r'\d+', txt)
        qtys.append(int(n.group()) if n else 0)

cigars = sum(qtys)
graded = sum(1 for row in rows if re.search(r'class=["\'][^"\']*\bgrade\b', row, re.I))
pending = max(entries - graded, 0)

html = re.sub(
    r'<title>.*?</title>',
    f'<title>Cigar Inventory — {entries} Entries | Strength, Flavor &amp; Personal Ranking</title>',
    html,
    count=1,
    flags=re.I | re.S,
)

summary = (
    f'<div class="summary">'
    f'<div><strong>{entries}</strong><span>inventory entries</span></div>'
    f'<div><strong>{cigars}</strong><span>cigars recorded</span></div>'
    f'<div><strong>{graded}</strong><span>graded entries</span></div>'
    f'<div><strong>{pending}</strong><span>profiles pending</span></div>'
    f'</div><p class="update-note">'
)
html, n = re.subn(
    r'<div class="summary">.*?</div></div><p class="update-note">',
    lambda _m: summary,
    html,
    count=1,
    flags=re.I | re.S,
)
if n != 1:
    raise SystemExit('summary block not found')

style = '''<style id="inventory-column-text-normalization">
#inventory-table thead th{font-family:Arial,sans-serif!important;font-size:14px!important;line-height:1.35!important;font-weight:700!important;font-style:normal!important;letter-spacing:normal!important;vertical-align:middle!important}
#inventory-table tbody td,#inventory-table tbody td *{font-family:Arial,sans-serif!important;font-size:14px!important;line-height:1.35!important;font-style:normal!important;letter-spacing:normal!important;vertical-align:middle!important}
#inventory-table tbody td{font-weight:400!important}
#inventory-table tbody td.name,#inventory-table tbody td.qty{font-weight:600!important}
</style>'''
style_re = re.compile(r'<style\b[^>]*\bid=["\']inventory-column-text-normalization["\'][^>]*>.*?</style>', re.I | re.S)
if style_re.search(html):
    html = style_re.sub(lambda _m: style, html, count=1)
else:
    html = html.replace('</head>', style + '</head>', 1)

script = '''<script id="inventory-live-totals">
(function(){function refresh(){var t=document.getElementById('inventory-table');if(!t||!t.tBodies.length)return;var r=Array.from(t.tBodies[0].rows),e=r.length,c=r.reduce(function(s,row){var q=row.querySelector('td.qty'),n=q?parseInt(q.textContent.replace(/\\D/g,''),10):0;return s+(Number.isFinite(n)?n:0)},0),g=r.filter(function(row){return !!row.querySelector('.grade')}).length,p=Math.max(e-g,0);document.title='Cigar Inventory — '+e+' Entries | Strength, Flavor & Personal Ranking';var v={'inventory entries':e,'cigars recorded':c,'graded entries':g,'profiles pending':p};document.querySelectorAll('.summary div').forEach(function(card){var l=card.querySelector('span'),x=card.querySelector('strong');if(!l||!x)return;var k=l.textContent.trim().toLowerCase();if(Object.prototype.hasOwnProperty.call(v,k))x.textContent=v[k]})}if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',refresh);else refresh()})();
</script>'''
script_re = re.compile(r'<script\b[^>]*\bid=["\']inventory-live-totals["\'][^>]*>.*?</script>', re.I | re.S)
if script_re.search(html):
    html = script_re.sub(lambda _m: script, html, count=1)
else:
    html = html.replace('</body>', script + '</body>', 1)

p.write_text(html, encoding='utf-8')
print(f'Corrected: {entries} entries, {cigars} cigars, {graded} graded, {pending} pending')
