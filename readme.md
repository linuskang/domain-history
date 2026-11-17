# DNS history for is-a.dev

This project keeps a local, full-history clone of
[`is-a-dev/register`](https://github.com/is-a-dev/register) and lets you query
the commits and exact file changes for a domain.

`index.html` is a dependency-free static site and can be deployed directly to
GitHub Pages. It uses the GitHub API from the browser, so no server is needed.

## Usage

```sh
# Pull the complete upstream history (first run clones; later runs fetches).
python3 domain_history.py sync

# Query one domain. The domain may include http(s)://, `.is-a.dev`, and a trailing dot.
python3 domain_history.py history example.is-a.dev --json

# Export histories for every domains/*.json file.
python3 domain_history.py export data/domain-history.json
```

The cache defaults to `.cache/is-a-dev-register`; use `--cache PATH` to choose
another location. Queries include the primary record and related records such
as `_discord.example.json` or `links.example.json`. `history --json` returns
those files and, for each file, every commit's SHA, author, timestamp, subject,
and complete git patch.
