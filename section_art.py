"""
Cyberpunk HUD artwork for the four README sections.

GitHub strips CSS and JavaScript from READMEs, but it does render animated SVG
files used as images. Every panel here is a self-contained SVG that uses SMIL
animation, so it works on github.com and in the mobile app.

Used by generate_terminal.py (profile, missions, toolkit, headers) and
scripts/update_analytics.py (live GitHub signal panel).
"""

from datetime import date, datetime
from pathlib import Path
from xml.sax.saxutils import escape


FONT = (
    "ui-monospace,SFMono-Regular,Menlo,Consolas,"
    "'Liberation Mono','Courier New',monospace"
)

CYAN = "#00ffcc"
PINK = "#ff0055"
VIOLET = "#a78bfa"
AMBER = "#ffb020"

TEXT = "#eafffb"
SOFT = "#b8cfd0"
MUTED = "#6b8a99"

DIRECTIVES = [
    "build_useful_products",
    "solve_challenging_problems",
    "keep_experimenting",
]

SECTIONS = {
    1: ("SYSTEM PROFILE", "IDENTITY LOADED", "IIT INDORE  /  STATUS: BUILDING", CYAN),
    2: ("FEATURED MISSIONS", "PROJECT ARCHIVE", "Selected builds, experiments, deployments", PINK),
    3: ("THE TOOLKIT", "MODULE INVENTORY", "Tech I use to turn ideas into systems", VIOLET),
    4: ("GITHUB SIGNAL", "ACTIVITY FEED", "A snapshot of recent GitHub activity", AMBER),
}


def e(value):
    return escape(str(value))


def char_width(size):
    return size * 0.62


def chip_width(text, size=13, pad=24):
    return round(len(text) * char_width(size) + pad)


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------

def frame_path(w, h, cut=18):
    return f"M{cut} 0H{w}V{h - cut}L{w - cut} {h}H0V{cut}Z"


def defs(accent, w, h, cut=18):
    return f"""
  <defs>
    <filter id="glow" x="-30%" y="-60%" width="160%" height="220%"
            color-interpolation-filters="sRGB">
      <feGaussianBlur stdDeviation="2.4" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
      <path d="M32 0H0V32" fill="none" stroke="{accent}" stroke-opacity=".08"/>
    </pattern>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0d151c"/>
      <stop offset="1" stop-color="#080b10"/>
    </linearGradient>
    <linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{accent}" stop-opacity="0"/>
      <stop offset=".5" stop-color="{accent}" stop-opacity=".14"/>
      <stop offset="1" stop-color="{accent}" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="clip"><path d="{frame_path(w, h, cut)}"/></clipPath>
  </defs>"""


def panel(w, h, accent, cut=18, sweep=True):
    path = frame_path(w, h, cut)
    sweep_svg = ""
    if sweep:
        sweep_svg = f"""
  <g clip-path="url(#clip)">
    <rect x="-200" y="0" width="200" height="{h}" fill="url(#sweep)">
      <animateTransform attributeName="transform" type="translate"
        from="0 0" to="{w + 200} 0" dur="7s" repeatCount="indefinite"/>
    </rect>
  </g>"""
    return f"""
  <path d="{path}" fill="url(#bg)"/>
  <path d="{path}" fill="url(#grid)"/>{sweep_svg}
  <path d="{path}" fill="none" stroke="{accent}" stroke-opacity=".32" stroke-width="1.2"/>
  <path d="{path}" fill="none" stroke="{accent}" stroke-width="2.2"
        pathLength="1000" stroke-dasharray="90 910" filter="url(#glow)">
    <animate attributeName="stroke-dashoffset" from="1000" to="0"
             dur="7s" repeatCount="indefinite"/>
  </path>
  <path d="M{w - 40} 10H{w - 10}V40" fill="none" stroke="{accent}" stroke-width="2"/>
  <path d="M10 {h - 40}V{h - 10}H40" fill="none" stroke="{accent}" stroke-width="2"/>"""


