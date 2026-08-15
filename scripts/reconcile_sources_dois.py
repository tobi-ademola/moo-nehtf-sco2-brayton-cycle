r"""Reconcile the hand-verified DOI set in `SOURCES - Copy.md` into `SOURCES.md`, entry by entry.

**RETIRED 2026-08-15 — its input no longer exists, and that is the successful outcome.**
The reconcile ran to completion, its 14 conflicts were adjudicated against Crossref
(`scripts/apply_doi_conflict_resolutions.py`), and `SOURCES - Copy.md` was then deleted after being
checked to contain nothing SOURCES.md lacks: 0 DOIs unique to it, and its only unique prose was
superseded citations plus two corruptions from a Prettier pass. Running this now prints an
explanation and exits 0. It is kept because it is the RECORD OF HOW that merge was done and the
home of the `*[DOI verified]*` convention SOURCES.md now depends on — and because `--verified`
still accepts any future hand-verified revision.

WHY THIS EXISTS. The user hand-verified (opened and checked) every DOI in a copy of SOURCES.md
taken during Session D. SOURCES.md has moved on since: Session E (`edd9f8b`) added section A8 and
corrected the F2 Battisti citation. The two files are SIBLINGS, not ancestor/descendant --

    b9db467 (165 lines, 12 DOIs)
        |
        +--> Session D draft (50 sources) --> `SOURCES - Copy.md`   [+ hand-verified DOIs, + Prettier pass]
        |
        +--> edd9f8b -> HEAD `SOURCES.md`                            [+ A8, + F2 correction]

so neither file dominates. Merging the copy over SOURCES.md would silently drop Session E's work;
merging SOURCES.md over the copy would discard the verification. This script does the only correct
thing: it treats SOURCES.md as the structural base and ports ONLY the DOI values across.

The reason a reconcile is needed AT ALL is that SOURCES.md records identifiers but records no
VERIFICATION STATE. A checked DOI and an unchecked one are byte-identical in the file, so the
knowledge dies with the session that did the checking (`CLAUDE.md` Section 0 rule 2: the terminal
is ephemeral). This script recovers that state for one cycle; the durable fix is the `[verified]`
marker it writes back into SOURCES.md under --apply, so the next rewrite is reconcilable by reading.

WHAT IT DOES. Splits both files into entries (A1..J, including the D-series bullets), pulls each
entry's DOI plus the article number stated in its citation line, and classifies:

    CONFIRMED  -- both files carry the same DOI: the hand check stands, nothing to do
    FILLED     -- SOURCES.md holds a placeholder (`xxxxx`, `.../j.x.2023.xxxxx`), the copy holds a
                  real DOI: a pure gain, safe to apply
    CHANGED    -- both hold real but DIFFERENT DOIs: a conflict needing adjudication, NOT auto-applied
    NO_DOI     -- entry legitimately has none (A2 thesis, D1/D3, E2 NREL report, C0/J prose)

and cross-checks each verified DOI's trailing number against the article number in the citation
("Energy 300:131594" vs `10.1016/j.energy.2024.131594`). Elsevier/MDPI/IEEE suffixes normally ARE
the article number, so a DISAGREES flag means the entry is internally inconsistent -- the DOI and
the volume:article line cannot both be right, and one of them still has to be fixed by hand.

Inputs:  SOURCES.md (base, HEAD state) and `SOURCES - Copy.md` (hand-verified DOIs), both at repo
         root. Override with --base / --verified. Stdlib only -- no PySAM, no .venv dependency.

Run (report only, writes nothing to SOURCES.md):
      .\.venv\Scripts\python.exe -u .\scripts\reconcile_sources_dois.py

Run (apply FILLED, and CHANGED too once the policy in apply_policy() says so):
      .\.venv\Scripts\python.exe -u .\scripts\reconcile_sources_dois.py --apply

Outputs: results/sources_doi_reconcile_<stamp>.csv  -- one row per entry, the tickable ledger
         results/sources_doi_reconcile_<stamp>.md   -- counts + the conflict worklist, for PROGRESS_LOG
"""

import argparse
import csv
import datetime
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(REPO_ROOT, "results")

DEFAULT_BASE = "SOURCES.md"
DEFAULT_VERIFIED = "SOURCES - Copy.md"

