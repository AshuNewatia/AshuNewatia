"""Generate the animated robotic-font header (assets/hero.svg) used in README.md.

Run:  python scripts/generate_art.py

Why a custom font?  GitHub renders README SVGs as <img>, which cannot load web
fonts, so text would fall back to a plain system font.  Here every letter is
drawn as vector strokes in a built-in angular "robot" font, so it looks the
same on every device.  Edit the TEXT SETTINGS below, run the script, commit.
"""
import math
import random
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / 'assets'

# ───────────────────────── TEXT SETTINGS (edit me) ─────────────────────────
NAME = 'ASHU NEWATIA'
HUD_LEFT = 'STATUS: ONLINE'
HUD_RIGHT = 'LOC: IIT INDORE'
TYPED_LINES = [            # cycle in the hero (typing + erasing)
    '> FULL STACK DEVELOPER',
    '> VOICE AI EXPLORER',
    '> BUILDING AT IIT INDORE',
    '> PROBLEMS -> SOFTWARE',
]

CYAN, VIOLET, MAGENTA = '#22D3EE', '#A78BFA', '#F472B6'
INK, DIM, BG, LINE = '#E6F1FF', '#5B6B8C', '#0B1220', '#1E2B45'

# ───────────────────────── ROBOT FONT (6 x 10 grid) ────────────────────────
G = {
    'A': [[(0, 10), (0, 2.5), (2.5, 0), (3.5, 0), (6, 2.5), (6, 10)], [(0, 6), (6, 6)]],
    'B': [[(0, 10), (0, 0), (4.5, 0), (6, 1.5), (6, 3.5), (4.5, 5), (0, 5)],
          [(4.5, 5), (6, 6.5), (6, 8.5), (4.5, 10), (0, 10)]],
    'C': [[(6, 2), (4, 0), (2, 0), (0, 2), (0, 8), (2, 10), (4, 10), (6, 8)]],
    'D': [[(0, 0), (0, 10), (4, 10), (6, 8), (6, 2), (4, 0), (0, 0)]],
    'E': [[(6, 0), (0, 0), (0, 10), (6, 10)], [(0, 5), (4.5, 5)]],
    'F': [[(6, 0), (0, 0), (0, 10)], [(0, 5), (4.5, 5)]],
    'G': [[(6, 2), (4, 0), (2, 0), (0, 2), (0, 8), (2, 10), (4, 10), (6, 8), (6, 5), (3.5, 5)]],
    'H': [[(0, 0), (0, 10)], [(6, 0), (6, 10)], [(0, 5), (6, 5)]],
    'I': [[(1, 0), (5, 0)], [(3, 0), (3, 10)], [(1, 10), (5, 10)]],
    'J': [[(6, 0), (6, 8), (4, 10), (2, 10), (0, 8)]],
    'K': [[(0, 0), (0, 10)], [(6, 0), (1, 5), (6, 10)]],
    'L': [[(0, 0), (0, 10), (6, 10)]],
    'M': [[(0, 10), (0, 0), (3, 4), (6, 0), (6, 10)]],
    'N': [[(0, 10), (0, 0), (6, 10), (6, 0)]],
    'O': [[(2, 0), (4, 0), (6, 2), (6, 8), (4, 10), (2, 10), (0, 8), (0, 2), (2, 0)]],
    'P': [[(0, 10), (0, 0), (4.5, 0), (6, 1.5), (6, 4), (4.5, 5.5), (0, 5.5)]],
    'Q': [[(2, 0), (4, 0), (6, 2), (6, 8), (4, 10), (2, 10), (0, 8), (0, 2), (2, 0)], [(3.5, 7), (6, 10)]],
    'R': [[(0, 10), (0, 0), (4.5, 0), (6, 1.5), (6, 4), (4.5, 5.5), (0, 5.5)], [(3, 5.5), (6, 10)]],
    'S': [[(6, 2), (4, 0), (2, 0), (0, 2), (0, 3.5), (2, 5), (4, 5), (6, 6.5), (6, 8), (4, 10), (2, 10), (0, 8)]],
    'T': [[(0, 0), (6, 0)], [(3, 0), (3, 10)]],
    'U': [[(0, 0), (0, 8), (2, 10), (4, 10), (6, 8), (6, 0)]],
    'V': [[(0, 0), (3, 10), (6, 0)]],
    'W': [[(0, 0), (1.5, 10), (3, 6), (4.5, 10), (6, 0)]],
    'X': [[(0, 0), (6, 10)], [(6, 0), (0, 10)]],
    'Y': [[(0, 0), (3, 5), (6, 0)], [(3, 5), (3, 10)]],
    'Z': [[(0, 0), (6, 0), (0, 10), (6, 10)]],
    '0': [[(2, 0), (4, 0), (6, 2), (6, 8), (4, 10), (2, 10), (0, 8), (0, 2), (2, 0)], [(1.5, 8), (4.5, 2)]],
    '1': [[(1, 2), (3, 0), (3, 10)], [(1, 10), (5, 10)]],
    '2': [[(0, 2), (2, 0), (4, 0), (6, 2), (6, 3.5), (0, 10), (6, 10)]],
    '3': [[(0, 1), (1.5, 0), (4.5, 0), (6, 1.5), (6, 3.5), (4.5, 5), (2, 5)],
          [(4.5, 5), (6, 6.5), (6, 8.5), (4.5, 10), (1.5, 10), (0, 9)]],
    '4': [[(4.5, 10), (4.5, 0), (0, 6.5), (6, 6.5)]],
    '5': [[(6, 0), (0, 0), (0, 4.5), (4, 4.5), (6, 6.5), (6, 8), (4, 10), (2, 10), (0, 8)]],
    '6': [[(6, 1), (4.5, 0), (2, 0), (0, 2), (0, 8), (2, 10), (4, 10), (6, 8), (6, 6.5), (4, 4.5), (0, 4.5)]],
    '7': [[(0, 0), (6, 0), (2.5, 10)]],
    '8': [[(2, 0), (4, 0), (6, 1.5), (6, 3.5), (4.5, 5), (1.5, 5), (0, 3.5), (0, 1.5), (2, 0)],
          [(1.5, 5), (0, 6.5), (0, 8.5), (1.5, 10), (4.5, 10), (6, 8.5), (6, 6.5), (4.5, 5)]],
    '9': [[(0, 9), (1.5, 10), (4, 10), (6, 8), (6, 2), (4, 0), (2, 0), (0, 2), (0, 3.5), (2, 5.5), (6, 5.5)]],
    '.': [[(3, 9.4), (3, 10)]],
    ',': [[(3, 9), (2, 11)]],
    ':': [[(3, 2.6), (3, 3.2)], [(3, 6.8), (3, 7.4)]],
    '-': [[(1, 5), (5, 5)]],
    '/': [[(6, 0), (0, 10)]],
    '|': [[(3, -1), (3, 11)]],
    '+': [[(1, 5), (5, 5)], [(3, 2.5), (3, 7.5)]],
    '>': [[(1, 1), (5, 5), (1, 9)]],
    '<': [[(5, 1), (1, 5), (5, 9)]],
    '_': [[(0, 10), (6, 10)]],
    '!': [[(3, 0), (3, 6.5)], [(3, 9.4), (3, 10)]],
    "'": [[(3, 0), (3, 2.5)]],
    ' ': [],
}
GAP = 2.6                     # space between glyph cells (font units)
ADV = 6 + GAP                 # advance per character (monospaced)


