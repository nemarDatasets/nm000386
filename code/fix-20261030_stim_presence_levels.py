"""fix-20261030: swap the stim_presence labels of StiPresence codes 2 and 3 (nm000386).

The release README defines Trial.StiPresence as 1 = staircase, 2 = "salient stimulus with fixed high contrast",
3 = "no stimulus", and the first conversion labelled 2 -> salient, 3 -> absent. The recorded trials contradict this:
in every run, all code-2 trials have Trial.Sti.Contrast 0 (1332 of 1332) and all code-3 trials a positive contrast
(720 of 720: 70, or 50 for sub-04), and the paper (Fang et al. 2024, eLife 13:RP89076) gives 20% no-grating and
10% salient trials, matching 36 vs 18 trials per 180-trial session for codes 2 vs 3. So code 2 is the absent
(zero-contrast) condition and code 3 the salient one. This script swaps the two labels in events.tsv after asserting
the contrast pattern. Usage: python fix-20261030_stim_presence_levels.py <bids_root>
"""
import csv, glob, os, sys

root = sys.argv[1]
swap = {"salient": "absent", "absent": "salient"}
n = 0
for ev in sorted(glob.glob(os.path.join(root, "sub-*/ieeg/*_events.tsv"))):
    rows = list(csv.DictReader(open(ev, newline=""), delimiter="\t"))
    header = list(rows[0].keys())
    for r in rows:
        sp = r["stim_presence"]
        if sp == "salient":
            assert r["contrast"] == "0", (ev, r)
        elif sp == "absent":
            assert r["contrast"] not in ("0", "n/a") and float(r["contrast"]) > 0, (ev, r)
        if sp in swap:
            r["stim_presence"] = swap[sp]
            n += 1
    with open(ev, "w", newline="") as f:
        w = csv.DictWriter(f, header, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
print("rows relabelled", n)