# A DOI is `10.<registrant>/<suffix>`; the suffix runs to whitespace or markdown punctuation.
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s)\]}`,;\"']+")
# `### A5. Stamatellos ...` / `## C. VISCOSITY ...` / `### C0. HEADLINE ...`
HEADING_RE = re.compile(r"^#{2,4}\s+([A-Z]\d{0,2})[.\s]")
# The D-series lives in bullets, not headings: `- **D2. Yang et al. 2023**, ...`
BULLET_ENTRY_RE = re.compile(r"^\s*-\s+\*\*([A-Z]\d{1,2})\.")
# Placeholders left to resolve later: `10.1016/j.solener.2023.xxxxx`, `10.1021/acsami.3c0xxxx`
STUB_RE = re.compile(r"(x{3,}|\.\.\.)", re.IGNORECASE)
# The article number in a citation line. The parenthesised issue is optional and need not be
# numeric -- real forms in this file are `300:131594`, `16(12):4755`, `254(A):124286`, `50(20-B)`.
ARTICLE_NO_RE = re.compile(r"\b\d{1,3}(?:\([0-9A-Za-z-]{1,6}\))?:(\d{3,7})\b")
# The trailing numeric token of a DOI suffix: `...2024.131594` -> `131594`, `en16124755` -> `16124755`
DOI_TAIL_RE = re.compile(r"(\d{3,9})[a-z-]*$", re.IGNORECASE)
# The hedge a DOI carried while unverified: `(verify at cite)`, `(fetch at cite)`,
# `(verify article no. at cite)`, `(PII S0927024821004736 -- verify vol/pages at cite)`.
VERIFY_HEDGE_RE = re.compile(r"\s*\([^)]*\b(?:verify|fetch)\b[^)]*\)")


def normalize(raw):
    """Reduce a DOI to the form used to decide 'is this the same link?'.

    This is the equivalence rule the whole reconcile turns on: two DOIs landing on the same key are
    treated as ONE link, so a match means 'already hand-verified' and a miss means 'adjudicate'.
    The error is not symmetric -- too strict re-opens work already done (wasteful), too loose marks
    an unchecked DOI as verified (a citation error reaching the thesis). Real cases in these files:

        `10.3389/fnuen.2024.1341754.`  vs `10.3389/fnuen.2024.1341754`   (markdown sentence period)
        `https://doi.org/10.1016/...`  vs `10.1016/...`                  (resolver-prefixed)
        `10.1016/J.SOLMAT.2022.111852` vs `10.1016/j.solmat.2022.111852` (DOIs are case-insensitive)
    """
    if not raw:
        return ""
    key = raw.strip().lower()
    key = re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", key)
    return key.rstrip(".,;:)]}")


def split_entries(text):
    """Return {entry_id: {"lines": [(lineno, text), ...]}} for one SOURCES-format file.

    Headings open an entry; D-series bullets open one too and are closed by the next bullet at the
    same level, since they carry no heading of their own.
    """
    entries = {}
    current = "(preamble)"
    in_bullet_entry = False
    for lineno, line in enumerate(text.splitlines(), start=1):
        heading = HEADING_RE.match(line)
        bullet = BULLET_ENTRY_RE.match(line)
        if heading:
            current, in_bullet_entry = heading.group(1), False
        elif bullet:
            current, in_bullet_entry = bullet.group(1), True
        elif in_bullet_entry and re.match(r"^\s*-\s+(?!\*\*[A-Z]\d)", line):
            # a sibling bullet that is not a new D-entry ends the current one
            current, in_bullet_entry = current, True
        entries.setdefault(current, {"lines": []})["lines"].append((lineno, line))
    return entries


def entry_doi(entry):
    """Return (raw_doi, lineno) for the first DOI in an entry, or (None, None)."""
    for lineno, line in entry["lines"]:
        found = DOI_RE.search(line)
        if found:
            return found.group(0), lineno
    return None, None


def entry_article_numbers(entry):
    """Return the article/page numbers stated in an entry's CITATION prose only.

    Scanning the whole entry produces false positives, because `n:m` shapes also occur in the key
    numbers ("100:100 nuclear:CSP" in H3, "263:111852-analog" in B3). The citation is always the
    prose between the heading and the first `- **...**` bullet, so stop there. Stopping also keeps
    the DOI bullet out of scope, so the DOI cannot corroborate itself.
    """
    numbers = set()
    # lines[0] is the entry's own opener; for a D-series bullet that opener IS a `- **` line, so
    # skipping it is what lets the loop below break on the NEXT bullet rather than immediately.
    for _, line in entry["lines"][1:]:
        if re.match(r"^\s*-\s+\*\*", line):
            break
        numbers.update(ARTICLE_NO_RE.findall(line))
    return numbers