def document(w, h, title, desc, accent, body, cut=18, sweep=True):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"
     viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d"
     font-family="{FONT}">
  <title id="t">{e(title)}</title>
  <desc id="d">{e(desc)}</desc>{defs(accent, w, h, cut)}{panel(w, h, accent, cut, sweep)}
{body}
</svg>
"""


def chip(x, y, text, color, size=13, height=26, delay=0.0, pulse=True):
    width = chip_width(text, size)
    anim = ""
    if pulse:
        anim = (
            f'<animate attributeName="opacity" values="1;.6;1" dur="3.2s" '
            f'begin="{delay:.1f}s" repeatCount="indefinite"/>'
        )
    return width, f"""
  <g>{anim}
    <path d="M{x + 6} {y}H{x + width}V{y + height - 6}L{x + width - 6} {y + height}H{x}V{y + 6}Z"
          fill="{color}" fill-opacity=".10" stroke="{color}" stroke-opacity=".7"/>
    <text x="{x + width / 2}" y="{y + height / 2 + size * 0.36}" font-size="{size}"
          fill="{color}" text-anchor="middle">{e(text)}</text>
  </g>"""


def blink_dot(cx, cy, color, r=4, dur="1.4s"):
    return f"""
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" filter="url(#glow)">
    <animate attributeName="opacity" values="1;.2;1" dur="{dur}" repeatCount="indefinite"/>
  </circle>"""


def arrow(x, y, color, size=9, width=2):
    """Drawn north-east arrow so it never depends on font support."""
    return (
        f'<path d="M{x} {y + size}L{x + size} {y}M{x + 1} {y}H{x + size}V{y + size - 1}" '
        f'fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="square"/>'
    )


# ---------------------------------------------------------------------------
# Section headers
# ---------------------------------------------------------------------------

def header_svg(number):
    title, tag, desc, accent = SECTIONS[number]
    w, h = 1100, 120
    num = f"{number:02}"

    body = f"""
  <text x="36" y="92" font-size="88" font-weight="800" fill="none"
        stroke="{PINK}" stroke-width="1.4" opacity=".55">{num}
    <animate attributeName="x" values="36;36;40;33;36;36" keyTimes="0;.86;.89;.92;.95;1"
             dur="5s" repeatCount="indefinite"/>
  </text>
  <text x="36" y="92" font-size="88" font-weight="800" fill="none"
        stroke="{accent}" stroke-width="1.6" filter="url(#glow)">{num}</text>

  <text x="196" y="44" font-size="12" fill="{MUTED}" letter-spacing="5">SECTION  //  {num}</text>
  <text x="196" y="86" font-size="38" font-weight="800" fill="{TEXT}"
        letter-spacing="3" filter="url(#glow)">{e(title)}</text>

  <text x="1058" y="46" font-size="13" fill="{accent}" text-anchor="end"
        letter-spacing="3">{e(tag)}</text>
  <text x="1058" y="68" font-size="12" fill="{SOFT}" text-anchor="end">{e(desc)}</text>
  <path d="M760 84H1058" stroke="{accent}" stroke-opacity=".3"/>
  <text x="1058" y="102" font-size="11" fill="{MUTED}" text-anchor="end"
        letter-spacing="3">ONLINE</text>
  {blink_dot(985, 98, accent)}
"""
    return document(
        w, h,
        f"{num} / {title}",
        f"Section header: {title}",
        accent, body, cut=22,
    )


# ---------------------------------------------------------------------------
# 01 / Operator terminal
# ---------------------------------------------------------------------------

def profile_svg(data):
    w = 680
    accent = CYAN

    rows = [
        ("cmd", "whoami"),
        ("out", f"{data['name']}  ·  {data['title']}"),
        ("gap", ""),
        ("cmd", "cat bio.txt"),
        ("out", data["bio"]),
        ("out", "Connecting collaborative software, campus tools"),
        ("out", "and voice AI with practical problems."),
        ("gap", ""),
        ("cmd", "ls directives/"),
    ]
    for index, name in enumerate(DIRECTIVES, start=1):
        rows.append(("dir", f"{index:02}_{name}"))
    rows += [("gap", ""), ("cmd", "status")]

    start_y = 82
    line = 24
    cycle = 16
    total = len([r for r in rows if r[0] != "gap"]) + 1

    out = []
    y = start_y
    step = 0
    for kind, text in rows:
        if kind == "gap":
            y += 12
            continue
        begin = 0.04 + step * (0.7 / total)
        end = begin + 0.035
        step += 1
        clip_id = f"r{step}"
        width = 640
        out.append(f"""
  <clipPath id="{clip_id}"><rect x="28" y="{y - 16}" width="{width}" height="22">
    <animate attributeName="width" values="0;0;{width};{width}"
             keyTimes="0;{begin:.3f};{end:.3f};1" dur="{cycle}s" repeatCount="indefinite"/>
  </rect></clipPath>""")
        if kind == "cmd":
            out.append(
                f'<text x="28" y="{y}" font-size="14" clip-path="url(#{clip_id})">'
                f'<tspan fill="{accent}">operator@iit-indore</tspan>'
                f'<tspan fill="{MUTED}">:~$ </tspan>'
                f'<tspan fill="{TEXT}">{e(text)}</tspan></text>'
            )
        elif kind == "dir":
            number, rest = text.split("_", 1)
            out.append(
                f'<text x="46" y="{y}" font-size="14" clip-path="url(#{clip_id})">'
                f'<tspan fill="{PINK}">{number}</tspan>'
                f'<tspan fill="{SOFT}">_{e(rest)}</tspan></text>'
            )
        else:
            out.append(
                f'<text x="28" y="{y}" font-size="14" fill="{SOFT}" '
                f'clip-path="url(#{clip_id})">{e(text)}</text>'
            )
        y += line

    # status result + cursor
    out.append(f"""
  <g>
    <animate attributeName="opacity" values="0;0;1;1"
             keyTimes="0;{0.04 + (total - 0.5) * (0.7 / total):.3f};{0.04 + (total - 0.5) * (0.7 / total) + 0.02:.3f};1"
             dur="{cycle}s" repeatCount="indefinite"/>
    <circle cx="36" cy="{y - 5}" r="4" fill="{accent}" filter="url(#glow)"/>
    <text x="50" y="{y}" font-size="14" font-weight="700" fill="{accent}"
          letter-spacing="2" filter="url(#glow)">BUILDING</text>
    <rect x="140" y="{y - 13}" width="9" height="16" fill="{accent}">
      <animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/>
    </rect>
  </g>""")

    h = y + 34

    chrome = f"""
  <path d="M0 18H{w}V44H0Z" fill="{accent}" fill-opacity=".07"/>
  <path d="M0 44H{w}" stroke="{accent}" stroke-opacity=".3"/>
  <circle cx="30" cy="31" r="5" fill="{PINK}"/>
  <circle cx="50" cy="31" r="5" fill="{AMBER}"/>
  <circle cx="70" cy="31" r="5" fill="{accent}"/>
  <text x="{w / 2}" y="35" font-size="12" fill="{MUTED}" text-anchor="middle"
        letter-spacing="2">ashu — zsh — 80×24</text>"""

    return document(
        w, h,
        "Operator terminal",
        f"Terminal window introducing {data['name']}: {data['bio']}",
        accent, chrome + "".join(out), cut=18,
    )


def feed_label_svg():
    w, h = 300, 34
    accent = PINK
    body = f"""
  {blink_dot(26, 17, accent, 5, "1s")}
  <text x="44" y="22" font-size="12" fill="{accent}" letter-spacing="3">REC</text>
  <text x="{w - 18}" y="22" font-size="12" fill="{SOFT}" text-anchor="end"
        letter-spacing="2">WORKSPACE FEED // ACTIVE</text>"""
    return document(w, h, "Workspace feed", "Workspace feed is active", accent,
                    body, cut=8, sweep=False)


# ---------------------------------------------------------------------------
# 02 / Mission cards
# ---------------------------------------------------------------------------

MISSION_COLORS = [CYAN, PINK, VIOLET, AMBER]


def mission_svg(index, project):
    w, h = 1100, 180
    accent = MISSION_COLORS[(index - 1) % len(MISSION_COLORS)]
    num = f"{index:02}"

    tag_text = project["tag"].upper()
    tag_w, tag_svg = chip(188, 22, tag_text, accent, size=11, height=22, pulse=False)

    tech_parts = [part.strip() for part in project["tech"].split("/") if part.strip()]
    x = 188
    tech_svg = []
    for i, part in enumerate(tech_parts):
        width, svg = chip(x, 132, part, SOFT, size=13, height=28, delay=i * 0.4)
        tech_svg.append(svg)
        x += width + 10

    body = f"""
  <text x="34" y="104" font-size="70" font-weight="800" fill="none"
        stroke="{accent}" stroke-width="1.5" filter="url(#glow)">{num}</text>
  <text x="38" y="132" font-size="11" fill="{MUTED}" letter-spacing="5">MISSION</text>
  <path d="M158 24V156" stroke="{accent}" stroke-opacity=".35" stroke-dasharray="3 5"/>

  {tag_svg}
  <text x="188" y="86" font-size="30" font-weight="800" fill="{TEXT}"
        letter-spacing="2" filter="url(#glow)">{e(project["name"])}</text>
  <text x="188" y="116" font-size="15" fill="{SOFT}">{e(project["summary"])}</text>
  {"".join(tech_svg)}

  <text x="960" y="52" font-size="11" fill="{MUTED}" text-anchor="middle"
        letter-spacing="4">ACCESS POINT</text>
  <g>
    <path d="M868 66H1052V96L1038 110H858V80Z" fill="{accent}" fill-opacity=".14"
          stroke="{accent}" stroke-width="1.6" filter="url(#glow)">
      <animate attributeName="fill-opacity" values=".10;.28;.10" dur="2.4s"
               repeatCount="indefinite"/>
    </path>
    <text x="944" y="94" font-size="15" font-weight="700" fill="{accent}"
          text-anchor="middle" letter-spacing="2">OPEN REPO</text>
    <g>
      <animateTransform attributeName="transform" type="translate"
        values="0 0;3 -3;0 0" dur="1.6s" repeatCount="indefinite"/>
      {arrow(1000, 81, accent)}
    </g>
  </g>"""
    return document(
        w, h,
        f"Mission {num}: {project['name']}",
        f"{project['name']} — {project['summary']} Tech: {project['tech']}.",
        accent, body, cut=20,
    )


# ---------------------------------------------------------------------------
# 03 / Toolkit
# ---------------------------------------------------------------------------

def toolkit_svg(stack):
    w = 1100
    colors = [CYAN, PINK, VIOLET, AMBER]
    chip_x0, chip_max = 330, 1050
    row_gap = 14
    top = 24

    rows = []
    y = top
    total_tech = 0
    for index, (category, techs) in enumerate(stack.items(), start=1):
        accent = colors[(index - 1) % len(colors)]
        total_tech += len(techs)

        # Lay chips out with wrapping.
        placed = []
        cx, cy, lines = chip_x0, 0, 1
        for item in techs:
            width = chip_width(item, 14)
            if cx + width > chip_max:
                cx, cy, lines = chip_x0, cy + 40, lines + 1
            placed.append((cx, cy, item))
            cx += width + 12

        row_h = max(96, 32 + lines * 40)
        chips = []
        for i, (px, py, item) in enumerate(placed):
            chip_h = 30
            _, svg = chip(px, y + (row_h - (lines * 40 - 10)) / 2 + py, item, accent,
                          size=14, height=chip_h, delay=(index + i) * 0.35)
            chips.append(svg)

        mid = y + row_h / 2
        path = f"M18 {y}H{w - 18}V{y + row_h - 14}L{w - 32} {y + row_h}H0V{y + 18}Z"
        rows.append(f"""
  <g>
    <path d="{path}" fill="{accent}" fill-opacity=".04" stroke="{accent}" stroke-opacity=".35"/>
    <path d="M0 {y + 18}L18 {y}" stroke="{accent}" stroke-width="2.4"/>
    <polygon points="62,{mid - 30} 90,{mid - 15} 90,{mid + 15} 62,{mid + 30} 34,{mid + 15} 34,{mid - 15}"
             fill="{accent}" fill-opacity=".12" stroke="{accent}" stroke-width="1.6"
             filter="url(#glow)"/>
    <text x="62" y="{mid + 7}" font-size="19" font-weight="800" fill="{accent}"
          text-anchor="middle">{index:02}</text>
    <text x="118" y="{mid - 4}" font-size="22" font-weight="800" fill="{TEXT}"
          letter-spacing="2">{e(category)}</text>
    <text x="118" y="{mid + 18}" font-size="11" fill="{MUTED}"
          letter-spacing="2">MODULE_{index:02} // LOADED</text>
    <path d="M300 {y + 16}V{y + row_h - 16}" stroke="{accent}" stroke-opacity=".35"
          stroke-dasharray="3 5"/>
    {"".join(chips)}
  </g>""")
        y += row_h + row_gap

    footer_y = y + 18
    modules = len(stack)
    h = footer_y + 44

    body = "".join(rows) + f"""
  <text x="36" y="{footer_y + 8}" font-size="12" fill="{SOFT}" letter-spacing="3">
    {modules:02} MODULES  //  {total_tech:02} TECHNOLOGIES INSTALLED</text>
  <rect x="760" y="{footer_y - 3}" width="200" height="8" fill="none"
        stroke="{CYAN}" stroke-opacity=".5"/>
  <rect x="762" y="{footer_y - 1}" width="0" height="4" fill="{CYAN}" filter="url(#glow)">
    <animate attributeName="width" values="0;196;196" keyTimes="0;.7;1"
             dur="4s" repeatCount="indefinite"/>
  </rect>
  <text x="1058" y="{footer_y + 8}" font-size="11" fill="{CYAN}" text-anchor="end"
        letter-spacing="2">READY</text>"""

    desc = "; ".join(f"{k}: {', '.join(v)}" for k, v in stack.items())
    return document(w, h, "Toolkit module inventory", desc, VIOLET, body, cut=22)


# ---------------------------------------------------------------------------
# 04 / GitHub signal (live data)
# ---------------------------------------------------------------------------

LEVEL_COLORS = ["#101b21", "#0b4a42", "#04806a", "#00c9a7", "#00ffcc"]


def signal_svg(data):
    w = 1100
    accent = AMBER

    tiles = [
        ("CONTRIBUTIONS", f"{data['contributions']:,}", "LAST 365 DAYS", CYAN),
        ("ACTIVE DAYS", f"{data['active_days']:,}", "OF 365", PINK),
        ("REPOSITORIES", f"{data['original_repositories']:,}", "ORIGINAL · PUBLIC", VIOLET),
        ("FOLLOWERS", f"{data['followers']:,}", "GITHUB", AMBER),
    ]
    if data.get("stars"):
        tiles.insert(3, ("STARS", f"{data['stars']:,}", "ON ORIGINAL REPOS", AMBER))

    margin, gap = 32, 16
    tile_w = (w - 2 * margin - gap * (len(tiles) - 1)) / len(tiles)
    tile_y, tile_h = 28, 112

    tile_svg = []
    for i, (label, value, caption, color) in enumerate(tiles):
        x = margin + i * (tile_w + gap)
        size = 48 if len(value) <= 5 else 38
        tile_svg.append(f"""
  <g>
    <path d="M{x + 12} {tile_y}H{x + tile_w}V{tile_y + tile_h - 12}L{x + tile_w - 12} {tile_y + tile_h}H{x}V{tile_y + 12}Z"
          fill="{color}" fill-opacity=".05" stroke="{color}" stroke-opacity=".45"/>
    <path d="M{x} {tile_y + 12}L{x + 12} {tile_y}" stroke="{color}" stroke-width="2.4"/>
    <text x="{x + 18}" y="{tile_y + 26}" font-size="11" fill="{MUTED}"
          letter-spacing="3">{label}</text>
    <text x="{x + 18}" y="{tile_y + 76}" font-size="{size}" font-weight="800"
          fill="{color}" filter="url(#glow)">{value}
      <animate attributeName="opacity" values="1;.75;1" dur="3.5s"
               begin="{i * 0.5:.1f}s" repeatCount="indefinite"/>
    </text>
    <text x="{x + 18}" y="{tile_y + 99}" font-size="10" fill="{SOFT}"
          letter-spacing="2">{caption}</text>
  </g>""")

    calendar = data.get("calendar") or []
    heat = ""
    heat_bottom = tile_y + tile_h
    if calendar:
        cell, pitch = 14, 18
        grid_x, grid_y = 92, tile_y + tile_h + 72
        first = date.fromisoformat(calendar[0]["date"])
        offset = (first.weekday() + 1) % 7  # GitHub weeks start on Sunday

        cells, months, last_month = [], [], None
        for index, day in enumerate(calendar):
            slot = index + offset
            col, row = divmod(slot, 7)
            level = max(0, min(4, int(day["level"])))
            cells.append(
                f'<rect x="{grid_x + col * pitch}" y="{grid_y + row * pitch}" '
                f'width="{cell}" height="{cell}" rx="2" fill="{LEVEL_COLORS[level]}"/>'
            )
            d = date.fromisoformat(day["date"])
            if row == 0 and d.month != last_month:
                months.append((col, d.strftime("%b").upper()))
                last_month = d.month

        # Drop a cramped partial first month label.
        if len(months) > 1 and months[1][0] - months[0][0] < 3:
            months = months[1:]
        months = [
            f'<text x="{grid_x + col * pitch}" y="{grid_y - 10}" font-size="10" '
            f'fill="{MUTED}">{name}</text>'
            for col, name in months
        ]

        day_labels = "".join(
            f'<text x="{grid_x - 12}" y="{grid_y + r * pitch + 11}" font-size="10" '
            f'fill="{MUTED}" text-anchor="end">{name}</text>'
            for r, name in ((1, "MON"), (3, "WED"), (5, "FRI"))
        )
        columns = (len(calendar) + offset + 6) // 7
        grid_w = columns * pitch
        heat_bottom = grid_y + 7 * pitch

        legend_x = w - margin - 5 * pitch - 90
        legend = "".join(
            f'<rect x="{legend_x + 44 + i * pitch}" y="{heat_bottom + 14}" width="{cell}" '
            f'height="{cell}" rx="2" fill="{color}"/>'
            for i, color in enumerate(LEVEL_COLORS)
        )

        heat = f"""
  <text x="{margin + 4}" y="{tile_y + tile_h + 38}" font-size="12" fill="{accent}"
        letter-spacing="4">CONTRIBUTION MATRIX</text>
  <path d="M{margin + 4} {tile_y + tile_h + 46}H{w - margin}" stroke="{accent}" stroke-opacity=".25"/>
  {"".join(months)}{day_labels}
  {"".join(cells)}
  <g clip-path="url(#heat-clip)">
    <rect x="{grid_x - 80}" y="{grid_y - 4}" width="80" height="{7 * pitch + 6}"
          fill="url(#sweep)">
      <animateTransform attributeName="transform" type="translate"
        from="0 0" to="{grid_w + 160} 0" dur="5s" repeatCount="indefinite"/>
    </rect>
  </g>
  <clipPath id="heat-clip"><rect x="{grid_x}" y="{grid_y - 4}" width="{grid_w}"
        height="{7 * pitch + 6}"/></clipPath>
  <text x="{legend_x}" y="{heat_bottom + 25}" font-size="10" fill="{MUTED}">LESS</text>
  {legend}
  <text x="{legend_x + 44 + 5 * pitch + 6}" y="{heat_bottom + 25}" font-size="10"
        fill="{MUTED}">MORE</text>"""

    stamp = datetime.fromisoformat(data["fetched_at"]).strftime("%d %b %Y · %H:%M UTC").upper()
    footer_y = heat_bottom + 60 if calendar else tile_y + tile_h + 40
    h = footer_y + 24

    body = "".join(tile_svg) + heat + f"""
  {blink_dot(margin + 8, footer_y - 4, accent)}
  <text x="{margin + 22}" y="{footer_y}" font-size="11" fill="{SOFT}"
        letter-spacing="2">LIVE SNAPSHOT  //  {e(stamp)}  //  {e(str(data['contribution_source']).upper())}</text>"""

    desc = (
        f"{data['contributions']:,} contributions and {data['active_days']:,} active days "
        f"in the last year, {data['original_repositories']:,} original public repositories, "
        f"{data['followers']:,} followers."
    )
    return document(w, h, "GitHub activity signal", desc, accent, body, cut=22)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_static_assets(data, assets_dir):
    """Write every panel that comes from data.json."""
    assets_dir = Path(assets_dir)
    assets_dir.mkdir(exist_ok=True)

    files = {f"section-{n:02}.svg": header_svg(n) for n in SECTIONS}
    files["profile-terminal.svg"] = profile_svg(data)
    files["feed-label.svg"] = feed_label_svg()
    files["toolkit.svg"] = toolkit_svg(data["stack"])

    for index, project in enumerate(data["projects"], start=1):
        files[f"mission-{index:02}.svg"] = mission_svg(index, project)

    for name, content in files.items():
        (assets_dir / name).write_text(content, encoding="utf-8")

    return sorted(files)
