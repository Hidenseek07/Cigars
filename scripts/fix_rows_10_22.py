from pathlib import Path
import re, html as htmlmod

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

    if re.search(r'\bdata-quantity=["\'][^"\']*["\']', open_tag, re.I):
        open_tag = re.sub(r'\bdata-quantity=["\'][^"\']*["\']', f'data-quantity="{data_quantity}"', open_tag, count=1, flags=re.I)
    else:
        open_tag = open_tag[:-1] + f' data-quantity="{data_quantity}">'

    replacements = {
        2: values['brand'],
        3: values['line'],
        4: values['vitola'],
        5: values['quantity'],
        6: values['strength'],
    }
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


# #5 CAO Italia Piazza: Italia is the line, Piazza is the 6 x 60 vitola.
set_row(5, {
    'brand': 'CAO',
    'line': 'Italia',
    'vitola': 'Piazza — 6 × 60',
    'quantity': '2',
    'strength': '<span class="strength-name">Medium</span><span class="source-caution">Balanced mid-range strength and body.</span>',
}, 2)

# #10 Alec Bradley Black Market Filthy Hooligan.
set_row(10, {
    'brand': 'Alec Bradley',
    'line': 'Black Market Filthy Hooligan',
    'vitola': 'Toro — 6 × 50',
    'quantity': '2',
    'strength': '<span class="strength-name">Medium</span><span class="source-caution">Balanced mid-range strength and body.</span>',
}, 2)

# #22 Perdomo Habano Bourbon Barrel-Aged Connecticut.
set_row(22, {
    'brand': 'Perdomo',
    'line': 'Habano Bourbon Barrel-Aged Connecticut',
    'vitola': 'Churchill — 7 × 54',
    'quantity': '2',
    'strength': '<span class="strength-name">Mild–Medium</span><span class="source-caution">Approachable strength with more body and intensity than a mild cigar.</span>',
    'flavor': 'Cream, caramel, cedar, almonds and leather, with a buttery-smooth finish.',
}, 2)

p.write_text(html, encoding='utf-8')


def clean(x):
    x = re.sub(r'<[^>]+>', ' ', x)
    return ' '.join(htmlmod.unescape(x).split())

expected = {
    5: ('CAO', 'Italia', 'Piazza — 6 × 60', '2', 'Medium'),
    10: ('Alec Bradley', 'Black Market Filthy Hooligan', 'Toro — 6 × 50', '2', 'Medium'),
    22: ('Perdomo', 'Habano Bourbon Barrel-Aged Connecticut', 'Churchill — 7 × 54', '2', 'Mild–Medium'),
}

final = p.read_text(encoding='utf-8')
report = []
for entry_id, exp in expected.items():
    m = re.search(rf'<tr\b[^>]*\bid=["\']cigar-{entry_id:02d}["\'][^>]*>(.*?)</tr>', final, re.I | re.S)
    if not m:
        raise SystemExit(f'verification row {entry_id} missing')
    cells = re.findall(r'<td\b[^>]*>(.*?)</td>', m.group(1), re.I | re.S)
    if len(cells) != 9:
        raise SystemExit(f'verification row {entry_id} has {len(cells)} cells')
    got = tuple(clean(cells[i]) for i in (2,3,4,5,6))
    # Strength contains the subnote after the primary label, so compare its first token/range.
    strength_primary = exp[4]
    ok = got[0] == exp[0] and got[1] == exp[1] and got[2] == exp[2] and got[3] == exp[3] and got[4].startswith(strength_primary)
    report.append(f'Entry {entry_id}: Brand={got[0]!r}; Line={got[1]!r}; Vitola={got[2]!r}; Quantity={got[3]!r}; Strength={got[4]!r}; VERIFIED={ok}')
    if not ok:
        raise SystemExit(f'verification failed for row {entry_id}: {got}')

Path('rows_5_10_22_verification.txt').write_text('\n'.join(report) + '\n', encoding='utf-8')
print('Repaired and verified inventory rows 5, 10 and 22')
