from pathlib import Path
import re, html as htmllib

P = Path('cigar_inventory.html')
s = P.read_text(encoding='utf-8')

def strip_tags(x):
    x = re.sub(r'<br\s*/?>', ' ', x, flags=re.I)
    x = re.sub(r'<[^>]+>', ' ', x)
    return ' '.join(htmllib.unescape(x).split())

def strength_note(value):
    base = value.replace('*','').strip()
    notes = {
        'Mild': 'Lower-intensity profile; generally the most approachable strength range.',
        'Mild–Medium': 'Approachable strength with more body and intensity than a mild cigar.',
        'Medium': 'Balanced mid-range strength and body.',
        'Medium–Full': 'Stronger profile with fuller body and greater nicotine potential.',
        'Full': 'High-intensity strength profile with the greatest nicotine potential.'
    }
    note = notes.get(base, 'Inventory strength classification for this cigar.')
    if '*' in value:
        note += ' Approximate classification; individual experience can vary.'
    return note

# Locate inventory tbody while preserving the rest of the large document exactly.
tm = re.search(r'<table\b[^>]*\bid=["\']inventory-table["\'][^>]*>.*?</table>', s, re.I|re.S)
if not tm:
    raise SystemExit('inventory-table not found')
table = tm.group(0)
bm = re.search(r'<tbody\b[^>]*>.*?</tbody>', table, re.I|re.S)
if not bm:
    raise SystemExit('tbody not found')
tbody = bm.group(0)
row_matches = list(re.finditer(r'<tr\b([^>]*)>.*?</tr>', tbody, re.I|re.S))
if len(row_matches) != 76:
    raise SystemExit(f'expected 76 rows, found {len(row_matches)}')

new_rows = []
report = []
for idx, rm in enumerate(row_matches, 1):
    row = rm.group(0)
    cells = list(re.finditer(r'<td\b([^>]*)>(.*?)</td>', row, re.I|re.S))
    if len(cells) != 9:
        raise SystemExit(f'entry {idx}: expected 9 cells, found {len(cells)}')

    # Column 4: Line / Cigar. Add class=name while preserving existing attributes/content.
    c4 = cells[3]
    attrs4 = c4.group(1)
    body4 = c4.group(2)
    if re.search(r'\bclass=["\'][^"\']*\bname\b', attrs4, re.I) is None:
        cm = re.search(r'\bclass=(["\'])(.*?)\1', attrs4, re.I|re.S)
        if cm:
            classes = cm.group(2).strip()
            repl = f'class={cm.group(1)}{classes} name{cm.group(1)}'
            attrs4 = attrs4[:cm.start()] + repl + attrs4[cm.end():]
        else:
            attrs4 = ' class="name"' + attrs4
    new_c4 = f'<td{attrs4}>{body4}</td>'

    # Column 7: Strength. Preserve useful existing explanatory text when present.
    c7 = cells[6]
    attrs7 = c7.group(1)
    body7 = c7.group(2)
    row_open = re.match(r'<tr\b([^>]*)>', row, re.I|re.S)
    row_attrs = row_open.group(1) if row_open else ''
    dm = re.search(r'\bdata-strength=["\']([^"\']+)["\']', row_attrs, re.I)
    strength = dm.group(1).strip() if dm else ''
    if not strength:
        # Fallback to visible first-line/strong/span text.
        strength = strip_tags(body7).split('  ')[0].strip()
    # Existing note text from source-caution or subnote is preferred.
    note = ''
    sm = re.search(r'<(?:span|div)\b[^>]*class=["\'][^"\']*(?:source-caution|subnote)[^"\']*["\'][^>]*>(.*?)</(?:span|div)>', body7, re.I|re.S)
    if sm:
        note = strip_tags(sm.group(1))
    else:
        plain = strip_tags(body7)
        # If the cell contains additional prose after the strength label, preserve it.
        canonical = strength.replace('*','').strip()
        for prefix in (strength, canonical):
            if prefix and plain.startswith(prefix):
                remainder = plain[len(prefix):].strip(' —:-')
                if remainder and remainder != plain:
                    note = remainder
                    break
    if not note:
        note = strength_note(strength)

    safe_strength = htmllib.escape(strength)
    safe_note = htmllib.escape(note)
    attrs7_clean = re.sub(r'\s*class=(["\']).*?\1', '', attrs7, count=1, flags=re.I|re.S)
    new_c7 = f'<td class="strength-cell"{attrs7_clean}><span class="strength-name">{safe_strength}</span><span class="source-caution">{safe_note}</span></td>'

    # Rebuild row replacing columns 4 and 7 only.
    replacements = [(cells[3].start(), cells[3].end(), new_c4), (cells[6].start(), cells[6].end(), new_c7)]
    for start, end, repl in sorted(replacements, reverse=True):
        row = row[:start] + repl + row[end:]
    new_rows.append(row)
    report.append(f'{idx}: line={strip_tags(body4)!r}; strength={strength!r}; note={note!r}')

# Replace rows sequentially in tbody.
out = []
last = 0
for rm, newrow in zip(row_matches, new_rows):
    out.append(tbody[last:rm.start()])
    out.append(newrow)
    last = rm.end()
out.append(tbody[last:])
new_tbody = ''.join(out)
new_table = table[:bm.start()] + new_tbody + table[bm.end():]
s = s[:tm.start()] + new_table + s[tm.end():]

# Ensure typography explicitly keeps these two columns bold while subnotes remain secondary.
style = '''<style id="line-strength-normalization">
#inventory-table tbody td.name{font-weight:700!important}
#inventory-table tbody td.strength-cell{font-weight:400!important}
#inventory-table tbody td.strength-cell .strength-name{display:block;font-weight:700!important}
#inventory-table tbody td.strength-cell .source-caution{display:block;margin-top:3px;font-size:12px!important;line-height:1.25!important;font-weight:400!important;opacity:.78}
</style>'''
style_re = re.compile(r'<style\b[^>]*\bid=["\']line-strength-normalization["\'][^>]*>.*?</style>', re.I|re.S)
if style_re.search(s):
    s = style_re.sub(style, s, count=1)
else:
    s = s.replace('</head>', style + '</head>', 1)

P.write_text(s, encoding='utf-8')
Path('line_strength_normalization_report.txt').write_text('\n'.join(report), encoding='utf-8')
print('Normalized Line / Cigar and Strength for all 76 rows')
