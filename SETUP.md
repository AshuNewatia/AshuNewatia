# Editable GitHub profile

All manually maintained profile content is now in README.md. The SVG designs contain decorative shapes and motion only. The analytics SVG is the one content-bearing SVG: it is automatically regenerated from live GitHub data by the existing daily workflow.

## Install

1. Extract the ZIP.
2. Copy README.md and assets/ from the extracted folder into the root of your AshuNewatia/AshuNewatia repository.
3. Commit the files. The ZIP includes the existing analytics script and .github workflow for completeness; those files are unchanged.
4. The existing workflow continues refreshing assets/analytics.svg. No new workflow or dependency is needed.

Do not upload the ZIP itself. Keep the repository public and README.md at the root.

## Where to edit

| Content | Edit in README.md |
| --- | --- |
| Name and tagline | Intro section directly under the banner |
| Education and development interests | Intro and Developer signal |
| Technology stack | Plain-text lists; optionally update the accompanying icon URL |
| Project names and descriptions | Each details block under Connected builds |
| Project technology tags | Technologies line in that project block |
| Repository and demo links | Markdown links in the relevant project block |
| Future goals | Build, Explore and Improve blockquotes |
| Personal interests | Personal.log details block |
| Social links and footer | Last section |

The decorative SVGs have no names, labels, descriptions, tags or goals inside them. Add a project by copying a details block and editing its summary, description, technologies and link. Remove the open attribute if you want CampusFlow collapsed initially. Artwork is symbolic, so changing the number of project entries does not require regenerating it.

## Changes from your uploaded ZIP

Changed:
- README.md: all handwritten content is native Markdown/HTML text, with commented edit points.
- SETUP.md: updated editing and installation instructions.

Added, all text-free:
- assets/identity-circuit.svg: pulsing processor and incoming circuit traces.
- assets/project-circuit.svg: satellite network with animated signals.
- assets/outbound-circuit.svg: outward-flowing circuit branches.

Removed from this ZIP, safe to delete from your repository after replacing README.md:
- assets/identity-motion.gif
- assets/projects-motion.gif
- assets/directives-motion.gif

Preserved unchanged:
- assets/waneella.gif (your uploaded banner)
- assets/circuit.svg
- assets/analytics.svg (current snapshot)
- scripts/update_analytics.py
- .github/workflows/profile-analytics.yml

## GitHub rendering

GitHub does not allow arbitrary CSS positioning or JavaScript inside READMEs. Editable text therefore sits above or below the SVG artwork rather than being overlaid on it. Project descriptions expand using GitHub's native details/summary support. Native README text uses GitHub's fonts; custom text rendered inside an SVG would defeat the purpose of this update.

The tech icons are external decorative widgets from skillicons.dev; their technology names are also written as ordinary text. The banner bytes were retained from your upload. This package does not establish its original authorship or license.

## Automatic analytics

The chart is intentionally separate from handwritten copy. Its public repository counts, contribution calendar, streaks, follower count and language shares refresh through the existing workflow. To change its account or visual layout, edit scripts/update_analytics.py. To change the schedule, edit .github/workflows/profile-analytics.yml.

The displayed language distribution counts primary languages of owned non-fork public repositories; it is not a skill rating or a measure of time spent. The snapshot timestamp is inside the chart. If GitHub changes its public calendar markup or requests fail, the last successful chart remains until a later successful run.