def crosscheck(doi, article_numbers):
    """Does the DOI's trailing number match an article number stated in the citation?

    Elsevier (`10.1016/j.energy.2024.131594`), MDPI (`10.3390/en16124755`) and Springer suffixes
    normally embed the article number, so DISAGREES means the entry contradicts itself and one of
    the two fields is still wrong even after the DOI is trusted. Registrants that do not encode it
    (ASME `10.1115/1.4027936`, IEEE `10.1109/4235.996017`, AIP `10.1063/5.0086032`) return N/A.
    """
    if not doi or not article_numbers:
        return "n/a"
    if doi.lower().startswith(("10.1115/", "10.1109/", "10.1063/", "10.1021/", "10.3389/")):
        return "n/a"
    tail = DOI_TAIL_RE.search(doi)
    if not tail:
        return "n/a"
    tail_digits = tail.group(1)
    for number in article_numbers:
        if tail_digits.endswith(number) or number.endswith(tail_digits):
            return "agrees"
    return "DISAGREES"


def apply_policy(status, crosscheck_result):
    """Decide what --apply does with one reconciled entry: return (action, reason).

    Actions: "apply"      -- write the verified DOI into SOURCES.md
             "skip"       -- nothing to do (already identical, or no DOI on either side)
             "quarantine" -- a decision the reconcile is not entitled to make on its own; the entry
                             is reported and left untouched for a human to adjudicate.
    """
    if status == "FILLED":
        return "apply", "placeholder replaced by a hand-verified DOI -- pure gain"
    if status == "CONFIRMED":
        return "skip", "identical in both files; the hand check carries over"
    if status == "NO_DOI":
        return "skip", "entry carries no DOI by design"
    if status == "MISSING_DOI":
        return "quarantine", "no DOI in EITHER file -- still needs a hand lookup"
    if status == "CHANGED":
        # ALWAYS quarantine, and `crosscheck_result` deliberately does not soften this. Settled
        # empirically on 2026-08-15, when all 14 CHANGED rows were adjudicated against Crossref
        # (`scripts/apply_doi_conflict_resolutions.py`):
        #
        #   as-drafted DOI correct   0 / 14   -- it agreed with the printed article number because
        #                                       the two were fabricated together, not because it
        #                                       was right. So "agrees" is not evidence.
        #   hand-verified correct   13 / 14
        #   NEITHER correct          1 / 14   -- C7 resolved to a third DOI entirely.
        #
        # That single miss is the argument. Auto-applying the verified column would have been right
        # 13 times and written a wrong citation into the thesis once, silently -- and a citation
        # error costs far more than one lookup. Neither column is trustworthy enough to apply
        # unattended; only an external authority queried BY TITLE settles it.
        return "quarantine", (
            "both DOIs real and different -- resolve against Crossref by title "
            "(crosscheck was '{}', which is not sufficient evidence either way)".format(
                crosscheck_result))
    return "skip", "unclassified"


def reconcile(base_entries, verified_entries):
    """Return one row dict per entry present in either file."""
    rows = []
    for entry_id in sorted(set(base_entries) | set(verified_entries)):
        # Section J is the transparency log, and J1/J2 quote the very DOIs under dispute. Scanning
        # them would feed this script's own output back in as if it were citation data.
        if entry_id == "(preamble)" or re.match(r"^J\d*$", entry_id):
            continue
        base = base_entries.get(entry_id, {"lines": []})
        ver = verified_entries.get(entry_id, {"lines": []})
        base_doi, base_line = entry_doi(base)
        ver_doi, _ = entry_doi(ver)

        if not base_doi and not ver_doi:
            # Two very different things look identical here: a section heading or an entry that is
            # DOI-less by nature (A2 thesis, E2 NREL report -- both say "n/a"), versus a real
            # journal source nobody has found a DOI for yet. Only the second needs work.
            declares_none = any("n/a" in line.lower() for _, line in base["lines"] + ver["lines"])
            is_entry = bool(re.match(r"^[A-Z]\d+$", entry_id)) and entry_id not in ("C0",)
            status = "MISSING_DOI" if (is_entry and not declares_none) else "NO_DOI"
        elif base_doi and ver_doi and normalize(base_doi) == normalize(ver_doi):
            status = "CONFIRMED"
        elif base_doi and STUB_RE.search(base_doi) and ver_doi:
            status = "FILLED"
        elif base_doi and ver_doi:
            status = "CHANGED"
        elif ver_doi:
            status = "FILLED"
        else:
            status = "BASE_ONLY"

        check = crosscheck(ver_doi or base_doi, entry_article_numbers(base) or entry_article_numbers(ver))
        try:
            action, reason = apply_policy(status, check)
        except NotImplementedError as exc:
            action, reason = "UNDECIDED", str(exc)
        rows.append({
            "entry": entry_id,
            "status": status,
            "base_doi": base_doi or "",
            "verified_doi": ver_doi or "",
            "article_no_crosscheck": check,
            "action": action,
            "reason": reason,
            "base_line": base_line or "",
        })
    return rows


