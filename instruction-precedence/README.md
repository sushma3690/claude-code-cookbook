# Instruction precedence: memory vs `CLAUDE.md`

Claude Code reads a few different places looking for instructions at the start of every session. The two most common sources are the memory system under `~/.claude/projects/` and the `CLAUDE.md` file inside a repo. When they look like they are telling Claude different things, which one wins?

Short honest answer: there is no documented precedence table. Both are text input. In practice, Claude weighs them against each other using the heuristics below, and when a conflict is genuinely unresolvable it is supposed to stop and ask you.

## What each file is actually for

| File | Lives | Scope | Owner | Good for |
| --- | --- | --- | --- | --- |
| `CLAUDE.md` | Inside the repo, checked in | Anyone who clones the repo | The project | Build commands, formatter, architecture notes, folders to avoid, directly repo-specific conventions |
| `~/.claude/projects/<encoded-cwd>/memory/*.md` with `MEMORY.md` index | On your laptop only | You, in that one project | You | Your preferences, how you want Claude to talk to you, what Claude is allowed to do without re-asking, personal safety rails |

Most of the time these two files are speaking about different things and never collide. `CLAUDE.md` says "run `pnpm test`", memory says "I am new to this stack, explain the test runner the first time it shows up." Both apply, no overlap.

## When they *do* look like they conflict

Two heuristics, in order:

### 1. More specific wins

A rule that applies to the exact thing you are doing right now beats a rule that applies more broadly.

- `CLAUDE.md` says "indent with 2 spaces." Your memory says "I prefer 4 spaces." In this repo, 2 wins. The project knows its own conventions better than your global preference.
- Your memory says "ask before running destructive bash." `CLAUDE.md` says "feel free to use `rm` on anything under `/tmp/build-cache`." When touching `/tmp/build-cache`, the project's narrower allowance applies and Claude proceeds; everywhere else, your broader safety rule still holds.

### 2. The safety rail you own wins

If one of the rules is a personal safety rail you set, treat it as stronger than any project convention.

- Your memory says "never push to any remote without my say-so." A `CLAUDE.md` says "always auto-push after a successful test run." Your rule wins. Nothing a repo asserts should quietly override something you set up to protect yourself.
- Your memory says "no new dependencies without discussing first." `CLAUDE.md` says "install any missing package automatically." Your rule wins, for the same reason.

A project rule should never be the thing that silently talks your personal rule out of applying. If Claude ever does that, call it out and tell it to update the stale one.

## When the two really do fight

Not every conflict fits the two heuristics above. If a rule is both equally specific and not a safety rail (just a style preference versus a project convention, say), there is no reliable rank. The right behavior is for Claude to pause, surface the conflict, and ask you which one applies in this situation. One short exchange, then the choice can be written back into whichever file was less clear.

If you notice Claude silently picking one over the other without asking, that is a sign the rule it followed is too broadly worded or the other rule is phrased too softly to be taken as binding. Tighten whichever one was intended to be the stronger signal.

## Practical setup

Put rules in the lane that fits their nature:

- **In `CLAUDE.md`** (committed to the repo):
  - Build, test, lint commands.
  - Project structure and folders to avoid.
  - Known footguns ("the migration script is destructive, do not run without approval").
  - Team conventions (naming, formatting, commit style).
- **In your `memory/`** (your laptop only):
  - How you want to be talked to (ELI5, deep technical, short, verbose).
  - Standing permissions ("may update `user.name` in my own repos", "may push to my own fork").
  - Standing refusals ("never open a PR for me", "always ask before `git push --force`").
  - Context about who you are and what you are learning.

Kept in those lanes, the "which wins" question almost never comes up. When it does, the two heuristics above handle most cases, and asking handles the rest.

## Related

- The [`git-config-override/`](../git-config-override/) recipe is a worked example of putting a *permission* (one of the "standing permissions" above) into a project-scoped memory. It is the shape most "may Claude do X without asking?" rules take.
- The `init` skill (built into Claude Code) scaffolds a reasonable `CLAUDE.md` for a repo you own. Run it once per repo and then edit what it generated.
