#!/usr/bin/env python3
"""Query the git history of domain files in is-a-dev/register."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


DEFAULT_REPOSITORY = "https://github.com/is-a-dev/register.git"
DEFAULT_CACHE = Path(".cache/is-a-dev-register")
DOMAIN_FILE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.-]*$")


class GitError(RuntimeError):
    """Raised when a git command fails."""


def git(cache: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(cache), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise GitError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def sync(cache: Path, repository: str) -> None:
    cache.parent.mkdir(parents=True, exist_ok=True)
    if not (cache / ".git").is_dir():
        subprocess.run(
            ["git", "clone", repository, str(cache)],
            check=True,
            text=True,
        )
        return
    git(cache, "fetch", "--prune", "origin")
    git(cache, "reset", "--hard", "origin/HEAD")


def normalize_domain(value: str) -> str:
    domain = value.strip().lower()
    if domain.startswith("https://"):
        domain = domain[8:]
    elif domain.startswith("http://"):
        domain = domain[7:]
    domain = domain.split("/", 1)[0]
    domain = domain.rstrip(".")
    if not domain or not DOMAIN_FILE.fullmatch(domain):
        raise ValueError(f"invalid domain: {value!r}")
    return domain


def domain_path(domain: str) -> str:
    return f"domains/{normalize_domain(domain)}.json"


def history(cache: Path, domain: str) -> dict[str, Any]:
    path = domain_path(domain)
    commits = git(
        cache,
        "log",
        "--follow",
        "--format=%H%x00%aI%x00%an%x00%ae%x00%s",
        "--",
        path,
    ).splitlines()
    entries = []
    for line in commits:
        commit, authored_at, author, email, subject = line.split("\x00", 4)
        patch = git(cache, "show", "--format=", "--find-renames", commit, "--", path)
        entries.append(
            {
                "commit": commit,
                "authored_at": authored_at,
                "author": author,
                "email": email,
                "subject": subject,
                "patch": patch,
            }
        )
    return {"domain": normalize_domain(domain), "path": path, "commits": entries}


def domain_files(cache: Path) -> list[str]:
    return [
        line
        for line in git(cache, "ls-tree", "-r", "--name-only", "HEAD", "--", "domains")
        .splitlines()
        if line.endswith(".json")
    ]


def export_history(cache: Path, output: Path) -> int:
    records = []
    for path in domain_files(cache):
        records.append(history(cache, Path(path).stem))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    return len(records)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--repository", default=DEFAULT_REPOSITORY)
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync", help="clone or update the full upstream history")
    sync_parser.set_defaults(action="sync")

    query_parser = subparsers.add_parser("history", help="show a domain's commits and patches")
    query_parser.add_argument("domain")
    query_parser.add_argument("--json", action="store_true", dest="as_json")
    query_parser.set_defaults(action="history")

    export_parser = subparsers.add_parser("export", help="write history for every domain file")
    export_parser.add_argument("output", type=Path)
    export_parser.set_defaults(action="export")

    args = parser.parse_args()
    try:
        if args.action == "sync":
            sync(args.cache, args.repository)
            print(f"Repository ready at {args.cache}")
        elif args.action == "history":
            result = history(args.cache, args.domain)
            if args.as_json:
                print(json.dumps(result, indent=2))
            else:
                for commit in result["commits"]:
                    print(f"{commit['commit'][:10]} {commit['authored_at']} {commit['author']}: {commit['subject']}")
                    print(commit["patch"], end="")
        else:
            count = export_history(args.cache, args.output)
            print(f"Wrote {count} domain histories to {args.output}")
    except (GitError, ValueError, FileNotFoundError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
