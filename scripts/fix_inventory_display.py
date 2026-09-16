from pathlib import Path
from html import unescape
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

# Quantity is the sixth table column. Read the visible cell instead of relying on
# optional classes or data attributes so every row is handled consistently.
def row_quantity(row):
    cells = re.findall(r'<td\b[^>]*>(.*?)</td>', row, re.I | re.S)
    if len(cells) < 6:
        return 0
    text = unescape(re.sub(r'<[^>]+>', '', cells[5])).strip()
    number = re.search(r'\d+', text)
    return int(number.group()) if number else 0

cigars = sum(row_quantity(row) for row in rows)

html = re.sub(
    r'<title>.*?</title>',
    f'<title>Cigar Inventory — {entries} Entries | Strength, Flavor &amp; Personal Ranking</title>',
    html,
    count=1,
    flags=re.I | re.S,
)

# Keep the summary limited to values that can be derived reliably from the table.
summary = (
    f'<div class="summary">'
    f'<div><strong>{entries}</strong><span>inventory entries</span></div>'
    f'<div><strong>{cigars}</strong><span>cigars recorded</span></div>'
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

# Synchronize any prose total with the actual table quantities.
html = re.sub(
    r'Total recorded:\s*\d+\s*cigars\s*across\s*\d+\s*entries',
    f'Total recorded: {cigars} cigars across {entries} entries',
    html,
    count=1,
    flags=re.I,
)

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

# Repair the existing table filter/status code so quantity totals come from the
# visible Quantity cell. This prevents NaN when data-quantity is absent.
helper = "const rowQuantity = row => { const cell=row.cells[5]; if(!cell) return 0; const match=cell.textContent.match(/\\d+/); return match ? Number(match[0]) : 0; };"
if 'const rowQuantity = row =>' not in html:
    html, helper_changes = re.subn(
        r'(const totalEntries\s*=\s*rows\.length;)',
        r'\1\n  ' + helper,
        html,
        count=1,
    )
    if helper_changes != 1:
        raise SystemExit('could not insert rowQuantity helper')

html, total_changes = re.subn(
    r'const totalQuantity\s*=\s*rows\.reduce\(\(sum,row\)\s*=>\s*sum\s*\+\s*Number\(row\.dataset\.quantity\),\s*0\);',
    'const totalQuantity = rows.reduce((sum,row) => sum + rowQuantity(row), 0);',
    html,
    count=1,
)
if total_changes != 1 and 'const totalQuantity = rows.reduce((sum,row) => sum + rowQuantity(row), 0);' not in html:
    raise SystemExit('could not repair totalQuantity calculation')

html, visible_changes = re.subn(
    r'quantity\s*\+=\s*Number\(row\.dataset\.quantity\);',
    'quantity+=rowQuantity(row);',
    html,
    count=1,
)
if visible_changes != 1 and 'quantity+=rowQuantity(row);' not in html:
    raise SystemExit('could not repair filtered quantity calculation')

script = '''<script id="inventory-live-totals">
(function(){function q(row){var cell=row.cells[5];if(!cell)return 0;var m=cell.textContent.match(/\\d+/);return m?Number(m[0]):0}function refresh(){var t=document.getElementById('inventory-table');if(!t||!t.tBodies.length)return;var r=Array.from(t.tBodies[0].rows),e=r.length,c=r.reduce(function(s,row){return s+q(row)},0);document.title='Cigar Inventory — '+e+' Entries | Strength, Flavor & Personal Ranking';var v={'inventory entries':e,'cigars recorded':c};document.querySelectorAll('.summary div').forEach(function(card){var l=card.querySelector('span'),x=card.querySelector('strong');if(!l||!x)return;var k=l.textContent.trim().toLowerCase();if(Object.prototype.hasOwnProperty.call(v,k))x.textContent=v[k]})}if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',refresh);else refresh()})();
</script>'''
script_re = re.compile(r'<script\b[^>]*\bid=["\']inventory-live-totals["\'][^>]*>.*?</script>', re.I | re.S)
if script_re.search(html):
    html = script_re.sub(lambda _m: script, html, count=1)
else:
    html = html.replace('</body>', script + '</body>', 1)

p.write_text(html, encoding='utf-8')
print(f'Corrected: {entries} entries, {cigars} cigars')
