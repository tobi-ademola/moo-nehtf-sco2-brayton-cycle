r"""Apply the Crossref adjudication of the 14 SOURCES.md DOI conflicts raised by the 2026-08-15 reconcile.

WHY THIS EXISTS. `scripts/reconcile_sources_dois.py` merged a hand-verified DOI set into SOURCES.md
and quarantined 14 entries where the hand-verified DOI and the as-drafted DOI were both real but
DIFFERENT. Those 14 were adjudicated on 2026-08-15 by querying Crossref for each paper's
authoritative record BY TITLE (`api.crossref.org/works?query.bibliographic=...`) rather than by
testing which candidate DOI resolves -- a DOI that resolves only proves it points at *some* paper,
not at *this* paper. This script carries that adjudication as data so the edit is reviewable and
re-runnable instead of surviving only as scrollback (`CLAUDE.md` Section 0 rule 2).

WHAT THE ADJUDICATION FOUND -- and it changed the working hypothesis.

The reconcile had flagged all 14 because the AS-DRAFTED DOI matched the printed article number
(`Energy 300:131594` <-> `10.1016/j.energy.2024.131594`) while the hand-verified one did not. That
identity looked like evidence of correctness but is the opposite: the drafted DOI and the printed
volume:article were FABRICATED TOGETHER, so they agree with each other and with nothing else.
Crossref confirms the as-drafted DOI is wrong in **14 of 14** cases, and the printed volume is
wrong in 12 of them too -- so the citation metadata had to be corrected alongside the DOI, which
is the whole reason this script edits two fields per entry rather than one.

**But the hand-verified column was not perfect either.** For C7 (Xian 2022) BOTH candidates are
wrong: the true record is Applied Energy **323**:119555, while the copy carried an Applied Thermal
Engineering 2025 DOI -- a different paper. 13 of 14 to the hand-verified column, 1 to neither.
That single miss is the empirical case for `apply_policy()` quarantining every CHANGED row instead
of trusting the verified column wholesale: auto-applying would have written C7's error into the
thesis silently.

Inputs:  SOURCES.md at repo root (edited in place). The adjudication itself is the RESOLUTIONS
         table below -- evidence column quotes the Crossref record it came from. Stdlib only.

Run:  .\.venv\Scripts\python.exe -u .\scripts\apply_doi_conflict_resolutions.py --dry-run
      .\.venv\Scripts\python.exe -u .\scripts\apply_doi_conflict_resolutions.py

Outputs: results/sources_doi_resolutions_<stamp>.csv  -- the adjudication ledger, one row per entry
         results/sources_doi_resolutions_<stamp>.md   -- same, plus the evidence, for PROGRESS_LOG
"""

import argparse
import csv
import datetime
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(REPO_ROOT, "results")
SOURCES_PATH = os.path.join(REPO_ROOT, "SOURCES.md")

MARK = "  *[DOI verified 2026-08-15 — Crossref]*"

