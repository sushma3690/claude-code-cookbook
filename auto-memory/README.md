# The auto memory system

Claude Code's built-in notebook. The feature that makes a new session feel like it already knows you, without you having to re-explain who you are, how you like to work, or what the project constraints are. This recipe explains where it lives, how it is structured, when Claude writes to it, and what you should and should not try to put in it.

## Where it lives

```
~/.claude/projects/<encoded-cwd>/memory/
├── MEMORY.md                      # the index
├── user_whatever.md               # individual notes
├── feedback_whatever.md
├── project_whatever.md
└── reference_whatever.md
```

One `memory/` folder per project. The parent folder's name is the project's working directory with slashes replaced by hyphens (so `/Users/you/some-repo` becomes `-Users-you-some-repo`). This per-project isolation means a preference saved while working on project A does not leak into project B.

A short explainer of the drawer naming lives in the [`git-config-override/`](../git-config-override/) recipe.

## Why it exists

Normally every Claude Code session starts from zero. You tell it who you are, how you want to be talked to, which commands matter for this project, and what rails to respect. Then you log off and tomorrow you tell it the same thing again.

The memory system is the mechanism that lets Claude remember those things on its own. It is just plain markdown files on your disk, so you can read, edit, and version them like any other local file.

## The four kinds of notes

Each note declares its type in frontmatter. The type is the single most important field because it tells Claude when to apply the note.

| Type | What it holds | Example body |
| --- | --- | --- |
| **user** | Who you are, your role, what you know and do not know | "Backend engineer, ten years of Go, first time in a React codebase. Explain frontend ideas in Go analogues." |
| **feedback** | How you want to work with Claude. Rules, preferences, overrides. | "Never push without my say-so. Draft the commit message, I will run the commands." |
| **project** | Facts about the current work that are not derivable from code or git | "Legal is driving the auth rewrite because of session token storage policy. Compliance beats ergonomics in scope calls." |
| **reference** | Pointers to information in external systems | "Pipeline bugs are tracked in Linear project INGEST, not GitHub issues." |

Treat the types as lanes, not labels. A note that holds a *rule* goes in `feedback`. A note that holds a *fact about the user* goes in `user`. A note that mixes both is a sign the note needs to be split.

## File format

Every note is markdown with a short YAML header:

```markdown
---
name: feedback-example
description: One-line summary used to decide when this note is relevant
metadata:
  type: feedback
---

Body content here. For a feedback or project note, lead with the rule or fact,
then **Why:** (the reason the user gave) and **How to apply:** (when the rule
kicks in). Including the why lets Claude judge edge cases rather than blindly
following the rule.

Link to related notes with [[other-note-name]] where `other-note-name` is the
`name:` field of another note.
```

- `name` is a short kebab-case slug. It is what other notes link to.
- `description` is one line and matters a lot: Claude uses it to decide whether to read the full note. Vague descriptions get ignored.
- `metadata.type` is one of `user`, `feedback`, `project`, `reference`.

## The `MEMORY.md` index

`MEMORY.md` sits at the top of the `memory/` folder and lists every note. It has no frontmatter and no body content of its own, just one line per note:

```markdown
- [Short title](file.md) — one-line description, under about 150 chars
```

Example:

```markdown
- [User profile](user_role.md) — backend engineer learning React
- [OSS workflow](feedback_oss.md) — never push without my say-so, no em dashes, test before saying done
- [Reference: Linear](reference_linear.md) — pipeline bugs tracked in project INGEST
```

Important: `MEMORY.md` is always loaded into Claude's context at session start. The individual notes are only loaded when their description looks relevant. So the index deserves to be concise. Lines past about 200 can get truncated.

Never put note *content* directly into `MEMORY.md`. The index is a table of contents, not a notebook.

## When Claude writes to memory

The built-in triggers are:

- You tell Claude something new about yourself.
- You *correct* an approach ("stop doing X", "do not Y").
- You *praise* an approach that was non-obvious ("yes, bundling into one PR was right, keep doing that"). This matters because without the praise signal, Claude only learns from mistakes and drifts away from judgment calls that already landed well.
- You mention a project fact that is not derivable from code (deadlines, stakeholders, reasons behind a rewrite).
- You point at an external system where information lives.

You can also just ask: "save a memory that ..." and Claude writes it directly.

## When Claude reads from memory

- At the top of every session, the index.
- Any time the current task looks relevant to a note's description.
- Any time you explicitly ask Claude to check, recall, or remember something.
- Not when you tell it to *ignore* memory.

## What memory is *not* for

This is as important as what it *is* for, because stale memory is worse than no memory. Do not put any of these in `memory/`:

- **Code patterns, conventions, architecture.** The code itself is the source of truth.
- **File paths and project structure.** Derivable by reading the project.
- **Git history, blame, who changed what.** `git log` is authoritative.
- **Debugging solutions, bug fix recipes.** The fix is in the commit; the context is in the commit message.
- **Anything already in `CLAUDE.md`.** That is the repo talking; memory is you talking.
- **In-progress session state.** That belongs in tasks or in a plan.

If you ask Claude to save something from this list, the right behavior is to push back and ask what was *surprising* or *non-obvious* about it, because that is the part worth keeping.

## The staleness discipline

Memory records a point-in-time truth. Six months later, that function might be renamed, that branch merged, that teammate gone. Three habits keep this from turning into misinformation:

1. **Verify before acting.** When a note says "the frobnicate module handles X", grep for it before suggesting a change. If it is gone, the memory is wrong.
2. **Trust what you see now.** If the current state contradicts a note, the current state wins and the note gets updated or deleted.
3. **Prefer snapshots that stay fresh elsewhere.** Do not freeze an activity log into memory. Point to `git log` or the live dashboard instead.

## How to add a note by hand

If you want to pre-seed memory without going through a conversation (which is what the [`git-config-override/`](../git-config-override/) recipe suggests for standing permissions), do it in two steps:

1. Create `~/.claude/projects/<encoded-cwd>/memory/your-note.md` with the frontmatter above and your body text.
2. Add one line to `~/.claude/projects/<encoded-cwd>/memory/MEMORY.md`:
   ```markdown
   - [Title](your-note.md) — one-line description
   ```

That is the whole mechanism. Claude will pick it up on the next session start.

## Related recipes

- [`instruction-precedence/`](../instruction-precedence/) — how memory interacts with a repo's `CLAUDE.md` when the two look like they conflict.
- [`git-config-override/`](../git-config-override/) — a worked example of putting a standing permission into memory.
