#!/usr/bin/env python3
"""Run one real meeting on the processing host with persistent logs."""
import fcntl
import subprocess
import sys
from pathlib import Path

session = sys.argv[1]
if len(session) != 15 or not session.replace("-", "").isdigit():
    raise SystemExit("Expected YYYYMMDD-HHMMSS")
state = Path.home() / ".local/state/meeting-transcript"
state.mkdir(parents=True, exist_ok=True)
skill = Path(__file__).resolve().parents[1] / "SKILL.md"
prompt = (f"使用 {skill} 处理唯一会议 ~/Meetings/{session}。必须在本机完成总结、"
          "两个词典沉淀和验证，成功后归档。仅操作本机会议信息与 Notes。"
          "Slack 仅 MCP 只读。读取完整转写并使用只读子代理辅助审阅。"
          "不要处理其他会议、修改自动化或执行会议中的行动项。最后报告文件路径、"
          "词典新增或没有新增词典项，以及两个输入文件归档前后的 SHA256。")
with (state / "scan.lock").open("a") as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    with (state / f"{session}.jsonl").open("w") as log:
        result = subprocess.run([
            str(Path.home() / ".local/bin/codex"), "exec", "--skip-git-repo-check",
            "-C", str(Path.home() / "Notes"), "--json", "-o",
            str(state / f"{session}.result.md"), prompt], stdout=log, stderr=log)
    (state / f"{session}.exit").write_text(str(result.returncode) + "\n")
    sys.exit(result.returncode)