def bullet_last_line(lines, idx):
    """Index of the LAST physical line of the markdown bullet starting at `idx`.

    DOI bullets are not always one line -- A3's runs on ("...ASME ES2012-91179,\n  DOI ...).\n").
    Appending the verified marker at `idx` would drop it mid-sentence, so walk forward over
    continuation lines (indented, not themselves a bullet or heading) and mark the real end.
    """
    end = idx
    while end + 1 < len(lines):
        nxt = lines[end + 1]
        if not nxt.strip():
            break
        if not re.match(r"^\s{2,}\S", nxt) or re.match(r"^\s*-\s", nxt) or nxt.startswith("#"):
            break
        end += 1
    return end


def apply_to_base(base_path, rows, date_str):
    """Rewrite SOURCES.md: substitute verified DOIs, and record the verification state in the file.

    Two edits per touched DOI line, and the second is the point of the exercise:
      1. the DOI itself is replaced (rows whose action is "apply");
      2. the stale `(verify at cite)` / `(fetch at cite)` hedge is dropped and a
         `*[DOI verified <date>]*` marker appended, on APPLY and CONFIRMED rows alike.

    Without (2), SOURCES.md would once again hold checked and unchecked DOIs in byte-identical
    form and the next rewrite would be unreconcilable -- the exact failure this script exists to
    undo. Edits are keyed to the entry's own DOI line number, so a DOI string that happens to
    appear twice in the file cannot be clobbered at the wrong site. Re-running is a no-op.
    """
    with open(base_path, "r", encoding="utf-8", newline="") as fh:
        lines = fh.read().splitlines(keepends=True)

    applied, marked = [], []
    for row in rows:
        if row["status"] not in ("CONFIRMED", "FILLED") or not row["base_line"]:
            continue
        if row["status"] == "FILLED" and row["action"] != "apply":
            continue
        idx = int(row["base_line"]) - 1
        line = lines[idx]
        if row["base_doi"] not in line:
            continue  # line moved since the scan; skip rather than guess
        if row["action"] == "apply":
            line = line.replace(row["base_doi"], row["verified_doi"], 1)
            applied.append((row["entry"], row["base_doi"], row["verified_doi"]))
        lines[idx] = VERIFY_HEDGE_RE.sub("", line)

        end = bullet_last_line(lines, idx)
        tail = lines[end]
        if "DOI verified" not in tail:
            eol = "\r\n" if tail.endswith("\r\n") else ("\n" if tail.endswith("\n") else "")
            body = VERIFY_HEDGE_RE.sub("", tail[:len(tail) - len(eol)]).rstrip()
            lines[end] = "{}  *[DOI verified {}]*{}".format(body, date_str, eol)
            marked.append(row["entry"])

    with open(base_path, "w", encoding="utf-8", newline="") as fh:
        fh.write("".join(lines))
    return applied, marked


