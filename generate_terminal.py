import json
import re
import xml.etree.ElementTree as ET

from html import escape
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent

START = "<!-- GITHUB-TELEMETRY:START -->"
END = "<!-- GITHUB-TELEMETRY:END -->"


def safe_url(value):
    parsed = urlparse(value)

    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or re.search(r"[\s<>()]", value)
    ):
        raise ValueError("Links must be valid HTTPS URLs")

    return value


def main():
    data_file = ROOT / "data.json"
    template_file = ROOT / "terminal.template.svg"
    readme_path = ROOT / "README.md"

    data = json.loads(
        data_file.read_text(encoding="utf-8")
    )

    roles = data["roles"]

    if len(roles) != 3:
        raise ValueError("Provide exactly three roles in data.json")

    values = {
        "NAME": data["name"],
        "TITLE": data["title"],
        "BIO": data["bio"],
    }

    values.update({
        f"ROLE_{index}": role
        for index, role in enumerate(roles, start=1)
    })

    template = template_file.read_text(encoding="utf-8")

    rendered = re.sub(
        r"{{([A-Z0-9_]+)}}",
        lambda match: escape(
            str(values[match.group(1)]),
            quote=True,
        ),
        template,
    )

    # Check that the generated SVG is valid XML.
    ET.fromstring(rendered)

    (ROOT / "terminal.svg").write_text(
        rendered,
        encoding="utf-8",
    )

    # Keep the most recent GitHub activity snapshot when the rest of
    # the README is regenerated.
    if readme_path.exists():
        old_readme = readme_path.read_text(encoding="utf-8")
    else:
        old_readme = ""

    if (
        old_readme.count(START) == 1
        and old_readme.count(END) == 1
        and old_readme.index(START) < old_readme.index(END)
    ):
        activity = old_readme[
            old_readme.index(START):
            old_readme.index(END) + len(END)
        ]
    else:
        activity = (
            START
            + "\n\n"
            + "*Activity appears after the first successful refresh.*"
            + "\n\n"
            + END
        )

    github = safe_url(data["github"])
    linkedin = safe_url(data["linkedin"])

    def html_text(value):
        return escape(str(value), quote=True)

    project_rows = []

    for index, project in enumerate(data["projects"], start=1):
        name = html_text(project["name"])
        tag = html_text(project["tag"])
        summary = html_text(project["summary"])
        tech = html_text(project["tech"])
        url = safe_url(project["url"])

        project_rows.append(
            f"""
<tr>
  <td>
    <strong>{index:02} / {name}</strong><br />
    <sub>{tag}</sub><br /><br />
    {summary}<br /><br />
    <code>{tech}</code><br /><br />
    <a href="{url}">OPEN REPOSITORY ↗</a>
  </td>
</tr>
""".strip()
        )

    stack_rows = []

    for category, technologies in data["stack"].items():
        category_text = html_text(category)

        technology_text = " · ".join(
            f"`{html_text(item)}`"
            for item in technologies
        )

        stack_rows.append(
            f"| **{category_text}** | {technology_text} |"
        )

    project_table = "\n".join(project_rows)
    stack_table = "\n".join(stack_rows)

    name = html_text(data["name"])
    bio = html_text(data["bio"])

    readme = f"""<p align="center">
  <img
    src="./terminal.svg"
    width="100%"
    alt="{name}: animated cyberpunk terminal with roles and bio"
  />
</p>

<p align="center">
  <strong>
    BUILD SYSTEMS &nbsp; / &nbsp;
    SOLVE PROBLEMS &nbsp; / &nbsp;
    KEEP EXPLORING
  </strong>
</p>

<p align="center">
  <a href="{github}?tab=repositories">[ REPOSITORIES ↗ ]</a>
  &nbsp; ✦ &nbsp;
  <a href="{linkedin}">[ LINKEDIN ↗ ]</a>
</p>

---

## ◈ 01 / SYSTEM PROFILE

{bio} I enjoy connecting collaborative software, campus tools and voice AI with practical problems.

<p align="center">
  <img
    src="./assets/waneella.gif"
    width="300"
    alt="Animated pixel-art workspace"
  />
</p>

## ◈ 02 / FEATURED MISSIONS

<table width="100%">
{project_table}
</table>

## ◈ 03 / THE TOOLKIT

| MODULE | INSTALLED |
| :--- | :--- |
{stack_table}

## ◈ 04 / GITHUB SIGNAL

{activity}

<p align="center">
  <sub>
    Contribution calendar and complete history →
    <a href="{github}#overview">OPEN GITHUB ↗</a>
  </sub>
</p>

---

<p align="center">
  <strong>HAVE AN IDEA? LET’S BUILD IT.</strong>
  <br /><br />
  <a href="{linkedin}">CONNECT ON LINKEDIN ↗</a>
  &nbsp; / &nbsp;
  <a href="{github}?tab=repositories">EXPLORE REPOSITORIES ↗</a>
  <br /><br />
  <sub>END OF TRANSMISSION // {name.upper()}</sub>
</p>
"""

    readme_path.write_text(
        readme,
        encoding="utf-8",
    )

    print("Generated terminal.svg and README.md")


if __name__ == "__main__":
    main()