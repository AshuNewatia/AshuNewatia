"""Render public GitHub metrics into a self-contained, animated SVG. Python stdlib only."""
import argparse
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from html import escape
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
USER = 'AshuNewatia'


def fetch(url, api=True):
    headers = {'User-Agent': 'AshuNewatia-profile', 'Accept': 'application/vnd.github+json' if api else 'text/html'}
    token = os.environ.get('GH_TOKEN')
    if token and api:
        headers['Authorization'] = f'Bearer {token}'
    with urlopen(Request(url, headers=headers), timeout=45) as response:
        text = response.read().decode()
    return json.loads(text) if api else text


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells = {}
        self.counts = {}
        self.tip = None
        self.text = ''

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('data-date') and a.get('data-level') is not None:
            self.cells[a['id']] = (a['data-date'], int(a['data-level']))
        if tag == 'tool-tip' and a.get('for'):
            self.tip, self.text = a['for'], ''

    def handle_data(self, text):
        if self.tip:
            self.text += text

    def handle_endtag(self, tag):
        if tag == 'tool-tip' and self.tip:
            match = re.match(r'\s*([\d,]+) contributions?\b', self.text)
            if match:
                self.counts[self.tip] = int(match[1].replace(',', ''))
            elif self.text.strip().startswith('No contributions'):
                self.counts[self.tip] = 0
            self.tip = None

    def days(self):
        if not self.cells or not all(k in self.counts for k in self.cells):
            raise ValueError('GitHub calendar format changed; keeping the previous chart.')
        return sorted((date.fromisoformat(d), level, self.counts[k]) for k, (d, level) in self.cells.items())