# entry, old DOI line (exact), new DOI line, old citation fragment, new citation fragment,
# winner, Crossref evidence.
# `winner` records WHO was right, which is the finding this table exists to preserve:
#   "verified" = the hand-checked copy; "neither" = both candidates wrong, Crossref supplied a third.
RESOLUTIONS = [
    dict(entry="A6", winner="verified",
         old_doi="- **DOI:** 10.1016/j.enconman.2024.118689 (verify article no. at cite)",
         new_doi="- **DOI:** 10.1016/j.enconman.2024.118805" + MARK,
         old_cite="*Energy Conversion and Management* 314:118689.",
         new_cite="*Energy Conversion and Management* 315:118805.",
         evidence="Crossref: Energy Conversion and Management 315, art. 118805, 2024"),
    dict(entry="A7", winner="verified",
         old_doi="- **DOI:** 10.1016/j.egyai.2023.100279 (verify at cite)",
         new_doi="- **DOI:** 10.1016/j.egyai.2023.100327" + MARK,
         old_cite="*Energy and AI* 14:100279.",
         new_cite="*Energy and AI* 15:100327 (issue year 2024; DOI suffix reads 2023 — online-first).",
         evidence="Crossref: Energy and AI 15, art. 100327, published 2024"),
    dict(entry="B1", winner="verified",
         old_doi="- **DOI:** 10.1016/j.solmat.2022.111852  (PII S0927024821004736 — verify vol/pages at cite)",
         new_doi="- **DOI:** 10.1016/j.solmat.2021.111432" + MARK,
         old_cite="*Solar Energy Materials and Solar Cells* 245:111852.",
         new_cite="*Solar Energy Materials and Solar Cells* 234:111432.",
         evidence="Crossref: Sol. Energy Mater. Sol. Cells 234, art. 111432, 2022. The PII "
                  "S0927024821004736 already in the entry encodes a 2021 submission, corroborating "
                  "the .2021. suffix against the drafted .2022."),
    dict(entry="B4", winner="verified",
         old_doi="- **DOI:** 10.1016/j.energy.2024.131594 (verify at cite)",
         new_doi="- **DOI:** 10.1016/j.energy.2024.131584" + MARK,
         old_cite="*Energy* 300:131594.",
         new_cite="*Energy* 301:131584.",
         evidence="Crossref: Energy 301, art. 131584, 2024"),
    dict(entry="B5", winner="verified",
         old_doi="- **DOI:** 10.1007/s11630-024-1990-4 (verify at cite)",
         new_doi="- **DOI:** 10.1007/s11630-024-2023-z" + MARK,
         old_cite="*J. Thermal Science* 33(5):1789–1802.",
         new_cite="*J. Thermal Science* 33(6):2221–2234.",
         evidence="Crossref: Journal of Thermal Science 33(6):2221-2234, 2024"),
    dict(entry="C1", winner="verified",
         old_doi="- **DOI:** 10.1016/j.icheatmasstransfer.2024.107837 (PII S0735193324009837 — verify no.)",
         new_doi="- **DOI:** 10.1016/j.icheatmasstransfer.2024.108221" + MARK,
         old_cite="*Int. Communications in Heat and Mass Transfer* 159:107837.",
         new_cite="*Int. Communications in Heat and Mass Transfer* 159:108221.",
         evidence="Crossref: Int. Comm. Heat Mass Transfer 159, art. 108221, 2024 — volume 159 was "
                  "already correct here, only the article number was wrong"),
    dict(entry="C7", winner="neither",
         old_doi="- **DOI:** 10.1016/j.apenergy.2022.119921 (verify at cite)",
         new_doi="- **DOI:** 10.1016/j.apenergy.2022.119555" + MARK,
         old_cite="*Applied Energy* 325:119921.",
         new_cite="*Applied Energy* 323:119555.",
         evidence="Crossref: Applied Energy 323, art. 119555, 2022. NEITHER candidate was right — "
                  "the drafted DOI gave 325:119921 and the hand-verified copy gave "
                  "10.1016/j.applthermaleng.2025.126209, an Applied Thermal Engineering 2025 paper. "
                  "This is the one row where the hand-verified column failed."),
    dict(entry="C9", winner="verified",
         old_doi="- **DOI:** 10.1016/j.icheatmasstransfer.2024.107345 (verify at cite)",
         new_doi="- **DOI:** 10.1016/j.icheatmasstransfer.2024.107734" + MARK,
         old_cite="*Int. Communications in Heat and Mass Transfer* 153:107345.",
         new_cite="*Int. Communications in Heat and Mass Transfer* 157:107734.",
         evidence="Crossref: Int. Comm. Heat Mass Transfer 157, art. 107734, 2024"),
    dict(entry="E3", winner="verified",
         old_doi="- **DOI:** 10.1016/j.enconman.2023.117387 (verify at cite)",
         new_doi="- **DOI:** 10.1016/j.enconman.2023.117551" + MARK,
         old_cite="Management* 292:117387.",
         new_cite="Management* 294:117551.",
         evidence="Crossref: Energy Conversion and Management 294, art. 117551, 2023"),
    dict(entry="F1", winner="verified",
         old_doi="- **DOI:** 10.1016/j.enconman.2024.118764 (verify at cite)",
         new_doi="- **DOI:** 10.1016/j.enconman.2023.118046" + MARK,
         old_cite="*Energy Conversion and Management* 309:118764.",
         new_cite="*Energy Conversion and Management* 301:118046.",
         evidence="Crossref: Energy Conversion and Management 301, art. 118046, published 2024 "
                  "(DOI suffix reads 2023 — online-first)"),
    dict(entry="G1", winner="verified",
         old_doi="- **DOI:** 10.1063/5.0085914 (verify at cite)",
         new_doi="- **DOI:** 10.1063/5.0086032" + MARK,
         old_cite="*AIP Conference Proceedings* 2445.",
         new_cite="*AIP Conference Proceedings* 2445:090009 (SOLARPACES 2020).",
         evidence="Crossref: AIP Conf. Proc. 2445, art. 090009, 2022, SOLARPACES 2020. The AIP "
                  "suffix encodes no article number, so no cross-check was possible before this."),
    dict(entry="G3", winner="verified",
         old_doi="- **DOI:** 10.1016/j.enconman.2023.117220 (verify at cite)",
         new_doi="- **DOI:** 10.1016/j.enconman.2023.116989" + MARK,
         old_cite="Conversion and Management* 290:117220.",
         new_cite="Conversion and Management* 284:116989.",
         evidence="Crossref: Energy Conversion and Management 284, art. 116989, 2023"),
    dict(entry="H2", winner="verified",
         old_doi="- **DOI:** 10.1016/j.energy.2024.131166 (verify at cite)",
         new_doi="- **DOI:** 10.1016/j.energy.2024.131548" + MARK,
         old_cite="*Energy* 296:131166.",
         new_cite="*Energy* 300:131548.",
         evidence="Crossref: Energy 300, art. 131548, 2024 (an SSRN preprint of the same title also "
                  "exists at 10.2139/ssrn.4696050 — cite the journal version)"),
    dict(entry="I7", winner="verified",
         old_doi="- **DOI:** 10.1016/j.enconman.2022.115342 (verify at cite)",
         new_doi="- **DOI:** 10.1016/j.enconman.2022.115366" + MARK,
         old_cite="*Energy Conversion and Management* 256:115342.",
         new_cite="*Energy Conversion and Management* 256:115366.",
         evidence="Crossref: Energy Conversion and Management 256, art. 115366, 2022 — volume 256 "
                  "was already correct, only the article number was wrong"),
    # ------------------------------------------------------------------------------------------
    # Batch 2 (same session): the three MISSING_DOI entries -- no DOI in EITHER file, so there was
    # nothing to adjudicate, only to find. Resolved by the same Crossref title query. These carry
    # their whole citation in the `cite` fields because the entries had no `- **DOI:**` line at all.
    # ------------------------------------------------------------------------------------------
    dict(entry="A4", winner="found (was MISSING_DOI)",
         old_doi="", new_doi="",
         old_cite="- Mammadov et al. 2026, *Topical Issues of Tech. Sci.* — 4 sCO₂ configs in solar tower at\n"
                  "  **fixed T_turb,in = 700 °C, P = 25 MPa, T_amb = 20 °C, Q = 120 MWth**; recompression\n"
                  "  η = **50.7%** (pre-comp 44.5, regen 37.7, simple 13%). Close to our 720 °C/25 MPa smoke\n"
                  "  test (η_calc 0.4926) → useful independent efficiency cross-check. DOI: (fetch on cite).",
         new_cite="Mammadov & Kalbaliyev (2026). \"Performance Assessment of Supercritical CO₂ Brayton Cycles\n"
                  "in Solar Power Tower Systems.\" *Topical Issues of Technical Sciences* 4(5), art. n19.\n"
                  "- **DOI:** 10.47390/ts-v4i5y2026n19" + MARK + "\n"
                  "- **Key numbers:** 4 sCO₂ configs in solar tower at **fixed T_turb,in = 700 °C, P = 25 MPa,\n"
                  "  T_amb = 20 °C, Q = 120 MWth**; recompression η = **50.7%** (pre-comp 44.5, regen 37.7,\n"
                  "  simple 13%). Close to our 720 °C/25 MPa smoke test (η_calc 0.4926) → useful independent\n"
                  "  efficiency cross-check.\n"
                  "- ⚠ **Venue caution (assessed 2026-08-15).** *Topical Issues of Technical Sciences*\n"
                  "  (Techscience.uz) is a low-profile regional outlet, not indexed in the major abstracting\n"
                  "  databases. The DOI is registered and resolves, but this entry should carry **no evidential\n"
                  "  weight on its own** — it is a soft corroboration of an efficiency magnitude already\n"
                  "  established by A0/A5/A6, never a validation anchor. Per §J's exclusion policy, it is kept\n"
                  "  (its number is plausible and it is used only as a cross-check) but explicitly discounted.",
         evidence="Crossref: Topical Issues of Technical Sciences 4(5), 2026, art. n19, "
                  "authors Mammadov & Kalbaliyev, DOI 10.47390/ts-v4i5y2026n19"),
    dict(entry="D1", winner="found (was MISSING_DOI)",
         old_doi="", new_doi="",
         old_cite="- **D1. Liu & Xiao 2023**, *Energy* 282 — \"MD investigation of thermophysical properties of\n"
                  "  molten salt with nanoparticles for solar energy application.\" General nano-in-salt MD\n"
                  "  method reference. [C]",
         new_cite="- **D1. Liu & Xiao 2023**, *Energy* 282:128732 — \"Molecular dynamics investigation of\n"
                  "  thermo-physical properties of molten salt with nanoparticles for solar energy\n"
                  "  application.\" General nano-in-salt MD method reference.\n"
                  "  DOI: 10.1016/j.energy.2023.128732" + MARK + "  [C]",
         evidence="Crossref: Energy 282, art. 128732, 2023, authors Liu & Xiao. Volume 282 was already "
                  "correct; the title in the entry was a paraphrase ('MD' for 'Molecular dynamics', "
                  "'thermophysical' for 'thermo-physical') and is now exact."),
    dict(entry="D3", winner="found (was MISSING_DOI)",
         old_doi="", new_doi="",
         old_cite="- **D3. Mirahmad et al. 2025**, *Nanomaterials* — review: NPs raise k but can lower c_p;\n"
                  "  **viscosity rise is the recurring drawback**. Framing citation for the pumping-power\n"
                  "  objective. (Review — use for framing, not primary quantitative data.) [C]",
         new_cite="- **D3. Mirahmad et al. 2025**, *Nanomaterials* 15(4):302 — \"Beyond Thermal Conductivity:\n"
                  "  A Review of Nanofluids for Enhanced Energy Storage and Heat Transfer.\" NPs raise k but\n"
                  "  can lower c_p; **viscosity rise is the recurring drawback**. Framing citation for the\n"
                  "  pumping-power objective. (Review — use for framing, not primary quantitative data.)\n"
                  "  DOI: 10.3390/nano15040302" + MARK + "  [C]",
         evidence="Crossref: Nanomaterials 15(4), art. 302, 2025, authors Mirahmad, Shankar Kumar, "
                  "Pato Doldán, Prieto Rios, Díez-Sierra. Title confirms it is a review, matching the "
                  "entry's existing 'use for framing, not primary data' caveat."),
    # Not a conflict: D2's DOI was FILLED from the verified copy and Crossref confirms it. The
    # lookup incidentally supplied the volume and title the entry had always lacked.
    dict(entry="D2", winner="verified (not a conflict — volume/title completed)",
         old_doi="", new_doi="",
         old_cite="- **D2. Yang et al. 2023**, *J. Energy Storage* — SiO₂ in KCl/NaCl/LiCl, Buckingham potential;",
         new_cite="- **D2. Yang et al. 2023**, *J. Energy Storage* 63:107015 — \"New insights into the\n"
                  "  heat capacity enhancement of nano-SiO₂ doped alkali metal chloride molten salt for\n"
                  "  thermal energy storage: A molecular dynamics study.\" SiO₂ in KCl/NaCl/LiCl, Buckingham potential;",
         evidence="Crossref: Journal of Energy Storage 63, art. 107015, 2023"),
]


