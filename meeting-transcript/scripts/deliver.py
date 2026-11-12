#!/usr/bin/env python3
"""Deliver completed text-only meeting inputs; retain every local artifact."""
import argparse
import fcntl
import hashlib
import json
import re
import shlex
import subprocess
import tempfile
import uuid
from pathlib import Path

FILES = ("transcript.md", "session.json")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def remote(host, *args, check=True):
    return subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", host,
         shlex.join(args)], check=check, text=True, capture_output=True, timeout=120)


def hashes(host, directory):
    result = remote(host, "sha256sum", *(f"{directory}/{n}" for n in FILES))
    return [line.split()[0] for line in result.stdout.splitlines()]


def deliver(host, root, session):
    if not re.fullmatch(r"\d{8}-\d{6}", session.name):
        raise ValueError(f"Invalid session ID: {session.name}")
    if any((session / n).is_symlink() for n in FILES):
        raise ValueError(f"Symlink input refused: {session}")
    contents = {n: (session / n).read_bytes() for n in FILES}
    metadata = json.loads(contents["session.json"])
    if metadata.get("state") != "completed":
        print(f"SKIP incomplete {session.name}")
        return
    if metadata.get("id") != session.name or not contents["transcript.md"].strip():
        raise ValueError(f"Invalid metadata or empty transcript: {session}")
    expected = [digest(contents[n]) for n in FILES]
    for directory in (f"{root}/{session.name}", f"{root}/archived/{session.name}"):
        found = remote(host, "test", "-e", directory, check=False)
        if found.returncode not in (0, 1):
            raise RuntimeError(found.stderr)
        if found.returncode == 0:
            if hashes(host, directory) != expected:
                raise ValueError(f"Changed input requires review: {directory}")
            print(f"UNCHANGED {directory}")
            return
    staging = f"{root}/.incoming/{session.name}-{uuid.uuid4().hex}"
    remote(host, "mkdir", "-p", staging)
    # Only these two immutable snapshots enter scp, never the meeting directory.
    with tempfile.TemporaryDirectory(prefix="meeting-text-") as temporary:
        paths = []
        for name, content in contents.items():
            path = Path(temporary) / name
            path.write_bytes(content)
            paths.append(str(path))
        subprocess.run(["scp", "-q", "-o", "BatchMode=yes", *paths,
                        f"{host}:{staging}/"], check=True, timeout=120)
    if hashes(host, staging) != expected:
        raise ValueError(f"Transfer hash mismatch: {staging}")
    if any(digest((session / n).read_bytes()) != expected[i]
           for i, n in enumerate(FILES)):
        raise ValueError(f"Source changed during delivery: {session}")
    destination = f"{root}/{session.name}"
    remote(host, "mv", "-T", "--no-clobber", staging, destination)
    if remote(host, "test", "-e", staging, check=False).returncode == 0:
        raise ValueError(f"Concurrent destination requires review: {destination}")
    if hashes(host, destination) != expected:
        raise ValueError(f"Published hash mismatch: {destination}")
    print(f"DELIVERED {session.name} files=2 sha256={','.join(expected)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="adam")
    parser.add_argument("--root", default="/home/xuanwo/Meetings")
    parser.add_argument("--source", type=Path, default=Path.home() / "Meetings")
    parser.add_argument("--session")
    args = parser.parse_args()
    state = Path.home() / ".cache/meeting-transcript"
    state.mkdir(parents=True, exist_ok=True)
    with (state / "delivery.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        sessions = [args.source / args.session] if args.session else sorted(
            p for p in args.source.iterdir()
            if re.fullmatch(r"\d{8}-\d{6}", p.name) and p.is_dir()
            and all((p / n).is_file() for n in FILES))
        failures = []
        for session in sessions:
            try:
                deliver(args.host, args.root, session)
            except Exception as error:
                failures.append(f"{session.name}: {error}")
        if failures:
            raise SystemExit("\n".join(failures))


if __name__ == "__main__":
    main()
