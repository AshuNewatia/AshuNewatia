"""Fetch GitHub data and update a marked README section plus a text-free calendar.
Python standard library only. No fixture/cached-data mode is used in production.
"""
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from html import escape
from html.parser import HTMLParser
import argparse
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
START = '<!-- GITHUB-TELEMETRY:START -->'
END = '<!-- GITHUB-TELEMETRY:END -->'
API = 'https://api.github.com'


def request(url, payload=None, api=True):
    headers = {'User-Agent': 'editable-profile-telemetry', 'Accept': 'application/vnd.github+json' if api else 'text/html'}
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if token and api:
        headers['Authorization'] = 'Bearer ' + token
    if payload is not None:
        headers['Content-Type'] = 'application/json'
    req = Request(url, data=json.dumps(payload).encode() if payload is not None else None, headers=headers)
    for attempt in range(3):
        try:
            with urlopen(req, timeout=35) as response:
                text = response.read().decode('utf-8')
            return json.loads(text) if api else text
        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise RuntimeError(f'GitHub request failed: HTTP {error.code}. Previous telemetry was not replaced.') from None
        except (URLError, TimeoutError):
            if attempt == 2:
                raise RuntimeError('GitHub request timed out or could not connect. Previous telemetry was not replaced.') from None
        time.sleep(attempt + 1)


class CalendarParser(HTMLParser):
    """Public GitHub calendar fallback for local runs without an API token."""
    def __init__(self):
        super().__init__()
        self.cells, self.counts = {}, {}
        self.tip, self.text = None, ''

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
            raise RuntimeError('GitHub calendar format changed. Previous telemetry was not replaced.')
        return [{'date': d, 'level': level, 'count': self.counts[k]} for k, (d, level) in self.cells.items()]


def get_calendar(username, now):
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if token:
        query = '''query($login:String!, $from:DateTime!, $to:DateTime!) {
          user(login:$login) { contributionsCollection(from:$from,to:$to) {
            contributionCalendar { weeks { contributionDays { date contributionCount contributionLevel } } }
          } }
        }'''
        start = datetime.combine(now.date() - timedelta(days=364), datetime.min.time(), tzinfo=timezone.utc)
        try:
            data = request(API + '/graphql', {'query': query, 'variables': {'login': username, 'from': start.isoformat(), 'to': now.isoformat()}})
            if data.get('errors'):
                raise RuntimeError('GraphQL returned an error')
            weeks = data['data']['user']['contributionsCollection']['contributionCalendar']['weeks']
            levels = {'NONE': 0, 'FIRST_QUARTILE': 1, 'SECOND_QUARTILE': 2, 'THIRD_QUARTILE': 3, 'FOURTH_QUARTILE': 4}
            days = [{'date': d['date'], 'level': levels[d['contributionLevel']], 'count': d['contributionCount']} for w in weeks for d in w['contributionDays']]
            return days, 'GitHub GraphQL API'
        except (RuntimeError, KeyError, TypeError):
            print('::warning::Contribution API unavailable; using the live public GitHub calendar instead.')
    parser = CalendarParser()
    parser.feed(request(f'https://github.com/users/{username}/contributions', api=False))
    return parser.days(), 'GitHub public contribution calendar'


