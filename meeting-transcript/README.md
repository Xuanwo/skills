# Text-only remote workflow

The recorder stays on the Mac. The remote agent owns summaries, dictionaries,
and the text archive. The existing Notes replica brings remote results back to
the Mac; this workflow does not introduce a second Notes writer.

## Delivery

Run `python3 scripts/deliver.py --session SESSION_ID` for the first trial.
Without `--session`, the script scans completed immediate child directories of
`~/Meetings`. It sends only `transcript.md` and `session.json` to
`adam:/home/xuanwo/Meetings`. Audio and all other artifacts remain on the Mac.

Delivery verifies SHA256 before publishing a hidden staging directory. Identical
pending or archived inputs are skipped. Changed inputs are an explicit error;
they require review rather than overwriting a summary's original evidence.
Interrupted transfers remain hidden and a later invocation can retry safely.
The script never archives or deletes local recorder directories.

Use a local launchd timer for delivery, with an absolute Python interpreter and
script path. Keep it disabled until the first end-to-end trial passes. Transport
failures are visible in the configured launchd log and retried on the next run.

## Remote processing

Deploy this directory through Git. Use the deployed `SKILL.md` explicitly rather
than an older machine-specific installed skill. `scripts/trial.py SESSION_ID`
runs one bounded Codex CLI task, stores its JSONL/result/exit status under
`~/.local/state/meeting-transcript`, and holds a scan lock. Run it in tmux so SSH
disconnects do not terminate processing. Do not run a trial concurrently with
the scheduled scanner.

Verify the note, both dictionary passes, original input hashes, and text archive
before enabling the remote automation. Keep the old Mac scanner disabled.
Schedule the remote agent through its supported automation interface, not by
editing app databases or automation files. The automation must execute on the
remote Notes host, not merely use remote-looking paths in a local task.

The automation follows `SKILL.md`, including read-only name verification and no
team-visible writes. Archival is permitted only after note and dictionary
validation. Re-running delivery after archival must skip the same session.

## Validation

Run `python3 -m unittest discover -s scripts -p 'test_*.py'` for the allowlist,
incomplete session, and changed-input guards. These tests supplement, but do not
replace, the real SSH transfer and remote summarization trial.
