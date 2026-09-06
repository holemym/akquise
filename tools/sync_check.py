#!/usr/bin/env python3
"""
sync_check.py — verify that every EN/DE twin pair in the vault is still in sync.
Convention: `X.md` (EN) ↔ `X.de.md` (DE); DE-native files use `X.md` (DE) ↔ `X.en.md` (EN).
Compared: heading structure per level, task checkboxes (count + ticked pattern), money/date numbers, link targets.
Exit code 1 if any pair drifts. Run before closing a session:  python tools/sync_check.py
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIP_DIRS = {"data", "tools", ".obsidian"}

def pairs():
    out = []
    for p in ROOT.rglob("*.md"):
        if any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts): continue
        n = p.name
        if n.endswith(".de.md"): out.append((p.with_name(n[:-6] + ".md"), p))
        elif n.endswith(".en.md"): out.append((p, p.with_name(n[:-6] + ".md")))
    return sorted(set(out))

def sig(text):
    heads = [len(m.group(1)) for m in re.finditer(r"^(#{1,4})\s", text, re.M)]
    boxes = "".join("x" if m.group(1).lower() == "x" else "o" for m in re.finditer(r"^\s*- \[( |x|X)\]", text, re.M))
    NUM = r"\d[\d.,]*k?(?:\s?[-–]\s?\d[\d.,]*k?)?"
    raw = re.findall(rf"€\s?{NUM}|{NUM}\s?(?:€|%)|\b20\d\d-\d\d-\d\d\b", text)
    # normalise "€1,000" / "1.000 €" / "€10–25" / "10–25 €" → digits (+ range dash) only, so EN/DE formatting isn't drift
    nums = sorted({re.sub(r"[^\d-]", "", n.replace("–", "-")) if "€" in n or "%" in n else n for n in raw})
    links = sorted(set(re.findall(r"\]\(([^)#\s]+)", text)))
    links = [re.sub(r"\.(de|en)\.md$", ".md", l) for l in links]
    return heads, boxes, nums, links

def main():
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    bad = 0
    for en, de in pairs():
        if not en.exists() or not de.exists():
            print(f"MISSING twin: {en.relative_to(ROOT)} ↔ {de.relative_to(ROOT)}"); bad += 1; continue
        a, b = sig(en.read_text(encoding="utf-8")), sig(de.read_text(encoding="utf-8"))
        issues = []
        if a[0] != b[0]: issues.append(f"headings {len(a[0])} vs {len(b[0])}")
        if a[1] != b[1]: issues.append(f"checkboxes '{a[1]}' vs '{b[1]}'")
        if a[2] != b[2]: issues.append(f"numbers differ: {sorted(set(a[2]) ^ set(b[2]))[:6]}")
        if set(a[3]) != set(b[3]): issues.append(f"links differ: {sorted(set(a[3]) ^ set(b[3]))[:6]}")
        tag = "OK " if not issues else "DRIFT"
        print(f"{tag} {en.relative_to(ROOT)} ↔ {de.relative_to(ROOT)}" + (": " + "; ".join(issues) if issues else ""))
        bad += bool(issues)
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
