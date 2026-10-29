#!/usr/bin/env python3
"""Pixel-diff two screenshots without third-party packages (uses macOS sips, or Pillow when present).

Usage:
  pixeldiff.py design.png page.png [--out heat.png] [--threshold 0.1] [--scale 2] [--regions 8]
  pixeldiff.py crop in.png out.png X Y W H [--scale 2]      crop a region given in CSS px

Prints the image sizes, the share of differing pixels, and the biggest differing regions in CSS px
(pixel coordinates divided by --scale, the device pixel ratio both images were taken at). The heatmap
shows the design faded with differing pixels in red. Colour difference is pixelmatch's YIQ metric:
--threshold 0.1 ignores anti-aliasing-level noise, lower is stricter.
"""
import atexit, os, shutil, struct, subprocess, sys, tempfile
from collections import deque

TMP = tempfile.mkdtemp(prefix='design-qa-')
atexit.register(shutil.rmtree, TMP, True)


def sips(*args):
    if not shutil.which('sips'):
        return False
    return subprocess.run(['sips', *args], capture_output=True).returncode == 0


def load(path):
    """(width, height, rows of (r, g, b) blended on white)."""
    try:
        from PIL import Image
        im = Image.open(path).convert('RGBA')
        bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bg, im).convert('RGB')
        w, h = im.size
        px = list(im.getdata())
        return w, h, [px[y * w:(y + 1) * w] for y in range(h)]
    except ImportError:
        pass
    bmp = os.path.join(TMP, os.path.basename(path) + '.bmp')
    if not sips('-s', 'format', 'bmp', path, '--out', bmp):
        sys.exit('Need macOS sips or Pillow (pip install pillow) to read PNGs.')
    data = open(bmp, 'rb').read()
    offset = struct.unpack_from('<I', data, 10)[0]
    w, h = struct.unpack_from('<ii', data, 18)
    bpp = struct.unpack_from('<H', data, 28)[0]
    if bpp not in (24, 32):
        sys.exit(f'Unsupported BMP depth {bpp}')
    top_down, h = h < 0, abs(h)
    step = bpp // 8
    stride = (w * step + 3) & ~3
    rows = []
    for y in range(h):
        start = offset + (y if top_down else h - 1 - y) * stride
        row = []
        for x in range(w):
            i = start + x * step
            b, g, r = data[i], data[i + 1], data[i + 2]
            if step == 4 and data[i + 3] < 255:
                a = data[i + 3] / 255
                r, g, b = (round(c * a + 255 * (1 - a)) for c in (r, g, b))
            row.append((r, g, b))
        rows.append(row)
    return w, h, rows


def save(path, w, h, rows):
    stride = (w * 3 + 3) & ~3
    pad = b'\0' * (stride - w * 3)
    body = b''.join(bytes(c for r, g, b in row for c in (b, g, r)) + pad for row in reversed(rows))
    header = struct.pack('<2sIHHIIiiHHIIiiII', b'BM', 54 + len(body), 0, 0, 54, 40, w, h, 1, 24, 0, len(body), 2835, 2835, 0, 0)
    bmp = os.path.join(TMP, 'heat.bmp')
    open(bmp, 'wb').write(header + body)
    if not path.endswith('.bmp') and sips('-s', 'format', 'png', bmp, '--out', path):
        return path
    out = os.path.splitext(path)[0] + '.bmp'
    shutil.copy(bmp, out)
    return out


def yiq(c):
    r, g, b = c
    return (r * 0.29889531 + g * 0.58662247 + b * 0.11448223,
            r * 0.59597799 - g * 0.27417610 - b * 0.32180189,
            r * 0.21147017 - g * 0.52261711 + b * 0.31114694)


