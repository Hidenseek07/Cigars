from pathlib import Path
import base64, io, re
from PIL import Image, ImageStat

CANON = Path('cigar_inventory.html')
V7 = Path('cigar_inventory_current_v7.html')


def table_rows(html):
    tm = re.search(r'<table\b[^>]*\bid=["\']inventory-table["\'][^>]*>(.*?)</table>', html, re.I | re.S)
    if not tm:
        raise SystemExit('inventory-table not found')
    bm = re.search(r'<tbody\b[^>]*>(.*?)</tbody>', tm.group(1), re.I | re.S)
    if not bm:
        raise SystemExit('tbody not found')
    body = bm.group(1)
    matches = list(re.finditer(r'<tr\b[^>]*>.*?</tr>', body, re.I | re.S))
    return bm, body, matches


def data_src_from_row(row):
    m = re.search(r'(<img\b[^>]*\bsrc=["\'])(data:[^"\']+)(["\'][^>]*>)', row, re.I | re.S)
    if not m:
        raise SystemExit('embedded image not found in target row')
    return m


def replace_row(html, entry_no, new_src, new_alt=None):
    tm = re.search(r'<table\b[^>]*\bid=["\']inventory-table["\'][^>]*>(.*?)</table>', html, re.I | re.S)
    bm = re.search(r'<tbody\b[^>]*>(.*?)</tbody>', tm.group(1), re.I | re.S)
    body = bm.group(1)
    matches = list(re.finditer(r'<tr\b[^>]*>.*?</tr>', body, re.I | re.S))
    row_m = matches[entry_no - 1]
    row = row_m.group(0)
    img = data_src_from_row(row)
    newrow = row[:img.start(2)] + new_src + row[img.end(2):]
    if new_alt is not None:
        newrow = re.sub(r'\balt=["\'][^"\']*["\']', f'alt="{new_alt}"', newrow, count=1, flags=re.I | re.S)
    newbody = body[:row_m.start()] + newrow + body[row_m.end():]
    return html[:bm.start(1)] + newbody + html[bm.end(1):]


def decode_data_uri(src):
    head, payload = src.split(',', 1)
    if ';base64' not in head:
        raise SystemExit('expected base64 image data URI')
    return head, base64.b64decode(payload)


def png_data_uri(img):
    buf = io.BytesIO()
    img.save(buf, format='PNG', optimize=True)
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode('ascii')


def crop_cao_band(src):
    _, raw = decode_data_uri(src)
    img = Image.open(io.BytesIO(raw)).convert('RGB')
    w, h = img.size
    hsv = img.convert('HSV')
    # CAO Italia's band is the most colorful region of the centered cigar.
    x0, x1 = int(w * 0.18), int(w * 0.82)
    y_min, y_max = int(h * 0.12), int(h * 0.82)
    sat = hsv.getchannel('S')
    vals = []
    for y in range(y_min, y_max):
        strip = sat.crop((x0, y, x1, y + 1))
        vals.append((ImageStat.Stat(strip).mean[0], y))
    # Smooth the saturation score so the center of the full band wins rather than a single bright edge.
    radius = max(10, int(h * 0.025))
    scores = []
    only = [v for v, _ in vals]
    for i, (_, y) in enumerate(vals):
        lo, hi = max(0, i - radius), min(len(vals), i + radius + 1)
        scores.append((sum(only[lo:hi]) / (hi - lo), y))
    band_y = max(scores)[1]

    crop_w = int(w * 0.78)
    crop_h = min(int(h * 0.34), int(w * 0.58))
    crop_h = max(crop_h, 150)
    left = max(0, (w - crop_w) // 2)
    top = max(0, min(h - crop_h, band_y - crop_h // 2))
    cropped = img.crop((left, top, left + crop_w, top + crop_h))
    return cropped, (w, h), (left, top, left + crop_w, top + crop_h)


canon = CANON.read_text(encoding='utf-8')
v7 = V7.read_text(encoding='utf-8')

# Entry 5: crop the existing CAO Italia Piazza source image down to its colorful band region.
_, body, rows = table_rows(canon)
row5 = rows[4].group(0)
src5 = data_src_from_row(row5).group(2)
crop5, original_size, crop_box = crop_cao_band(src5)
canon = replace_row(canon, 5, png_data_uri(crop5), 'CAO Italia Piazza band')

# Entry 22: restore the known-correct band-only crop from the older corrected v7 inventory.
_, v7body, v7rows = table_rows(v7)
v7row22 = v7rows[21].group(0)
src22 = data_src_from_row(v7row22).group(2)
canon = replace_row(canon, 22, src22, 'Perdomo Habano Bourbon Barrel-Aged Connecticut Churchill band')

CANON.write_text(canon, encoding='utf-8')
Path('thumbnail_fix_report.txt').write_text(
    f'Entry 5 CAO Italia Piazza: original={original_size}, crop_box={crop_box}, output={crop5.size}\n'
    f'Entry 22 Perdomo Habano Bourbon Barrel-Aged Connecticut Churchill: restored v7 band thumbnail\n',
    encoding='utf-8'
)
print('Thumbnail fixes applied to entries 5 and 22')
