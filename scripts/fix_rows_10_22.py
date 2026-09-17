from pathlib import Path
import re

p = Path('cigar_inventory.html')
html = p.read_text(encoding='utf-8')

def set_row(entry_id, values, data_quantity):
    global html
    row_re = re.compile(rf'(<tr\b[^>]*\bid=["\']cigar-{entry_id:02d}["\'][^>]*>)(.*?)(</tr>)', re.I | re.S)
    m = row_re.search(html)
    if not m:
        raise SystemExit(f'row {entry_id} not found')

    open_tag, body, close_tag = m.groups()
    cells = list(re.finditer(r'<td\b([^>]*)>(.*?)</td>', body, re.I | re.S))
    if len(cells) != 9:
        raise SystemExit(f'row {entry_id} has {len(cells)} cells, expected 9')

    # Update row data-quantity to match the repaired visible Quantity cell.
    if re.search(r'\bdata-quantity=["\'][^"\']*["\']', open_tag, re.I):
        open_tag = re.sub(r'\bdata-quantity=["\'][^"\']*["\']', f'data-quantity="{data_quantity}"', open_tag, count=1, flags=re.I)
    else:
        open_tag = open_tag[:-1] + f' data-quantity="{data_quantity}">'

    replacements = {}
    # 0-based cell positions: Brand=2, Line=3, Vitola=4, Quantity=5, Strength=6, Flavor=7
    replacements[2] = values['brand']
    replacements[3] = values['line']
    replacements[4] = values['vitola']
    replacements[5] = values['quantity']
    replacements[6] = values['strength']
    if 'flavor' in values:
        replacements[7] = values['flavor']

    pieces = []
    pos = 0
    for i, cell in enumerate(cells):
        pieces.append(body[pos:cell.start()])
        attrs = cell.group(1)
        inner = cell.group(2)
        if i in replacements:
            if i == 3:
                attrs = ' class="name"'
            elif i == 5:
                attrs = ' class="qty"'
            elif i == 6:
                attrs = ' class="strength-cell"'
            elif i == 7:
                attrs = ' class="flavor-cell"'
            inner = replacements[i]
        pieces.append(f'<td{attrs}>{inner}</td>')
        pos = cell.end()
    pieces.append(body[pos:])
    new_body = ''.join(pieces)
    new_row = open_tag + new_body + close_tag
    html = html[:m.start()] + new_row + html[m.end():]

set_row(10, {
    'brand': 'Alec Bradley',
    'line': 'Black Market Filthy Hooligan',
    'vitola': 'Toro — 6 × 50',
    'quantity': '2',
    'strength': '<span class="strength-name">Medium</span><span class="source-caution">Balanced mid-range strength and body.</span>',
}, 2)

set_row(22, {
    'brand': 'Perdomo',
    'line': 'Habano Bourbon Barrel-Aged Connecticut',
    'vitola': 'Churchill — 7 × 54',
    'quantity': '2',
    'strength': '<span class="strength-name">Mild–Medium</span><span class="source-caution">Approachable strength with more body and intensity than a mild cigar.</span>',
    'flavor': 'Cream, caramel, cedar, almonds and leather, with a buttery-smooth finish.',
}, 2)

p.write_text(html, encoding='utf-8')
print('Repaired inventory rows 10 and 22')