def regions(mask, w, h, cell, limit):
    cols, rws = (w + cell - 1) // cell, (h + cell - 1) // cell
    count = [[0] * cols for _ in range(rws)]
    for y in range(h):
        for x in range(w):
            if mask[y][x]:
                count[y // cell][x // cell] += 1
    seen = [[False] * cols for _ in range(rws)]
    found = []
    for cy in range(rws):
        for cx in range(cols):
            if not count[cy][cx] or seen[cy][cx]:
                continue
            q, seen[cy][cx] = deque([(cy, cx)]), True
            x0, y0, x1, y1, n = cx, cy, cx, cy, 0
            while q:
                y, x = q.popleft()
                n += count[y][x]
                x0, y0, x1, y1 = min(x0, x), min(y0, y), max(x1, x), max(y1, y)
                for ny in range(y - 1, y + 2):
                    for nx in range(x - 1, x + 2):
                        if 0 <= ny < rws and 0 <= nx < cols and count[ny][nx] and not seen[ny][nx]:
                            seen[ny][nx] = True
                            q.append((ny, nx))
            found.append((n, x0 * cell, y0 * cell, min((x1 + 1) * cell, w) - x0 * cell, min((y1 + 1) * cell, h) - y0 * cell))
    return sorted(found, reverse=True)[:limit]


def opt(args, name, default):
    return type(default)(args[args.index(name) + 1]) if name in args else default


def crop(args):
    src, out, x, y, w, h = args[:6]
    s = opt(args, '--scale', 2.0)
    x, y, w, h = (round(float(v) * s) for v in (x, y, w, h))
    shutil.copy(src, out)
    if not sips('-c', str(h), str(w), '--cropOffset', str(y), str(x), out):
        sys.exit('Cropping needs macOS sips.')
    print(out)


def main():
    args = sys.argv[1:]
    if args and args[0] == 'crop':
        return crop(args[1:])
    if len(args) < 2 or args[0] in ('-h', '--help'):
        sys.exit(__doc__)
    design, page = args[0], args[1]
    out = opt(args, '--out', os.path.join(os.path.dirname(os.path.abspath(page)), 'heat.png'))
    threshold, scale, limit = opt(args, '--threshold', 0.1), opt(args, '--scale', 2.0), opt(args, '--regions', 8)
    dw, dh, _ = load(design)
    pw, ph, _ = load(page)
    print(f'design {dw}x{dh}px ({dw / scale:g}x{dh / scale:g} css) · page {pw}x{ph}px ({pw / scale:g}x{ph / scale:g} css)')
    if (dw, dh) != (pw, ph):
        print(f'SIZE MISMATCH: page is {(pw - dw) / scale:+g} css px wide, {(ph - dh) / scale:+g} tall vs design. '
              'Fix the geometry first; the diff below resizes the page to the design and is approximate.')
        resized = os.path.join(TMP, 'page-resized.png')
        shutil.copy(page, resized)
        if not sips('-z', str(dh), str(dw), resized):
            sys.exit('Sizes differ and resizing needs macOS sips.')
        page = resized
    w, h, a = load(design)
    _, _, b = load(page)
    max_delta = 35215 * threshold * threshold
    mask, heat, diff = [], [], 0
    for y in range(h):
        mrow, hrow = [], []
        for x in range(w):
            p, q = a[y][x], b[y][x]
            if p == q:
                d = 0
            else:
                (y1, i1, q1), (y2, i2, q2) = yiq(p), yiq(q)
                d = 0.5053 * (y1 - y2) ** 2 + 0.299 * (i1 - i2) ** 2 + 0.1957 * (q1 - q2) ** 2
            hit = d > max_delta
            diff += hit
            mrow.append(hit)
            grey = round(255 - (255 - sum(p) / 3) * 0.2)
            hrow.append((255, 0, 0) if hit else (grey, grey, grey))
        mask.append(mrow)
        heat.append(hrow)
    total = w * h
    print(f'DIFF {diff / total:.2%} ({diff} of {total} px) at threshold {threshold:g}')
    saved = save(out, w, h, heat)
    print(f'heatmap {saved}')
    for n, x, y, rw, rh in regions(mask, w, h, max(4, round(4 * scale)), limit):
        print(f'  region x={x / scale:g} y={y / scale:g} w={rw / scale:g} h={rh / scale:g} css px · {n} px differ')


if __name__ == '__main__':
    main()
