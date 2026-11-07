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
        'languages_by_primary_repository_count': dict(languages.most_common()), 'calendar': ordered,
    }


def markdown(data):
    m, u = data['metrics'], data['username']
    stamp = datetime.fromisoformat(data['fetched_at']).strftime('%Y-%m-%d %H:%M UTC')
    lines = [START, '', f'**GitHub data for [{u}](https://github.com/{u})** · Last fetched: **{stamp}**', '',
        '| Contributions¹ | Current streak² | Best streak¹ | Public repos | Stars³ | Followers |',
        '| ---: | ---: | ---: | ---: | ---: | ---: |',
        f"| {m['contributions']:,} | {m['current_streak_days']} days | {m['best_streak_days']} days | {m['public_repositories']} | {m['stars_on_original_repositories']} | {m['followers']} |", '',
        '<img src="./assets/analytics.svg" width="100%" alt="Automatically fetched GitHub contribution calendar; brighter cells indicate more activity" />', '',
        f"**Activity window:** {data['window']['from']} → {data['window']['to']} · **Active days:** {m['active_days']} · **Original repositories:** {m['original_repositories']} · **Forks:** {m['forked_repositories']}", '',
        '**Language distribution** — primary language of owned, non-fork public repositories.', '',
        '| Language | Repositories | Share |', '| --- | ---: | ---: |']
    langs = data['languages_by_primary_repository_count']
    total = sum(langs.values())
    for name, count in langs.items():
        name = name.replace('|', '\\|').replace('\n', ' ')
        lines.append(f'| {name} | {count} | {count/total:.1%} |')
    if not total:
        lines.append('| No detected languages | 0 | — |')
    lines += ['', '¹ Last 365 UTC dates. Contributions follow GitHub’s profile calendar, which may include anonymized private activity if you have enabled it.',
              '² An unfinished UTC day with no contributions does not break yesterday’s streak.',
              '³ Stars received on owned, non-fork public repositories.', '',
              f"Sources: GitHub REST API + {data['sources']['contributions']}. Refreshes hourly via GitHub Actions; this is a timestamped snapshot, not a request on every profile visit.", '',
              f'[Inspect fetched data](./assets/telemetry.json) · [Refresh workflow](https://github.com/{u}/{u}/actions/workflows/profile-analytics.yml)', '', END]
    return '\n'.join(lines)


def calendar_svg(data):
    days = data['calendar']
    start = date.fromisoformat(days[0]['date'])
    start -= timedelta(days=(start.weekday()+1) % 7)
    colors = ['#162536', '#14515D', '#168396', '#20B7CA', '#67E8F9']
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="162" viewBox="0 0 1000 162" fill="none">', '<path d="M20 12H980" stroke="#253B4C"/>']
    for d in days:
        index = (date.fromisoformat(d['date'])-start).days
        col, row = divmod(index, 7)
        parts.append(f'<rect x="{22+col*18}" y="{25+row*16}" width="14" height="12" rx="2" fill="{colors[d["level"]]}"/>')
    parts += ['<path d="M20 150H980" stroke="#253B4C"/>', '</svg>']
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
    outputs = {ROOT/'assets/analytics.svg': calendar_svg(data), ROOT/'assets/telemetry.json': json.dumps(data, indent=2)+'\n', readme_path: updated}
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