def summarize(user, repos, days, now, source):
    today = now.date()
    window = {d['date']: d for d in days if today - timedelta(days=364) <= date.fromisoformat(d['date']) <= today}
    ordered = [window.get((today - timedelta(days=364-i)).isoformat()) for i in range(365)]
    if any(d is None for d in ordered):
        raise RuntimeError('Incomplete contribution calendar. Previous telemetry was not replaced.')
    if any(not isinstance(d['count'], int) or d['count'] < 0 or not 0 <= d['level'] <= 4 for d in ordered):
        raise RuntimeError('Invalid contribution data.')
    repos = [r for r in repos if not r.get('private', False)]
    original = [r for r in repos if not r['fork']]
    languages = Counter(r['language'] for r in original if r.get('language'))
    profile_repo = user['login'].lower()
    recent = sorted((r for r in original if r.get('name') and r['name'].lower() != profile_repo),
                    key=lambda r: r.get('pushed_at') or '', reverse=True)[:5]
    recent_repositories = [{'name': r['name'], 'url': r.get('html_url') or f"https://github.com/{user['login']}/{r['name']}",
                            'description': r.get('description') or '', 'language': r.get('language') or '',
                            'stars': r.get('stargazers_count', 0), 'pushed_at': (r.get('pushed_at') or '')[:10]}
                           for r in recent]
    best = run = 0
    for d in ordered:
        run = run + 1 if d['count'] else 0
        best = max(best, run)
    reverse = ordered[::-1]
    if reverse[0]['count'] == 0:
        reverse = reverse[1:]  # Today is unfinished in UTC.
    current = 0
    for d in reverse:
        if not d['count']:
            break
        current += 1
    return {
        'username': user['login'], 'fetched_at': now.isoformat(),
        'sources': {'profile_and_repositories': 'GitHub REST API', 'contributions': source},
        'window': {'from': ordered[0]['date'], 'to': ordered[-1]['date'], 'timezone': 'UTC'},
        'metrics': {'contributions': sum(d['count'] for d in ordered), 'current_streak_days': current,
                    'best_streak_days': best, 'public_repositories': user['public_repos'],
                    'original_repositories': len(original), 'forked_repositories': len(repos)-len(original),
                    'stars_on_original_repositories': sum(r['stargazers_count'] for r in original),
                    'followers': user['followers'], 'active_days': sum(bool(d['count']) for d in ordered)},
        'languages_by_primary_repository_count': dict(languages.most_common()),
        'recent_repositories': recent_repositories, 'calendar': ordered,
    }


def markdown(data):
    m, u = data['metrics'], data['username']
    stamp = datetime.fromisoformat(data['fetched_at']).strftime('%Y-%m-%d %H:%M UTC')
    def days(n): return f'{n}-day'
    lines = [START, '', '<div align="center">', '',
        f"### ⚡ {m['contributions']:,} contributions &nbsp; · &nbsp; {days(m['current_streak_days'])} streak &nbsp; · &nbsp; {days(m['best_streak_days'])} best", '',
        f"**{m['public_repositories']} repositories** &nbsp; / &nbsp; **{m['stars_on_original_repositories']} stars** &nbsp; / &nbsp; **{m['followers']} followers**", '',
        '<br />', '', '**CONTRIBUTION SIGNAL**', '',
        '<img src="./assets/analytics.svg" width="100%" alt="Animated circuit scanner with actual weekly contribution totals above a daily contribution calendar. The scanner is decorative; the data is fetched from GitHub." />', '',
        f"<sub>{data['window']['from']} → {data['window']['to']} · {m['active_days']} active days · {m['original_repositories']} original repos · {m['forked_repositories']} forks</sub>", '',
        '<br /><br />', '', '**LANGUAGE FREQUENCIES**', '',
        '<img src="./assets/language-signal.svg" width="100%" alt="Animated segmented language signal. Segment widths show the share of repositories by primary language." />', '']
    langs = data['languages_by_primary_repository_count']
    total = sum(langs.values())
    symbols = ['🔵', '🟣', '🟢', '🟠', '🩷']
    legend = []
    for i, (name, count) in enumerate(langs.items()):
        name = escape(name)
        legend.append(f"{symbols[i%len(symbols)]} **{name} {count/total:.0%}** · {count} {'repo' if count == 1 else 'repos'}")
    lines += [' &nbsp; / &nbsp; '.join(legend) if total else 'No detected languages', '']
    recent = data.get('recent_repositories') or []
    if recent:
        def cell(text, limit=80):
            text = ' '.join(str(text).split())
            text = text if len(text) <= limit else text[:limit-1].rstrip() + '…'
            return escape(text).replace('|', '&#124;')
        lines += ['<br /><br />', '', '**RECENTLY ACTIVE REPOSITORIES**', '',
                  '| Repository | About | Language | ★ | Last push |', '| --- | --- | --- | ---: | --- |']
        for r in recent:
            lines.append(f"| [{cell(r['name'], 40)}]({r['url']}) | {cell(r['description']) or '—'} | {cell(r['language']) or '—'} | {int(r['stars'])} | {cell(r['pushed_at']) or '—'} |")
        lines.append('')
    lines += ['<br /><br />', '', f'<sub>Fetched from GitHub · {stamp} · Hourly refresh</sub>', '', '</div>', '',
        '<details>', '<summary><sub>Signal definitions, sources & refresh</sub></summary>', '',
        'The upper signal plots actual weekly contribution totals; the matrix below shows daily contributions. Moving scanners, orbiting particles and glowing traces are decoration, not additional measurements.', '',
        'Contributions and best streak cover the last 365 UTC dates. An unfinished day with no contributions does not break yesterday’s streak. GitHub may include anonymized private activity if enabled on your profile.', '',
        'Stars are received stars on owned non-fork public repositories. Language widths count primary languages of owned non-fork public repositories, not time spent or code bytes. Legend order matches segments from left to right. The repository table lists your five most recently pushed original public repositories (this profile repository excluded).', '',
        f"Sources: GitHub REST API + {data['sources']['contributions']}. Timestamped hourly snapshots; no fetch runs on profile visits.", '',
        f'[Inspect fetched data](./assets/telemetry.json) · [Run refresh](https://github.com/{u}/{u}/actions/workflows/profile-analytics.yml)', '', '</details>', '', END]
    return '\n'.join(lines)


