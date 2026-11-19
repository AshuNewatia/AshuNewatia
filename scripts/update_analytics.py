from collections import Counter
from datetime import date, datetime, timedelta, timezone
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import argparse
import json
import os
import re
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import section_art  # noqa: E402

START = "<!-- GITHUB-TELEMETRY:START -->"
END = "<!-- GITHUB-TELEMETRY:END -->"

API = "https://api.github.com"


def request(url, payload=None, api=True):
    headers = {
        "User-Agent": "editable-profile-telemetry",
        "Accept": (
            "application/vnd.github+json"
            if api
            else "text/html"
        ),
    }

    token = (
        os.environ.get("GH_TOKEN")
        or os.environ.get("GITHUB_TOKEN")
    )

    if token and api:
        headers["Authorization"] = "Bearer " + token

    if payload is not None:
        headers["Content-Type"] = "application/json"

    request_data = None

    if payload is not None:
        request_data = json.dumps(payload).encode("utf-8")

    req = Request(
        url,
        data=request_data,
        headers=headers,
    )

    for attempt in range(3):
        try:
            with urlopen(req, timeout=35) as response:
                text = response.read().decode("utf-8")

            return json.loads(text) if api else text

        except HTTPError as error:
            retryable = error.code in (429, 500, 502, 503, 504)

            if not retryable or attempt == 2:
                raise RuntimeError(
                    f"GitHub request failed: HTTP {error.code}. "
                    "Previous telemetry was not replaced."
                ) from None

        except (URLError, TimeoutError):
            if attempt == 2:
                raise RuntimeError(
                    "GitHub request timed out or could not connect. "
                    "Previous telemetry was not replaced."
                ) from None

        time.sleep(attempt + 1)


class CalendarParser(HTMLParser):
    """Fallback parser for GitHub's public contribution calendar."""

    def __init__(self):
        super().__init__()

        self.cells = {}
        self.counts = {}

        self.tip = None
        self.text = ""

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)

        if (
            attributes.get("data-date")
            and attributes.get("data-level") is not None
        ):
            self.cells[attributes["id"]] = (
                attributes["data-date"],
                int(attributes["data-level"]),
            )

        if tag == "tool-tip" and attributes.get("for"):
            self.tip = attributes["for"]
            self.text = ""

    def handle_data(self, text):
        if self.tip:
            self.text += text

    def handle_endtag(self, tag):
        if tag != "tool-tip" or not self.tip:
            return

        match = re.match(
            r"\s*([\d,]+) contributions?\b",
            self.text,
        )

        if match:
            self.counts[self.tip] = int(
                match[1].replace(",", "")
            )

        elif self.text.strip().startswith("No contributions"):
            self.counts[self.tip] = 0

        self.tip = None

    def days(self):
        if not self.cells:
            raise RuntimeError(
                "GitHub calendar data was not found. "
                "Previous telemetry was not replaced."
            )

        if not all(key in self.counts for key in self.cells):
            raise RuntimeError(
                "GitHub calendar format changed. "
                "Previous telemetry was not replaced."
            )

        result = []

        for key, (day, level) in self.cells.items():
            result.append({
                "date": day,
                "level": level,
                "count": self.counts[key],
            })

        return result


def get_calendar(username, now):
    token = (
        os.environ.get("GH_TOKEN")
        or os.environ.get("GITHUB_TOKEN")
    )

    if token:
        query = """
        query($login: String!, $from: DateTime!, $to: DateTime!) {
          user(login: $login) {
            contributionsCollection(from: $from, to: $to) {
              contributionCalendar {
                weeks {
                  contributionDays {
                    date
                    contributionCount
                    contributionLevel
                  }
                }
              }
            }
          }
        }
        """

        start = datetime.combine(
            now.date() - timedelta(days=364),
            datetime.min.time(),
            tzinfo=timezone.utc,
        )

        try:
            response = request(
                API + "/graphql",
                {
                    "query": query,
                    "variables": {
                        "login": username,
                        "from": start.isoformat(),
                        "to": now.isoformat(),
                    },
                },
            )

            if response.get("errors"):
                raise RuntimeError("GraphQL returned an error")

            weeks = (
                response["data"]["user"]
                ["contributionsCollection"]
                ["contributionCalendar"]["weeks"]
            )

            levels = {
                "NONE": 0,
                "FIRST_QUARTILE": 1,
                "SECOND_QUARTILE": 2,
                "THIRD_QUARTILE": 3,
                "FOURTH_QUARTILE": 4,
            }

            days = []

            for week in weeks:
                for day in week["contributionDays"]:
                    days.append({
                        "date": day["date"],
                        "level": levels[day["contributionLevel"]],
                        "count": day["contributionCount"],
                    })

            return days, "GitHub GraphQL API"

        except (RuntimeError, KeyError, TypeError):
            print(
                "::warning::Contribution API unavailable; "
                "using the public GitHub calendar."
            )

    parser = CalendarParser()

    html = request(
        f"https://github.com/users/{username}/contributions",
        api=False,
    )

    parser.feed(html)

    return parser.days(), "GitHub public contribution calendar"


