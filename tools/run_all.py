#!/usr/bin/env python3
"""
run_all.py — detached full pipeline run:
  wait for the running harvest → re-run harvest (cached selectors are instant; empty ones get re-queried; stable pids)
  → audit → score → phone shots (batch-1 selection) → Befund pages → letters (HTML+PDF).
Writes data/run_all.log and touches data/RUN_DONE (or data/RUN_FAILED).
Launch detached (survives the tool timeout):
  powershell: Start-Process python -ArgumentList "tools/run_all.py" -WindowStyle Hidden -WorkingDirectory <akquise dir>
"""
import pathlib, subprocess, sys, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"; TOOLS = ROOT / "tools"
LOG = open(DATA / "run_all.log", "a", encoding="utf-8")
def log(m): LOG.write(time.strftime("%H:%M:%S ") + m + "\n"); LOG.flush()
def run(name, *args, logfile=None):
    out = open(DATA / (logfile or f"{name}.log"), "a", encoding="utf-8")
    r = subprocess.run([sys.executable, str(TOOLS / f"{name}.py"), *args], cwd=ROOT, stdout=out, stderr=subprocess.STDOUT)
    log(f"{name} {' '.join(args)} → exit {r.returncode}"); return r.returncode

BATCH1 = ["--segments", "S1,S4", "--districts", "1-9,18,19", "--top", "40"]
for f in ("RUN_DONE", "RUN_FAILED"): (DATA / f).unlink(missing_ok=True)
try:
    while not (DATA / "prospects.csv").exists(): time.sleep(20)
    log("first harvest done")
    run("harvest_osm")                       # rewrite with stable pids + re-query empty selectors
    log(f"prospects: {sum(1 for _ in open(DATA / 'prospects.csv', encoding='utf-8')) - 1} rows")
    rc = run("audit_site", "--workers", "24")
    run("score", "--top", "40")
    run("shots", *BATCH1)
    run("befund_pages", *BATCH1)
    rc2 = run("letters", *BATCH1, "--pdf")
    (DATA / ("RUN_DONE" if rc2 == 0 else "RUN_FAILED")).touch()
except Exception as e:
    log(f"FAILED {type(e).__name__}: {e}"); (DATA / "RUN_FAILED").touch()