def svg_start(height):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{height}" viewBox="0 0 1000 {height}" fill="none">',
        '<defs><linearGradient id="signal"><stop stop-color="#22D3EE"/><stop offset=".55" stop-color="#A78BFA"/><stop offset="1" stop-color="#F472B6"/></linearGradient><linearGradient id="fill" x1="0%" y1="0%" x2="0%" y2="100%"><stop stop-color="#22D3EE" stop-opacity=".16"/><stop offset="1" stop-color="#22D3EE" stop-opacity="0"/></linearGradient><linearGradient id="scan"><stop stop-color="#67E8F9" stop-opacity="0"/><stop offset="1" stop-color="#67E8F9" stop-opacity=".22"/></linearGradient><filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="3"/></filter></defs>',
        '<style>@media(prefers-reduced-motion:reduce){.motion{display:none}}</style>']


def calendar_svg(data):
    import math
    days = data['calendar']
    start = date.fromisoformat(days[0]['date'])
    start -= timedelta(days=(start.weekday()+1) % 7)
    weekly = {}
    for d in days:
        index = (date.fromisoformat(d['date'])-start).days
        col, row = divmod(index, 7)
        weekly[col] = weekly.get(col, 0) + d['count']
    peak = max(weekly.values()) or 1
    points = [(210+i*750/max(1,len(weekly)-1), 124-n*95/peak) for i,n in enumerate(weekly.values())]
    path = 'M'+' L'.join(f'{x:.2f} {y:.2f}' for x,y in points)
    parts = svg_start(350)
    parts += ['<path d="M24 157H976" stroke="#263849"/>',
        '<path d="M24 13H135L152 30M865 13H976" stroke="#263849"/>']
    for y in [31,62,93,124]:parts.append(f'<path d="M210 {y}H960" stroke="#1D2C3B" stroke-dasharray="2 8"/>')
    parts += [f'<path d="{path} L960 140H210Z" fill="url(#fill)"/>',
              f'<path d="{path}" stroke="url(#signal)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
              f'<path d="{path}" stroke="#67E8F9" stroke-width="4" filter="url(#glow)" opacity=".18"/>',
              f'<circle class="motion" r="3" fill="#E5F6FF"><animateMotion path="{path}" dur="12s" repeatCount="indefinite"/></circle>']
    # Orbit and moving signal links are decorative; no changing text is baked in.
    parts += ['<circle cx="89" cy="79" r="48" stroke="#263849"/>',
              '<circle cx="89" cy="79" r="33" stroke="#22D3EE" opacity=".3"/>',
              '<circle class="motion" cx="89" cy="79" r="48" stroke="#A78BFA" stroke-width="2" stroke-dasharray="45 106"><animateTransform attributeName="transform" type="rotate" values="0 89 79;360 89 79" dur="14s" repeatCount="indefinite"/></circle>',
              '<path d="M54 79H70L78 63L90 96L102 70L110 79H126" stroke="#67E8F9" stroke-width="2"/>',
              '<path d="M138 79H162L185 124H210" stroke="#345269"/>',
              '<circle class="motion" r="2.5" fill="#67E8F9"><animateMotion path="M138 79H162L185 124H210" dur="3s" repeatCount="indefinite"/></circle>']
    colors = ['#152337','#154A59','#16899B','#23BFCC','#82F5E3']
    lastx = 0
    for d in days:
        index = (date.fromisoformat(d['date'])-start).days
        col,row = divmod(index,7)
        x=28+col*18;lastx=max(lastx,x)
        parts.append(f'<rect x="{x}" y="{184+row*18}" width="13" height="13" rx="2" fill="{colors[d["level"]]}"/>')
    parts += [f'<clipPath id="matrix"><rect x="24" y="176" width="{lastx+20-24}" height="139"/></clipPath>',
              '<g clip-path="url(#matrix)"><rect class="motion" x="-70" y="177" width="70" height="138" fill="url(#scan)"><animate attributeName="x" values="-70;1000" dur="10s" repeatCount="indefinite"/></rect></g>',
              '<path d="M24 334H420L434 324H566L580 334H976" stroke="#263849"/>',
              '<path class="motion" d="M24 334H420L434 324H566L580 334H976" stroke="url(#signal)" pathLength="1" stroke-dasharray=".06 .94"><animate attributeName="stroke-dashoffset" values="1;0" dur="8s" repeatCount="indefinite"/></path>', '</svg>']
    return '\n'.join(parts)


