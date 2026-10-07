#!/usr/bin/env python3
"""Export a Claude Code session into readable markdown, one file per calendar day.

A Claude Code "session" is one conversation, stored on disk as a jsonl file
under `~/.claude/projects/<encoded-cwd>/<session-uuid>.jsonl`. Each line is one
event: a user message, an assistant message, a tool call, a file snapshot, and
so on. The raw file is great for machines and painful to read.

This script turns a session jsonl into one markdown file per calendar date,
dropping it into a sibling `transcripts/` folder next to the jsonl. It can be
hooked up as a `SessionEnd` hook so Claude writes a transcript automatically
when a session ends, or it can be run by hand on any jsonl.

Why "per calendar day" and not "per session": a single long conversation that
starts at 11 PM and continues past midnight produces two files, which is
usually what you want for a journal-style archive. Short same-day sessions
each get their own file because the filename includes a session id.
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def slugify(text: str, limit: int = 60) -> str:
    """Turn arbitrary text into a filename-safe slug.

    Keeps lowercase letters and digits, collapses everything else into single
    hyphens, trims leading and trailing hyphens, and caps the length so a very
    long title does not blow up the filename.
    """
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:limit] or "untitled"


def extract_text(content) -> str:
    """Pull plain text out of a message `content` field.

    Claude Code stores a message's content in two shapes. For plain user text
    it is a single string. For richer assistant replies it is a list of
    content blocks, each a dict with a `type` such as `text`, `tool_use`, or
    `thinking`. This helper only cares about `text` blocks and ignores the
    rest, because tool calls get summarised separately and thinking blocks
    are internal reasoning we do not want in the transcript.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for c in content:
            if isinstance(c, dict) and c.get("type") == "text":
                parts.append(c.get("text", ""))
        return "\n".join(parts)
    return ""


def summarize_tool_use(block: dict) -> str:
    """Render a one-line summary of a tool call.

    Full tool inputs (large file contents, long bash scripts, big JSON blobs)
    are not useful in a human-readable transcript and make the file huge. For
    each tool we only keep the bit a human would want when skimming later:
    the command for Bash, the file path for Read / Edit / Write, the task
    subject for the Task tools, and so on.
    """
    name = block.get("name", "?")
    inp = block.get("input") or {}
    if name == "Bash":
        cmd = (inp.get("command") or "").replace("\n", " ")[:140]
        return f"_[Bash]_ `{cmd}`"
    if name in {"Read", "Write"}:
        return f"_[{name}]_ `{inp.get('file_path', '')}`"
    if name == "Edit":
        return f"_[Edit]_ `{inp.get('file_path', '')}`"
    if name in {"TaskCreate", "TaskUpdate", "TaskList", "TaskGet"}:
        subj = inp.get("subject") or inp.get("taskId") or ""
        status = inp.get("status") or ""
        tail = f" {subj}" if subj else ""
        tail += f" -> {status}" if status else ""
        return f"_[{name}]_{tail}"
    if name == "WebFetch":
        return f"_[WebFetch]_ {inp.get('url', '')}"
    if name == "AskUserQuestion":
        return "_[AskUserQuestion]_"
    return f"_[{name}]_"