def apply(text, dry_run):
    """Substitute every resolution's DOI line and citation fragment. Returns (text, rows).

    Each replacement asserts the old string occurs EXACTLY ONCE. A fragment that has drifted, or
    that matches two entries (both C1 and C9 sit in the same journal, so their citation fragments
    are only unique because the volume differs), must fail loudly rather than silently edit the
    wrong source -- this file feeds a thesis bibliography.
    """
    rows = []
    for res in RESOLUTIONS:
        status = []
        for field, old, new in (("doi", res["old_doi"], res["new_doi"]),
                                ("cite", res["old_cite"], res["new_cite"])):
            if not old:
                continue
            count = text.count(old)
            if count == 0:
                status.append("{}: ALREADY APPLIED or drifted".format(field))
                continue
            if count > 1:
                raise SystemExit(
                    "ambiguous {} fragment for {} -- matches {} times:\n  {}".format(
                        field, res["entry"], count, old))
            if not dry_run:
                text = text.replace(old, new, 1)
            status.append("{}: ok".format(field))
        rows.append({
            "entry": res["entry"],
            "winner": res["winner"],
            "old_doi": res["old_doi"].replace("- **DOI:** ", ""),
            "new_doi": res["new_doi"].replace("- **DOI:** ", "").replace(MARK, ""),
            "old_citation": res["old_cite"].replace("\n", " "),
            "new_citation": res["new_cite"].replace("\n", " "),
            "evidence": res["evidence"],
            "result": "; ".join(status),
        })
    return text, rows


