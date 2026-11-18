# Profile setup

1. Copy the contents of this folder, including `.github`, into the root of your `AshuNewatia/AshuNewatia` repository. Commit and push.
2. In GitHub **Settings → Actions → General → Workflow permissions**, allow read and write permissions if the activity workflow cannot commit. On the Actions tab, run **Refresh profile activity** manually for the first snapshot. The job also runs hourly. Failed fetches leave the previous snapshot untouched.
3. Review the project repository links in `README.md`, add exact campus project and live demo links, screenshots or GIFs, and verified outcomes when available. Replace the LinkedIn contact or add an email if desired. Pin your selected repositories on your GitHub profile.
4. Add descriptions and READMEs in each project repository separately. Archive or delete a repository only after reviewing it in GitHub settings. These external repositories cannot be changed by copying this profile ZIP.

## Files
- `README.md`: profile, typing animation, project links, and activity markers. The activity block is replaced by the workflow; edit the rest freely.
- `assets/avatar.gif`: optimized animated artwork.
- `scripts/update_analytics.py`: fetches and validates GitHub data, then updates the marked activity block.
- `tests/test_telemetry.py`: calculation and rendering tests.
- `.github/workflows/profile-analytics.yml`: scheduled activity refresh.
- `.github/workflows/tests.yml`: tests on pushes and pull requests.

If copying over an older version, delete the old unused files: `assets/analytics.svg`, `assets/circuit.svg`, `assets/header.svg`, `assets/hero.svg`, `assets/language-signal.svg`, `assets/telemetry.json`, `assets/waneella.gif`, and `scripts/generate_art.py`. Copying files alone does not delete old files from Git.

The activity counts cover the last 365 UTC dates. Repositories are public and exclude forks. Stars count stars on those original public repositories and are hidden when zero. The activity snapshot comes from GitHub GraphQL or the public contribution calendar fallback; private activity visibility depends on GitHub's settings and token access. Typing animation and technology icons use external services.