def write_outputs(rows, args, stamp, commit):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    base = os.path.join(RESULTS_DIR, "sources_doi_reconcile_{}".format(stamp))
    fields = ["entry", "status", "base_doi", "verified_doi", "article_no_crosscheck",
              "action", "reason", "base_line"]
    with open(base + ".csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    counts = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    lines = [
        "# SOURCES.md <- hand-verified DOI reconcile",
        "",
        "- Generated: {}".format(stamp),
        "- Script: `scripts/reconcile_sources_dois.py` @ commit `{}`".format(commit),
        "- Base (structure): `{}`".format(args.base),
        "- Verified (DOIs):  `{}`".format(args.verified),
        "- Mode: {}".format("APPLIED to base" if args.apply else "report only, base untouched"),
        "",
        "| status | count | meaning |",
        "|---|---|---|",
        "| CONFIRMED | {} | same DOI in both files -- hand check carries over |".format(
            counts.get("CONFIRMED", 0)),
        "| FILLED | {} | placeholder in base, real DOI in verified copy |".format(
            counts.get("FILLED", 0)),
        "| CHANGED | {} | different real DOIs -- CONFLICT, needs adjudication |".format(
            counts.get("CHANGED", 0)),
        "| MISSING_DOI | {} | real source, no DOI in EITHER file -- hand lookup outstanding |".format(
            counts.get("MISSING_DOI", 0)),
        "| NO_DOI | {} | section heading, or DOI-less by nature (thesis / NREL report) |".format(
            counts.get("NO_DOI", 0)),
        "",
        "## Conflicts and cross-check failures",
        "",
        "`article_no_crosscheck = DISAGREES` means the verified DOI and the volume:article number",
        "printed in the citation line cannot both be right -- fix the citation metadata too.",
        "",
        "| entry | status | base DOI | verified DOI | crosscheck | action |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        if (row["status"] in ("CHANGED", "MISSING_DOI")
                or row["article_no_crosscheck"] == "DISAGREES"):
            lines.append("| {entry} | {status} | `{base_doi}` | `{verified_doi}` | "
                         "{article_no_crosscheck} | {action} |".format(**row))
    lines += ["", "## Substitutions {}".format(
        "applied" if args.apply else "--apply WOULD make (base untouched this run)"), ""]
    applied = [r for r in rows if r["action"] == "apply"]
    if applied:
        lines += ["| entry | old | new |", "|---|---|---|"]
        for row in applied:
            lines.append("| {entry} | `{base_doi}` | `{verified_doi}` |".format(**row))
    else:
        lines.append("_none_")
    lines.append("")
    with open(base + ".md", "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return base, counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=DEFAULT_BASE,
                        help="file providing structure/prose (default: SOURCES.md)")
    parser.add_argument("--verified", default=DEFAULT_VERIFIED,
                        help="file providing hand-verified DOIs (default: 'SOURCES - Copy.md')")
    parser.add_argument("--apply", action="store_true",
                        help="write the verified DOIs into --base (default: report only)")
    args = parser.parse_args()

    commit = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT).decode().strip()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    base_path = os.path.join(REPO_ROOT, args.base)
    verified_path = os.path.join(REPO_ROOT, args.verified)
    if not os.path.exists(verified_path):
        # Expected end state, not an error. See the RETIRED note in this module's docstring.
        print("The hand-verified input '{}' is not present.".format(args.verified))
        print("")
        print("This is expected: the reconcile it fed COMPLETED on 2026-08-15 and the file was")
        print("deleted once verified to hold nothing SOURCES.md lacks. This script is kept as the")
        print("record of how that merge was done, and is re-runnable only if a comparable")
        print("hand-verified revision is supplied:")
        print("")
        print("    python scripts/reconcile_sources_dois.py --verified <other-file.md>")
        print("")
        print("Outcome of the completed run: results/sources_doi_reconcile_20260815T122957Z.*")
        print("Conflict adjudication:        results/sources_doi_resolutions_20260815T122908Z.*")
        print("Current verification state lives in SOURCES.md itself, as *[DOI verified]* markers.")
        return 0
    with open(base_path, encoding="utf-8") as fh:
        base_entries = split_entries(fh.read())
    with open(verified_path, encoding="utf-8") as fh:
        verified_entries = split_entries(fh.read())

    rows = reconcile(base_entries, verified_entries)

    if args.apply:
        applied, marked = apply_to_base(base_path, rows, stamp[:4] + "-" + stamp[4:6] + "-" + stamp[6:8])
        print("applied {} DOI substitutions to {}".format(len(applied), args.base))
        for entry, old, new in applied:
            print("  {:4s} {}  ->  {}".format(entry, old, new))
        print("stamped {} DOI lines as verified: {}".format(len(marked), ", ".join(marked)))

    out, counts = write_outputs(rows, args, stamp, commit)
    print("entries: base {}  verified {}".format(len(base_entries) - 1, len(verified_entries) - 1))
    for status in ("CONFIRMED", "FILLED", "CHANGED", "MISSING_DOI", "NO_DOI"):
        print("  {:10s} {}".format(status, counts.get(status, 0)))
    undecided = [r["entry"] for r in rows if r["action"] == "UNDECIDED"]
    if undecided:
        print("  UNDECIDED  {}  -> {}".format(len(undecided), ", ".join(undecided)))
    print("wrote {}.csv / .md".format(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