def language_svg(data):
    langs = data['languages_by_primary_repository_count']
    total = sum(langs.values())
    parts = svg_start(86)
    parts += ['<path d="M24 20H976M24 66H976" stroke="#223344"/>']
    palette = ['#22D3EE','#A78BFA','#A3E635','#FBBF24','#F472B6']
    x=24
    for i,(name,count) in enumerate(langs.items()):
        width=952*count/total
        parts += [f'<rect x="{x:.2f}" y="33" width="{width:.2f}" height="16" fill="{palette[i%5]}" opacity=".8"/>',
                  f'<path d="M{x:.2f} 56H{x+width:.2f}" stroke="{palette[i%5]}" opacity=".2"/>']
        if i:parts.append(f'<path d="M{x:.2f} 33V49" stroke="#0D1117" stroke-width="3"/>')
        x+=width
    if not total:parts.append('<path d="M24 41H976" stroke="#263849" stroke-dasharray="3 8"/>')
    parts += ['<rect class="motion" x="-60" y="33" width="60" height="16" fill="url(#scan)"><animate attributeName="x" values="-60;1000" dur="6s" repeatCount="indefinite"/></rect>',
              '<circle class="motion" cy="66" r="2" fill="#67E8F9"><animate attributeName="cx" values="24;976" dur="6s" repeatCount="indefinite"/></circle>', '</svg>']
    return '\n'.join(parts)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--username', default=os.environ.get('PROFILE_USERNAME') or os.environ.get('GITHUB_REPOSITORY_OWNER') or 'AshuNewatia')
    args = p.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?', args.username):
        p.error('Invalid GitHub username')
    readme_path = ROOT/'README.md'
    readme = readme_path.read_text(encoding='utf-8')
    if readme.count(START) != 1 or readme.count(END) != 1 or readme.index(START) > readme.index(END):
        raise RuntimeError('Expected one valid telemetry marker pair in README.md')
    user = request(f'{API}/users/{args.username}')
    repos, page = [], 1
    while True:
        batch = request(f'{API}/users/{args.username}/repos?type=owner&per_page=100&page={page}')
        if not isinstance(batch, list):
            raise RuntimeError('Invalid GitHub repository response')
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    days, source = get_calendar(args.username, datetime.now(timezone.utc))
    now = datetime.now(timezone.utc)
    data = summarize(user, repos, days, now, source)
    before, tail = readme.split(START, 1)
    _, after = tail.split(END, 1)
    updated = before + markdown(data) + after
    # Fetches, validation and rendering all succeed before any output is replaced.
    outputs = {ROOT/'assets/analytics.svg': calendar_svg(data), ROOT/'assets/language-signal.svg': language_svg(data), ROOT/'assets/telemetry.json': json.dumps(data, indent=2)+'\n', readme_path: updated}
    temps = []
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix+'.tmp')
        tmp.write_text(content, encoding='utf-8')
        temps.append((tmp, path))
    for tmp, path in temps:
        tmp.replace(path)
    print(f'Fetched GitHub telemetry for {user["login"]}; updated README.md, calendar and JSON.')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError, KeyError, TypeError) as error:
        print(f'::error::{error}', file=sys.stderr)
        sys.exit(1)