def summarize(user, repositories, days, now, source):
    today = now.date()

    first_day = today - timedelta(days=364)

    window = {
        day["date"]: day
        for day in days
        if first_day <= date.fromisoformat(day["date"]) <= today
    }

    ordered = []

    for index in range(365):
        day = first_day + timedelta(days=index)
        ordered.append(window.get(day.isoformat()))

    if any(day is None for day in ordered):
        raise RuntimeError(
            "Incomplete contribution calendar. "
            "Previous telemetry was not replaced."
        )

    for day in ordered:
        valid_count = (
            isinstance(day["count"], int)
            and day["count"] >= 0
        )

        valid_level = 0 <= day["level"] <= 4

        if not valid_count or not valid_level:
            raise RuntimeError("Invalid contribution data.")

    public_repositories = [
        repository
        for repository in repositories
        if not repository.get("private", False)
    ]

    original_repositories = [
        repository
        for repository in public_repositories
        if not repository["fork"]
    ]

    stars = sum(
        repository["stargazers_count"]
        for repository in original_repositories
    )

    return {
        "username": user["login"],
        "fetched_at": now.isoformat(),
        "contribution_source": source,
        "contributions": sum(day["count"] for day in ordered),
        "active_days": sum(bool(day["count"]) for day in ordered),
        "original_repositories": len(original_repositories),
        "stars": stars,
        "followers": user["followers"],
        "calendar": [
            {"date": day["date"], "count": day["count"], "level": day["level"]}
            for day in ordered
        ],
    }


def markdown(data):
    timestamp = datetime.fromisoformat(
        data["fetched_at"]
    ).strftime("%d %b %Y · %H:%M UTC")

    stars = ""
    alt_stars = ""

    if data["stars"]:
        stars = f' &nbsp; / &nbsp; **{data["stars"]:,}** stars'
        alt_stars = f', {data["stars"]:,} stars'

    username = data["username"]

    alt = (
        f'{data["contributions"]:,} contributions and '
        f'{data["active_days"]:,} active days in the last year, '
        f'{data["original_repositories"]:,} original public repositories'
        f'{alt_stars}, {data["followers"]:,} followers'
    )

    return "\n".join([
        START,
        "",
        '<p align="center">',
        f'  <a href="https://github.com/{username}#overview">',
        f'    <img src="./assets/signal.svg" width="100%" alt="{escape(alt)}" />',
        "  </a>",
        "</p>",
        "",
        '<div align="center">',
        "",
        (
            f'<sub>**{data["contributions"]:,}** contributions · '
            f'**{data["active_days"]:,}** active days · '
            f'**{data["original_repositories"]:,}** '
            f'original public repositories'
            f'{stars} &nbsp; / &nbsp; '
            f'**{data["followers"]:,}** followers · '
            f'last 365 UTC dates · updated {timestamp} · '
            f'{escape(data["contribution_source"])}</sub>'
        ),
        "",
        "</div>",
        "",
        END,
    ])


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--username",
        default=(
            os.environ.get("PROFILE_USERNAME")
            or os.environ.get("GITHUB_REPOSITORY_OWNER")
            or "AshuNewatia"
        ),
    )

    args = parser.parse_args()

    username_pattern = (
        r"[A-Za-z0-9]"
        r"(?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?"
    )

    if not re.fullmatch(username_pattern, args.username):
        parser.error("Invalid GitHub username")

    readme_path = ROOT / "README.md"

    readme = readme_path.read_text(encoding="utf-8")

    valid_markers = (
        readme.count(START) == 1
        and readme.count(END) == 1
        and readme.index(START) < readme.index(END)
    )

    if not valid_markers:
        raise RuntimeError(
            "Expected one valid telemetry marker pair in README.md"
        )

    user = request(f"{API}/users/{args.username}")

    repositories = []
    page = 1

    while True:
        batch = request(
            f"{API}/users/{args.username}/repos"
            f"?type=owner&per_page=100&page={page}"
        )

        if not isinstance(batch, list):
            raise RuntimeError("Invalid GitHub repository response")

        repositories.extend(batch)

        if len(batch) < 100:
            break

        page += 1

    now = datetime.now(timezone.utc)

    days, source = get_calendar(args.username, now)

    data = summarize(
        user,
        repositories,
        days,
        now,
        source,
    )

    before, tail = readme.split(START, 1)
    _, after = tail.split(END, 1)

    updated = before + markdown(data) + after

    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    (assets / "signal.svg").write_text(
        section_art.signal_svg(data),
        encoding="utf-8",
    )

    # Replace the README only after fetching and validation succeed.
    temporary_file = readme_path.with_suffix(".md.tmp")

    temporary_file.write_text(
        updated,
        encoding="utf-8",
    )

    temporary_file.replace(readme_path)

    print(
        f"Fetched GitHub telemetry for {user['login']}; "
        "updated README.md."
    )


if __name__ == "__main__":
    try:
        main()

    except (RuntimeError, ValueError, KeyError, TypeError) as error:
        print(f"::error::{error}", file=sys.stderr)
        sys.exit(1)