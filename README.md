# claude-code-cookbook

A small, growing collection of hooks, settings, and workflow patterns I have found useful while working with [Claude Code](https://claude.com/claude-code). Each recipe lives in its own folder with a short README that explains what it does, why it exists, and how to install it.

The goal is not to redocument the official product. The goal is to capture the little pieces of plumbing that are easy to miss on a first read and worth sharing once they are working.

## Recipes

| Recipe | What it does |
| --- | --- |
| [`session-end-hook/`](./session-end-hook/) | Saves a readable markdown transcript of every Claude Code session, one file per calendar date, automatically when the session ends. |
| [`git-config-override/`](./git-config-override/) | Explains the default "never update git config" safety rule and three ways to selectively let Claude update your identity when you want it to. |
| [`instruction-precedence/`](./instruction-precedence/) | How Claude Code weighs `memory/` files against a repo's `CLAUDE.md` when they look like they conflict, and how to keep rules in the right lane so the question rarely comes up. |
| [`auto-memory/`](./auto-memory/) | What Claude Code's built-in memory system is, the four note types, the file and index format, when it writes and reads, and the explicit list of what to leave out so memory never goes stale. |

More recipes will be added as I pick up new patterns.

## How to use this repo

Every recipe is self-contained. Open the folder, read the README, drop the files where it tells you to, and (if the recipe is a hook) register it in `~/.claude/settings.json`. There is nothing to install at the repo level.

## Conventions

- Each recipe folder has a `README.md` that explains what, why, and how.
- Scripts are commented so a first-time reader can understand them without jumping to external docs.
- Nothing phones home. Every recipe runs locally and reads or writes only files on your own machine.

## License

MIT. Use, copy, adapt, and share freely.
