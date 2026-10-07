# Git config safety override

A short note on a safety rule inside Claude Code that trips up a lot of first-time users, plus three ways to let Claude update your git config when you actually do want it to.

## The rule

Claude Code ships with a built-in git safety protocol. One of the clauses is simply:

> Never update the git config.

That is deliberate. `git config` controls who commits appear to come from (`user.name`, `user.email`), what signing key is used, how pulls behave, and more. A silent change to any of those during an agent session is the kind of thing you want to prevent by default.

In practice the rule shows up like this: the first time you ask Claude Code to commit on a machine that does not yet have `user.name` set, the commit will fail and Claude will stop and ask you to run `git config` yourself.

## When this is the correct behavior

- You are on a shared machine and your personal identity should never be set by an agent.
- You have multiple identities for work and personal and never want them crossed.
- You are testing a sandboxed workflow and want full control over what Claude is allowed to touch.

If any of those apply, leave the rule in place and just run `git config` yourself when prompted. That is the end of the recipe.

## When you want Claude to just handle it

If you are the only user on your machine and you are happy for Claude to set your identity once and move on, there are three ways to tell it so, from most ephemeral to most persistent.

### 1. Per-session instruction

The simplest and lowest commitment option. Just say so in the session:

```
set git user.name globally and push
```

That one message overrides the rule for that specific action, in that specific session. Nothing persists. Next session, same rule applies.

Use this when the ask is a one-off (first-time setup on a new machine, correcting a typo in your email, bootstrapping a repo for a demo).

### 2. Personal memory

If you expect to make the same override call again and again, record it as a memory. Claude Code reads your memory at the start of every session.

A memory for this looks like:

```markdown
---
name: feedback-git-config
description: Pre-authorizes Claude to update git config in my own repos without re-asking
metadata:
  type: feedback
---

Updating `git config` is allowed on my machine when the change is confined to
`user.name`, `user.email`, or `init.defaultBranch` and the repo is one I own
(a personal fork or a repo under my own GitHub namespace). Show me the exact
command before running it. Any other git config key or any shared/upstream
repo still requires an explicit per-session yes from me.
```

Place the file under `~/.claude/projects/<encoded-cwd>/memory/` and add a one-line pointer to the project's `MEMORY.md`. Claude will apply the rule the next time you start a session in that directory.

Notes on the body:
- Lead with the rule, follow with the scope. The narrower the scope, the smaller the blast radius if the memory is misinterpreted later.
- "Show me the exact command before running it" keeps you in the loop even when the policy says yes.
- Keeping writes limited to a known subset of config keys protects you from a wider surprise (for example, Claude silently flipping `commit.gpgsign`).

### 3. Repo-wide `CLAUDE.md`

If a repo is shared with teammates and you want everyone's Claude sessions to behave the same way inside it, drop the rule into a top-level `CLAUDE.md`:

```markdown
# Repo rules for Claude Code

- `git config` changes limited to `user.name`, `user.email`, and
  `init.defaultBranch` are allowed in this repo without further confirmation,
  because contributors set their identity on first clone. Any other key still
  requires an explicit go-ahead.
```

`CLAUDE.md` lives in the repo and is read by every Claude Code session started in that directory, for anyone who checks it out. Prefer this over a personal memory when the rule should apply to collaborators as well.

## What to avoid

- A blanket "always allowed to touch git config" rule. Too wide. The point of the safety rule is to catch surprising changes, so keep the override narrow.
- Setting `user.email` to something you cannot verify. Commits that use an email not attached to your GitHub account show as a stranger in the commit graph.
- Overriding the rule in a memory and then forgetting the memory exists. Keep the memory discoverable (listed in `MEMORY.md`) and dated so you can review it later.

## Related rules in the git safety protocol

For context, the same protocol also discourages:

- Force-pushing to `main` or `master` without an explicit yes.
- Skipping hooks (`--no-verify`, `--no-gpg-sign`) without an explicit yes.
- Amending or deleting published commits without an explicit yes.

Each of those has the same shape: safe default, override by explicit instruction, with memory and `CLAUDE.md` as the persistent escape hatches. The pattern in this recipe applies to any of them.