def text_w(text, s):
    return len(text) * ADV * s - GAP * s


def glyph_d(ch, ox, oy, s):
    parts = []
    for line in G.get(ch.upper(), []):
        pts = [(ox + x * s, oy + y * s) for x, y in line]
        parts.append('M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in pts))
    return ' '.join(parts)


def text_d(text, x, y, s, only=None):
    """One path string for all characters.  `only` filters characters."""
    out = []
    for i, ch in enumerate(text):
        if only is not None and not only(ch):
            continue
        d = glyph_d(ch, x + i * ADV * s, y, s)
        if d:
            out.append(d)
    return ' '.join(out)


def stroke_attrs(s, w=0.85):
    return f'fill="none" stroke-width="{s * w:.2f}" stroke-linecap="square" stroke-linejoin="miter"'


def svg_open(w, h, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{title}"><title>{title}</title>')


SOFT = ('<filter id="soft" x="-20%" y="-50%" width="140%" height="200%">'
        '<feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/>'
        '<feMergeNode in="SourceGraphic"/></feMerge></filter>')
GLOW = ('<filter id="glow" x="-30%" y="-80%" width="160%" height="260%">'
        '<feGaussianBlur stdDeviation="7"/></filter>')


def chamfer(w, h, c=10):
    return f'M0 {c} L{c} 0 H{w - c} L{w} {c} V{h - c} L{w - c} {h} H{c} L0 {h - c}Z'


# ──────────────────────────── HERO (name + typing) ─────────────────────────
def hero():
    W, H = 640, 180
    rnd = random.Random(7)
    o = [svg_open(W, H, f'{NAME} — animated heading that types out roles: ' + ', '.join(t.strip('> ') for t in TYPED_LINES))]
    o.append('<defs>')
    o.append(f'<linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="{CYAN}"/>'
             f'<stop offset=".55" stop-color="{VIOLET}"/><stop offset="1" stop-color="{MAGENTA}"/></linearGradient>')
    o.append('<linearGradient id="beam" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
             '<stop offset=".5" stop-color="#fff" stop-opacity=".95"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')
    o.append('<linearGradient id="scan" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#22D3EE" stop-opacity="0"/>'
             '<stop offset=".5" stop-color="#22D3EE" stop-opacity=".18"/><stop offset="1" stop-color="#22D3EE" stop-opacity="0"/></linearGradient>')
    o.append('<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">'
             f'<path d="M40 0H0V40" fill="none" stroke="{LINE}" stroke-width="1" opacity=".7"/>'
             '<animate attributeName="x" from="0" to="40" dur="6s" repeatCount="indefinite"/></pattern>')
    o.append(SOFT + GLOW)
    o.append(f'<clipPath id="panel"><path d="{chamfer(W, H, 12)}"/></clipPath>')

    # name geometry
    s = 5
    nw = text_w(NAME, s)
    nx, ny = (W - nw) / 2, 36
    o.append('<mask id="nm">' + ''.join(
        f'<path d="{glyph_d(c, nx + i * ADV * s, ny, s)}" stroke="#fff" {stroke_attrs(s)}/>'
        for i, c in enumerate(NAME)) + '</mask>')

    # typing clip paths
    ts, tx_y, step, hold, erase, gap = 2.4, 114, 0.07, 1.9, 0.45, 0.35
    timeline, cursor_pts, t = [], [], 0.0
    for line in TYPED_LINES:
        n = len(line)
        left = (W - text_w(line, ts)) / 2
        start = t
        pts = [(start, 0)]
        for k in range(1, n + 1):
            pts.append((start + k * step, k))
        te = start + n * step + hold
        steps = 8
        for k in range(1, steps + 1):
            pts.append((te + erase * (k - 1) / steps, round(n * (1 - k / steps))))
        t = te + erase + gap
        timeline.append((line, left, start, pts, t))
    T = t

    def kt(v):
        return f'{min(v / T, 1):.4f}'

    for i, (line, left, start, pts, end) in enumerate(timeline):
        pts2 = [(0, 0)] + pts + [(end, 0), (T, 0)]
        # drop duplicate times
        clean, last = [], -1
        for tt, kk in pts2:
            if tt <= last:
                tt = last + 0.0005
            clean.append((tt, kk))
            last = tt
        clean[-1] = (T, 0)
        vals = ';'.join(f'{k * ADV * ts:.1f}' for _, k in clean)
        keys = ';'.join(kt(tt) for tt, _ in clean)
        o.append(f'<clipPath id="t{i}"><rect x="{left - 6:.1f}" y="{tx_y - 8}" height="{10 * ts + 16:.0f}" width="0">'
                 f'<animate attributeName="width" calcMode="discrete" dur="{T:.2f}s" repeatCount="indefinite" '
                 f'values="{vals}" keyTimes="{keys}"/></rect></clipPath>')
    o.append('</defs>')

    # panel + backdrop
    o.append(f'<g clip-path="url(#panel)"><rect width="{W}" height="{H}" fill="{BG}"/>'
             f'<rect width="{W}" height="{H}" fill="url(#grid)"/>')
    o.append(f'<rect width="{W}" height="90" y="-90" fill="url(#scan)"><animate attributeName="y" values="-90;{H}" dur="5s" repeatCount="indefinite"/></rect>')
    for _ in range(10):
        x, y, sz = rnd.randint(30, 610), rnd.randint(30, 150), rnd.choice([2, 3, 4])
        col = rnd.choice([CYAN, VIOLET, MAGENTA])
        dur, dl = rnd.uniform(5, 10), -rnd.uniform(0, 8)
        o.append(f'<rect x="{x}" y="{y}" width="{sz}" height="{sz}" fill="{col}" opacity="0">'
                 f'<animate attributeName="opacity" values="0;.8;0" dur="{dur:.1f}s" begin="{dl:.1f}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="y" values="{y};{y - 40}" dur="{dur:.1f}s" begin="{dl:.1f}s" repeatCount="indefinite"/></rect>')
    o.append('</g>')
    o.append(f'<path d="{chamfer(W, H, 12)}" fill="none" stroke="{LINE}" stroke-width="2"/>')

    # corner brackets
    for (x, y, dx, dy) in [(10, 10, 1, 1), (W - 10, 10, -1, 1), (10, H - 10, 1, -1), (W - 10, H - 10, -1, -1)]:
        o.append(f'<path d="M{x} {y + dy * 20}V{y}H{x + dx * 20}" fill="none" stroke="{CYAN}" stroke-width="2">'
                 f'<animate attributeName="opacity" values=".35;1;.35" dur="3s" repeatCount="indefinite"/></path>')

    # HUD
    hs = 1.05
    o.append(f'<path d="{text_d(HUD_LEFT, 56, 12, hs)}" stroke="{DIM}" {stroke_attrs(hs, 0.8)}/>')
    o.append(f'<rect x="38" y="13" width="8" height="8" fill="#34D399"><animate attributeName="opacity" values="1;.2;1" dur="1.4s" repeatCount="indefinite"/></rect>')
    o.append(f'<path d="{text_d(HUD_RIGHT, W - 40 - text_w(HUD_RIGHT, hs), 12, hs)}" stroke="{DIM}" {stroke_attrs(hs, 0.8)}/>')

    # name: glow, draw-in, beam
    allname = ' '.join(glyph_d(c, nx + i * ADV * s, ny, s) for i, c in enumerate(NAME) if c != ' ')
    o.append(f'<path d="{allname}" stroke="{CYAN}" {stroke_attrs(s, 1.0)} filter="url(#glow)" opacity=".5">'
             f'<animate attributeName="opacity" values=".25;.65;.25" dur="3.2s" repeatCount="indefinite"/></path>')
    for i, c in enumerate(NAME):
        d = glyph_d(c, nx + i * ADV * s, ny, s)
        if not d:
            continue
        b = 0.15 + i * 0.13
        o.append(f'<path d="{d}" pathLength="1" stroke="url(#g)" {stroke_attrs(s)} stroke-dasharray="1 1" stroke-dashoffset="1" opacity="0">'
                 f'<set attributeName="opacity" to="1" begin="{b:.2f}s" fill="freeze"/>'
                 f'<animate attributeName="stroke-dashoffset" from="1" to="0" begin="{b:.2f}s" dur="0.9s" fill="freeze"/></path>')
    o.append(f'<g mask="url(#nm)"><rect x="-200" y="{ny - 10}" width="160" height="{10 * s + 20}" fill="url(#beam)" transform="skewX(-20)">'
             f'<animateTransform attributeName="transform" type="translate" values="0 0;1400 0" dur="4.5s" begin="2.4s" repeatCount="indefinite" additive="sum"/></rect></g>')

    # underline with travelling pulses
    uy = ny + 10 * s + 14
    o.append(f'<path d="M{nx:.0f} {uy}H{nx + nw:.0f}" stroke="{LINE}" stroke-width="2"/>')
    for k, col in enumerate([CYAN, MAGENTA]):
        o.append(f'<path d="M{nx:.0f} {uy}H{nx + nw:.0f}" stroke="{col}" stroke-width="3" pathLength="1" stroke-dasharray=".08 .92" fill="none">'
                 f'<animate attributeName="stroke-dashoffset" values="1;0" dur="{3 + k * 1.5}s" repeatCount="indefinite"/></path>')

    # typed lines
    o.append(f'<g filter="url(#soft)">')
    for i, (line, left, *_r) in enumerate(timeline):
        o.append(f'<path d="{text_d(line, left, tx_y, ts)}" stroke="#A5F3FC" {stroke_attrs(ts, 0.8)} clip-path="url(#t{i})"/>')
    o.append('</g>')
    # cursor follows typed text
    xs, ks = [], []
    cur_pts = []
    for (line, left, start, pts, end) in timeline:
        for tt, kk in [(start, 0)] + pts[1:]:
            cur_pts.append((tt, left + kk * ADV * ts + 6))
    cur_pts.sort(key=lambda p: p[0])
    clean, last = [], -1
    for tt, xx in cur_pts:
        tt = max(tt, last + 0.0005)
        clean.append((tt, xx))
        last = tt
    clean.insert(0, (0, clean[0][1]))
    clean[1] = (max(clean[1][0], 0.001), clean[1][1])
    clean.append((T, clean[0][1]))
    vals = ';'.join(f'{x:.1f}' for _, x in clean)
    keys = ';'.join(kt(tt) for tt, _ in clean)
    o.append(f'<rect y="{tx_y}" width="{ts * 4:.0f}" height="{10 * ts:.0f}" fill="{CYAN}">'
             f'<animate attributeName="x" calcMode="discrete" dur="{T:.2f}s" repeatCount="indefinite" values="{vals}" keyTimes="{keys}"/>'
             f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur=".9s" repeatCount="indefinite" calcMode="discrete"/></rect>')

    # bottom status line
    by = H - 24
    o.append(f'<path d="M40 {by}H{W - 40}" stroke="{LINE}" stroke-width="2"/>')
    o.append(f'<path d="M40 {by}H{W - 40}" stroke="{VIOLET}" stroke-width="3" pathLength="1" stroke-dasharray=".05 .95" fill="none">'
             f'<animate attributeName="stroke-dashoffset" values="0;-1" dur="4s" repeatCount="indefinite"/></path>')
    for i in range(18):
        x = 40 + i * 14
        o.append(f'<rect x="{x}" y="{by + 8}" width="6" height="6" fill="{CYAN}" opacity=".15">'
                 f'<animate attributeName="opacity" values=".12;.9;.12" dur="2.4s" begin="{i * 0.1:.1f}s" repeatCount="indefinite"/></rect>')
    o.append('</svg>')
    return ''.join(o)


def main():
    svg = hero()
    (ASSETS / 'hero.svg').write_text(svg, encoding='utf-8')
    print(f'wrote assets/hero.svg ({len(svg) / 1024:.1f} KB)')


if __name__ == '__main__':
    main()
