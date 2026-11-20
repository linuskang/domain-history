# is-a.dev tools

This project is a dependency-free static site for GitHub Pages.

- `index.html` searches commits and file changes for a domain in `is-a-dev/register`.
- `subdomains.html` lists every subdomain registered to a GitHub username or email.

Both pages run entirely in the browser using the GitHub API and the public
`is-a-dev` registry, so no server or build step is needed.