def render_day(entries: list[dict], session_id: str, ai_title: str | None, day: str) -> str:
    """Render one day's worth of entries into markdown.

    The output alternates `## User` and `## Assistant` sections. An assistant
    turn can contain both prose and tool calls, so we collect text blocks and
    tool-use summaries together under a single Assistant heading. Empty turns
    (for example, system attachments with no visible content) are skipped so
    the file stays readable.
    """
    heading = ai_title or "(no title)"
    lines = [
        f"# {day} — {heading}",
        "",
        f"session: `{session_id}`",
        "",
    ]
    for e in entries:
        t = e.get("type")
        msg = e.get("message") or {}
        role = msg.get("role")
        content = msg.get("content")

        if t == "user" and role == "user":
            text = extract_text(content)
            if not text.strip():
                continue
            lines.append("## User")
            lines.append("")
            lines.append(text.rstrip())
            lines.append("")

        elif t == "assistant" and role == "assistant":
            if not isinstance(content, list):
                text = str(content or "").strip()
                if not text:
                    continue
                lines.append("## Assistant")
                lines.append("")
                lines.append(text)
                lines.append("")
                continue

            assistant_parts: list[str] = []
            for c in content:
                if not isinstance(c, dict):
                    continue
                ct = c.get("type")
                if ct == "text":
                    txt = (c.get("text") or "").rstrip()
                    if txt:
                        assistant_parts.append(txt)
                elif ct == "tool_use":
                    assistant_parts.append(summarize_tool_use(c))

            if not assistant_parts:
                continue
            lines.append("## Assistant")
            lines.append("")
            lines.append("\n\n".join(assistant_parts))
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def load_payload() -> tuple[str | None, str | None]:
    """Figure out which jsonl to export and what session id to use.

    Two ways this script gets called:

      1. As a Claude Code `SessionEnd` hook. The harness pipes a small JSON
         blob on stdin that includes `transcript_path` and `session_id`. We
         prefer that if it is there.

      2. By hand, like `export-transcript.py /path/to/session.jsonl`. In
         that case stdin is empty, so we fall back to the first positional
         argument and derive the session id from the filename.
    """
    transcript_path = None
    session_id = None

    if not sys.stdin.isatty():
        raw = sys.stdin.read().strip()
        if raw:
            try:
                payload = json.loads(raw)
                transcript_path = payload.get("transcript_path")
                session_id = payload.get("session_id")
            except json.JSONDecodeError:
                pass

    if not transcript_path and len(sys.argv) >= 2:
        transcript_path = sys.argv[1]

    if transcript_path and not session_id:
        session_id = Path(transcript_path).stem

    return transcript_path, session_id


def main() -> int:
    transcript_path, session_id = load_payload()
    if not transcript_path or not os.path.exists(transcript_path):
        # Nothing to export. Return cleanly so we never break the parent hook.
        return 0

    entries: list[dict] = []
    ai_title: str | None = None
    with open(transcript_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                # A broken line should not kill the whole export.
                continue
            entries.append(d)
            # Claude Code adds a short auto-generated title early in a
            # session as an `ai-title` entry. The latest copy wins, so we
            # keep overwriting as we scan.
            if d.get("type") == "ai-title" and d.get("aiTitle"):
                ai_title = d["aiTitle"]

    if not entries:
        return 0

    # Group every event by the calendar date of its timestamp. This is what
    # lets a long session that crosses midnight land in two separate files.
    by_date: dict[str, list[dict]] = defaultdict(list)
    for e in entries:
        ts = e.get("timestamp")
        if not ts:
            continue
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            continue
        day = dt.strftime("%Y-%m-%d")
        by_date[day].append(e)

    if not by_date:
        return 0

    # The transcripts folder sits next to the session jsonl, so every project
    # that Claude Code tracks gets its own transcripts folder automatically.
    project_dir = Path(transcript_path).parent
    out_dir = project_dir / "transcripts"
    out_dir.mkdir(exist_ok=True)

    title_slug = slugify(ai_title or "untitled")
    sid_short = (session_id or "unknown").split("-")[0]

    written = []
    for day, day_entries in sorted(by_date.items()):
        out_file = out_dir / f"{day}_{title_slug}_{sid_short}.md"
        out_file.write_text(
            render_day(day_entries, session_id or "unknown", ai_title, day),
            encoding="utf-8",
        )
        written.append(str(out_file))

    for path in written:
        print(f"wrote {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        # If anything goes wrong, log it and exit zero. A failing hook that
        # bubbles up a non-zero exit code can block the harness; a failing
        # export should never do that.
        print(f"export-transcript failed: {exc}", file=sys.stderr)
        sys.exit(0)