def render(user, repos, html):
    parser = CalendarParser()
    parser.feed(html)
    days = parser.days()
    today = datetime.now(timezone.utc).date()
    days = [d for d in days if today - timedelta(days=364) <= d[0] <= today]
    if not days:
        raise ValueError('No calendar data found.')
    total = sum(n for _, _, n in days)
    longest = run = 0
    for _, _, count in days:
        run = run + 1 if count else 0
        longest = max(longest, run)
    # An unfinished UTC day does not break the streak until it ends.
    current = 0
    reverse = days[::-1]
    if reverse[0][0] == today and reverse[0][2] == 0:
        reverse = reverse[1:]
    for _, _, count in reverse:
        if count == 0:
            break
        current += 1
    original = [r for r in repos if not r['fork']]
    languages = Counter(r['language'] for r in original if r.get('language'))
    stars = sum(r['stargazers_count'] for r in original)
    colors = ['#1A2337', '#154753', '#167F8A', '#16B5C7', '#67E8F9']
    s = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="690" viewBox="0 0 1000 690" role="img" aria-labelledby="title desc">',
         f'<title id="title">GitHub analytics for {USER}</title>',
         f'<desc id="desc">{total} public contributions in the displayed rolling year. Current streak {current} days, best streak {longest} days. Language distribution counts primary languages of owned non-fork public repositories.</desc>',
         '<defs><linearGradient id="edge"><stop stop-color="#22D3EE"/><stop offset="1" stop-color="#A78BFA"/></linearGradient></defs>',
         '<rect x="1" y="1" width="998" height="688" rx="20" fill="#090F1D" stroke="#253249"/>',
         '<path d="M30 1 H970" stroke="url(#edge)" stroke-width="3"/>']

    def text(x, y, value, size=13, color='#8EACC5', extra=''):
        s.append(f'<text x="{x}" y="{y}" fill="{color}" font-family="monospace" font-size="{size}" {extra}>{escape(str(value))}</text>')

    text(32, 40, '03 / GITHUB TELEMETRY', 16, '#67E8F9', 'letter-spacing="3"')
    s.append('<circle cx="936" cy="34" r="4" fill="#A3E635"><animate attributeName="opacity" values="1;.3;1" dur="2s" repeatCount="indefinite"/></circle>')
    text(32, 67, 'PUBLIC DATA / ROLLING YEAR / DAILY REFRESH', 11)
    metrics = [('CONTRIBUTIONS', total), ('CURRENT STREAK', f'{current}d'), ('BEST STREAK', f'{longest}d'), ('PUBLIC REPOS', user['public_repos']), ('STARS', stars), ('FOLLOWERS', user['followers'])]
    for i, (label, value) in enumerate(metrics):
        x = 32 + i * 158
        s.append(f'<rect x="{x}" y="90" width="146" height="96" rx="10" fill="#101A2D" stroke="#21324A"/>')
        text(x + 12, 116, label, 10)
        text(x + 12, 159, value, 30, '#E2F3FF')
    text(32, 222, 'CONTRIBUTION MATRIX', 13, '#A78BFA', 'letter-spacing="2"')
    start = days[0][0] - timedelta(days=(days[0][0].weekday() + 1) % 7)
    weeks = ((days[-1][0] - start).days // 7) + 1
    step = min(17, 915 / weeks)
    last_month = None
    for day, level, count in days:
        index = (day - start).days
        col, row = divmod(index, 7)
        x, y = 32 + col * step, 254 + row * 16
        if day.month != last_month and row == 0:
            text(x, 244, day.strftime('%b'), 10)
            last_month = day.month
        s.append(f'<rect x="{x:.1f}" y="{y}" width="{step-3:.1f}" height="12" rx="2" fill="{colors[level]}"><title>{day}: {count} contributions</title></rect>')
    # A decorative scanner crosses real calendar cells; it does not change their values.
    s.append('<rect x="32" y="252" width="2" height="110" fill="#E2F3FF" opacity=".3"><animate attributeName="x" values="32;945;32" dur="18s" repeatCount="indefinite"/></rect>')
    text(32, 390, f'{days[0][0]} — {days[-1][0]} / PUBLIC CONTRIBUTIONS', 10)
    text(32, 435, 'LANGUAGE SIGNAL', 13, '#A78BFA', 'letter-spacing="2"')
    text(32, 458, 'Primary language / owned non-fork public repositories', 11)
    palette = ['#22D3EE', '#A78BFA', '#A3E635', '#F472B6', '#FBBF24']
    denom = sum(languages.values())
    for i, (lang, count) in enumerate(languages.most_common(5)):
        y = 490 + i * 31
        text(32, y, lang, 12, '#E2F3FF')
        s.append(f'<rect x="185" y="{y-10}" width="285" height="10" rx="5" fill="#19263B"/><rect x="185" y="{y-10}" width="{285*count/denom:.2f}" height="10" rx="5" fill="{palette[i]}"/>')
        text(486, y, f'{count/denom:.0%}', 12)
    text(610, 435, 'BUILD SIGNAL', 13, '#A78BFA', 'letter-spacing="2"')
    text(610, 466, f'{len(original):02d} original public repositories', 14, '#E2F3FF')
    text(610, 496, f'{len(repos)-len(original):02d} public forks', 14, '#E2F3FF')
    text(610, 526, f'{sum(bool(n) for _,_,n in days):03d} active days in displayed year', 14, '#E2F3FF')
    text(610, 565, 'Actual data. No synthetic ranks.', 11)
    text(32, 658, 'SNAPSHOT / ' + datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'), 10)
    text(610, 658, 'SOURCE / GITHUB PUBLIC API + CALENDAR', 10)
    s.append('</svg>')
    return '\n'.join(s)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--cached', action='store_true', help='Use initial downloaded data, for local validation')
    args = p.parse_args()
    if args.cached:
        user = json.loads((ROOT / 'user.json').read_text())
        repos = json.loads((ROOT / 'repos.json').read_text())
        html = (ROOT / 'contributions.html').read_text()
    else:
        user = fetch(f'https://api.github.com/users/{USER}')
        repos = []
        page = 1
        while True:
            batch = fetch(f'https://api.github.com/users/{USER}/repos?type=owner&per_page=100&page={page}')
            repos.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        html = fetch(f'https://github.com/users/{USER}/contributions', api=False)
    svg = render(user, repos, html)
    dest = ROOT / 'assets' / 'analytics.svg'
    dest.parent.mkdir(exist_ok=True)
    temp = dest.with_suffix('.tmp')
    temp.write_text(svg)
    temp.replace(dest)
    print('Updated assets/analytics.svg')


if __name__ == '__main__':
    main()