def write_outputs(rows, stamp, commit, dry_run):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    base = os.path.join(RESULTS_DIR, "sources_doi_resolutions_{}".format(stamp))
    fields = ["entry", "winner", "old_doi", "new_doi", "old_citation", "new_citation",
              "evidence", "result"]
    with open(base + ".csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    conflicts = [r for r in rows if not r["winner"].startswith("verified (not")]
    neither = [r for r in conflicts if r["winner"] == "neither"]
    lines = [
        "# SOURCES.md — Crossref adjudication of the 14 DOI conflicts",
        "",
        "- Generated: {}".format(stamp),
        "- Script: `scripts/apply_doi_conflict_resolutions.py` @ commit `{}`".format(commit),
        "- Mode: {}".format("DRY RUN — SOURCES.md untouched" if dry_run else "APPLIED to SOURCES.md"),
        "- Method: Crossref `query.bibliographic` by paper TITLE, not by resolving either candidate.",
        "  A DOI that resolves only proves it points at *some* paper, not at *this* one.",
        "",
        "## Outcome",
        "",
        "| | count |",
        "|---|---|",
        "| conflicts adjudicated | {} |".format(len(conflicts)),
        "| hand-verified DOI correct | {} |".format(
            len([r for r in conflicts if r["winner"] == "verified"])),
        "| **neither candidate correct** | **{}** |".format(len(neither)),
        "| as-drafted DOI correct | 0 |",
        "",
        "The as-drafted DOI lost **14 of 14**, and the printed volume was wrong in 12 of those —",
        "so the volume:article line was corrected in the same pass, not just the DOI.",
        "",
        "## Per-entry",
        "",
        "| entry | winner | new DOI | new citation | evidence |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append("| {entry} | {winner} | `{new_doi}` | {new_citation} | {evidence} |".format(**row))
    lines.append("")
    with open(base + ".md", "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return base


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="report what would change without editing SOURCES.md")
    args = parser.parse_args()

    commit = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT).decode().strip()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    with open(SOURCES_PATH, "r", encoding="utf-8", newline="") as fh:
        text = fh.read()
    new_text, rows = apply(text, args.dry_run)
    if not args.dry_run:
        with open(SOURCES_PATH, "w", encoding="utf-8", newline="") as fh:
            fh.write(new_text)

    out = write_outputs(rows, stamp, commit, args.dry_run)
    for row in rows:
        print("  {:4s} {:12s} {}".format(row["entry"], row["winner"][:12], row["result"]))
    print("{} {} resolutions".format("would apply" if args.dry_run else "applied", len(rows)))
    print("wrote {}.csv / .md".format(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
