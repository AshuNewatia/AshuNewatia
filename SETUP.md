# Set up your GitHub profile

1. Open https://github.com/AshuNewatia/AshuNewatia.
2. Extract the ZIP. Copy the CONTENTS of the extracted folder into your repository root, preserving these paths:

   - README.md
   - assets/ (all five images)
   - scripts/update_analytics.py
   - .github/workflows/profile-analytics.yml

   Do not upload the ZIP itself or nest these files inside a profile-tech folder. Keep the repository public. SETUP.md is optional.

3. Commit and push to your default branch. Include the hidden .github folder. If using VS Code, open the extracted folder and copy .github explicitly. On Windows, File Explorer can show it as an ordinary folder.
4. The included chart already contains a real initial public-data snapshot. Once the workflow is present, open Actions → Refresh profile analytics → Run workflow. The same workflow runs daily at 02:23 UTC (07:53 India time).

No personal access token or API key is needed. The workflow uses GitHub's automatically provided repository token. It requests contents: write to commit only assets/analytics.svg. If repository or organization policy blocks the bot push, enable the necessary write permission or use a branch/PR workflow appropriate to that policy. A protected default branch may reject the automatic commit.

## What's included

- Original cyberpunk workstation banner with custom futuristic lettering.
- Orbitron animated typing line, terminal identity card with blinking cursor, animated circuit dividers.
- Custom analytics panel: public contributions for the displayed rolling year, current and longest streak, public repositories, stars on owned non-fork repositories, followers, primary-language shares and active days.
- An animated scanner over the actual contribution calendar. The scanner is decorative; the cells represent real GitHub data. It is not a contribution snake.
- Visual project cards and technology icons.

GitHub strips arbitrary CSS and JavaScript from profile READMEs. The futuristic lettering is rendered into images/SVGs; the live typing line uses an external SVG service. The banner's campus scene is an illustration.

## Analytics definitions

- Calendar: GitHub's public contribution calendar, clipped to the latest 365 UTC dates available. Private repository details are not accessed.
- Current streak: consecutive days with at least one contribution. An unfinished UTC day with zero contributions does not break yesterday's streak.
- Best streak: longest run within the displayed calendar, not an all-time record.
- Languages: count of owned, non-fork PUBLIC repositories grouped by their primary GitHub language. This is not lines of code, bytes, time spent, or a skill rating. Repositories with no detected language are excluded.
- Public repository count includes forks. Original repository and fork counts are also shown separately.
- Stars: stars received on owned non-fork public repositories.

The script uses the public REST API plus GitHub's public calendar HTML. If GitHub changes its calendar markup or an API request fails, the workflow fails and retains the last successful chart. The timestamp inside the chart makes staleness visible. GitHub may disable scheduled workflows in inactive public repositories; re-enable under Actions if necessary.

## Customization

- Edit README.md for your links, interests and toolkit icons.
- Images are linked using relative paths. Always upload assets with README.md.
- For project-card text, edit or replace assets/projects.svg. The descriptions reflect projects discussed in this conversation; review before publishing.
- For analytics colors/layout, edit scripts/update_analytics.py. It has no third-party Python dependencies.
- Optional external services: readme-typing-svg.demolab.com, shields.io, skillicons.dev. The main banner, charts and project cards are stored locally in your repository, so those stay available if an external widget fails.

## Visual asset provenance

The banner was created with the built-in image generator using this brief: an original premium cyberpunk developer workstation overlooking an illustrated IIT Indore campus at night, cyan/violet palette, wide layout, exact ASHU NEWATIA lettering, BUILD. EXPERIMENT. ITERATE. tagline, full-stack/voice-AI identity. Other interface assets are editable SVGs.
