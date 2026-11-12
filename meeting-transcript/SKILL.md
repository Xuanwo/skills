---
name: meeting-transcript
description: Summarize completed meeting transcripts on the processing host, maintain local dictionaries, and archive text-only inputs after validation.
---

# Meeting Transcript

## Paths and ownership

Resolve all paths against the executing user's home, never `/Users/xuanwo`.
Inputs are `~/Meetings/<session_id>/{transcript.md,session.json}`. Notes live in
`~/Notes/context`; dictionaries are under `~/Notes/areas/LanceDB`.
Adam is the sole summary and dictionary writer. The Mac retains original audio
and transcripts. Never fetch, upload, remove, or archive Mac audio. On Adam,
archiving means moving only the received text directory to `~/Meetings/archived`.
Ignore hidden staging directories. Process only numeric `YYYYMMDD-HHMMSS`
directories with both files and `session.json` state `completed`.

## Processing

1. Read `~/.agents/rules/notes.md` and `~/Notes/METADATA.md`. Resolve any old
   macOS path in those instructions to this host's home. Use registered metadata.
2. Read `meeting-transcript-entity-dictionary.md` first, then
   `meeting-transcript-correction-dictionary.md`. Use standard entity spellings
   and context-specific ASR corrections, never blind global replacements.
3. For each meeting, delegate a bounded read-only summary to a subagent. It reads
   the two inputs and dictionaries and returns a Chinese draft, timestamps,
   decisions, actions, risks, and a separate correction proposal. Review its work
   against the complete transcript before writing. Do not infer System speaker
   identity from the calendar roster. Mic usually identifies the local user.
4. Verify consequential ambiguous names with read-only Slack MCP (including the
   Magpie hub). Never use Slack CLI/HTTP API, mark messages read, send messages,
   or create drafts. Notion verification uses `ntn` or a read-only Notion API.
   Do not write team-visible content or perform any meeting action items.
5. Write an English calendar title/H1 and Chinese body. Use sections 来源,
   核心摘要, 要点, 决策与结论, 行动项, 风险与不确定项, 后续提示. Cite the
   archived transcript path, session ID, actual time and timezone. Distinguish
   proposals, decisions, implementation, deployment, verification, and release.
   Unknown owners and deadlines remain unknown. No ASR audit or 纠错说明 section
   belongs in the note.
6. Use `YYYY-MM-DD-<english-slug>-meeting-summary.md`. Before creating a new note,
   search Notes for this session ID, including notes moved out of context. Resume
   an existing partial result instead of creating a duplicate. Never overwrite an
   unrelated note; use a session suffix if its filename collides.
7. Update both dictionaries with useful new entities, recurring/important ASR
   errors, recommended spelling, triggering context, confidence and verification
   sources. Reuse existing entries without duplicating them. When neither needs
   additions, explicitly report `没有新增词典项`.
8. Read back the note and both dictionary changes. Validate metadata, required
   sections, spelling, sources, and uncertainties. Record input SHA256 hashes.
   Only then move the input directory to `~/Meetings/archived/<session_id>`;
   never overwrite an existing archive. Verify both file hashes after moving.
9. Report the note path, meaningful findings, dictionary outcome and archive
   validation. No pending work is a quiet result, not a new notification.

## Recovery and concurrency

Only one scan may write the shared dictionaries at a time. A failed note or
dictionary pass leaves the input unarchived. A retry reviews existing artifacts
and completes the missing work. Changed content for an already received session
must be surfaced for review, never silently replace archived evidence.

## Text delivery

`scripts/deliver.py` runs on the Mac. It snapshots exactly the two named files,
checks completed metadata, delivers them to a hidden directory over SSH, verifies
both SHA256 hashes, and renames the directory into the ready queue. Duplicate
inputs already pending or archived are skipped only if both hashes match.
Use `--session <id>` for a single-meeting trial. It never reads audio bytes.
