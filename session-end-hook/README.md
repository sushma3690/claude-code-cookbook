# Session-end transcript export

A small, self-contained recipe that makes Claude Code save a readable copy of every conversation to disk, automatically, the moment the session ends.

## What problem this solves

Claude Code stores each session as a JSON Lines file under `~/.claude/projects/<encoded-cwd>/<session-uuid>.jsonl`. The format is excellent for machines (every event is one line) and painful for humans. If you ever want to re-read what you worked on last Tuesday without reopening the full session, you need a nicer format.

This recipe turns each session into one markdown file per calendar date, dropped into a `transcripts/` folder next to the jsonl. It runs on its own, so you do not have to remember to export anything.

## What a `SessionEnd` hook is

Claude Code ships with a hook system. A hook is just a shell command the harness runs for you at a well-known moment. `SessionEnd` fires when a session finishes. The harness pipes a small JSON blob on the hook's stdin, including the path to the session's jsonl and the session id, so the hook knows exactly what to work on.

Hooks are configured in `~/.claude/settings.json`. Nothing else is required.

## What the exported files look like

Example filenames in `~/.claude/projects/<some-project>/transcripts/`:

```
2026-10-07_review-pr-feedback_a1b2c3d4.md
2026-10-08_debug-ci-failure_e5f6g7h8.md
2026-10-08_pair-on-oauth-flow_i9j0k1l2.md
```

Each file opens with the date and the harness's auto-generated short title, then prints user turns and assistant turns in order:

```markdown
# 2026-10-08 — Debug CI failure

session: `e5f6g7h8-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

## User

why is the deploy job red

## Assistant

_[Bash]_ `gh run view 123 --log-failed | tail -40`

## Assistant

The deploy step is failing because the staging secret rotated last night. Here is what to change ...
```

Tool calls are summarised in a single line (just the command for Bash, just the file path for Read / Edit / Write, and so on). The full tool output is not pulled in, because the goal of the file is to be readable later, not to replay the full session byte for byte.

## Install

### 1. Drop the script somewhere stable

A common choice is `~/.claude/hooks/`:

```bash
mkdir -p ~/.claude/hooks
cp export-transcript.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/export-transcript.py
```

Any absolute path works. Hooks run with whatever CWD the harness happens to use, so always point at the script with its full path.

### 2. Register it in `~/.claude/settings.json`

Open your settings file and add a `hooks.SessionEnd` entry. If the file does not have a `hooks` key yet, add one. If it already has other hooks, merge this in alongside them:

```json
{
  "hooks": {
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/Users/you/.claude/hooks/export-transcript.py"
          }
        ]
      }
    ]
  }
}
```

Replace `/Users/you/` with your own home directory. The nested `hooks` array is Claude Code's shape for matcher-plus-commands, which is why the `command` block sits two levels deep.

### 3. Verify

Start any Claude Code session, say something, exit. Then check:

```bash
ls ~/.claude/projects/<the-project-you-just-used>/transcripts/
```

You should see a fresh markdown file.

## Run it by hand

The same script works as a plain command line tool. Point it at any session jsonl:

```bash
~/.claude/hooks/export-transcript.py \
  ~/.claude/projects/-Users-you-some-repo/session-id-here.jsonl
```

Useful for backfilling older sessions, or for exporting a session you ended before you installed the hook.

## How it decides on a filename

```
YYYY-MM-DD_<ai-title-slug>_<session-short-id>.md
```

- `YYYY-MM-DD` comes from the calendar date of each entry's own timestamp, so a session that crosses midnight produces two files, one per day.
- `<ai-title-slug>` comes from Claude Code's own auto-generated short title for the session (the `ai-title` entry in the jsonl), sanitised to be filesystem-safe.
- `<session-short-id>` is the first segment of the session UUID, so two different sessions on the same day never collide.

## Known limitation

The `ai-title` is set early in a session. If your conversation starts on one topic and drifts to another, the title in the filename will describe the opening, not where you ended up. Rename files by hand if you want sharper labels.

## Safety notes

- The script catches every exception and exits zero, because a failing `SessionEnd` hook can block the harness. If an export silently fails, re-run the script by hand with the jsonl path to see the error.
- Transcripts include everything you typed and everything Claude replied, including any file paths, tool outputs, and code snippets that appeared inline. Treat the `transcripts/` folder like any other local notes directory.
