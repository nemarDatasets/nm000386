"""IEEG036 validator fixes (metadata only; no sample bytes touched):
 - duplicate BDF channel labels (sub-04: 'LDELT1' at Ch1 and Ch251, different data) -> later occurrences renamed
   '<label>_ch<idx>' in vhdr + channels.tsv; original label kept in channels.tsv column source_label;
 - HardwareFilters as schema object; electrodes.tsv/coordsystem (no coordinates released: x/y/z n/a);
 - README/channels note on the BDF half-LSB offset.
Usage: python b2dryad_fix036.py <bids>"""
import csv, glob, json, os, re, sys, shutil
OUT = sys.argv[1]
ren = 0
for v in sorted(glob.glob(os.path.join(OUT, "sub-*", "ieeg", "*_ieeg.vhdr"))):
    L = open(v, encoding="utf-8").read().split("\n"); seen = {}; names = []
    for i, l in enumerate(L):
        m = re.match(r"^Ch(\d+)=([^,]*),(.*)$", l)
        if not m: continue
        idx, lab = int(m.group(1)), m.group(2)
        new = lab if lab not in seen else f"{lab}_ch{idx}"
        if new != lab: L[i] = f"Ch{idx}={new},{m.group(3)}"; ren += 1
        seen[lab] = 1; names.append((new, lab))
    open(v, "w", encoding="utf-8").write("\n".join(L))
    c = v.replace("_ieeg.vhdr", "_channels.tsv"); rows = list(csv.reader(open(c), delimiter="\t"))
    h = rows[0]
    if "source_label" not in h: h.insert(1, "source_label")
    out = [h]
    for (new, lab), r in zip(names, rows[1:]):
        assert r[0] == lab, (c, r[0], lab)
        out.append([new, lab] + r[1:])
    with open(c, "w", newline="") as f: csv.writer(f, delimiter="\t", lineterminator="\n").writerows(out)
    j = v.replace("_ieeg.vhdr", "_ieeg.json"); d = json.load(open(j))
    d["HardwareFilters"] = {"BandpassFilter": {"LowCutoff": 1, "HighCutoff": 250}, "NotchFilter": {"Frequency": 50}}
    json.dump(d, open(j, "w"), indent=2, ensure_ascii=False)
for sd in sorted(glob.glob(os.path.join(OUT, "sub-*"))):
    sub = os.path.basename(sd); allc = []
    for c in sorted(glob.glob(os.path.join(sd, "ieeg", "*_channels.tsv"))):
        for r in list(csv.DictReader(open(c), delimiter="\t")):
            if r["type"] == "SEEG" and r["name"] not in allc: allc.append(r["name"])
    with open(os.path.join(sd, "ieeg", f"{sub}_space-Other_electrodes.tsv"), "w", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n"); w.writerow(["name", "x", "y", "z", "size"])
        for n in allc: w.writerow([n, "n/a", "n/a", "n/a", "n/a"])
    json.dump({"SpatialReference": "none: no electrode coordinates are included in the source release (only defaced MRI/CT)"},
              open(os.path.join(sd, "ieeg", f"{sub}_space-Other_electrodes.json"), "w"), indent=2)
    json.dump({"iEEGCoordinateSystem": "Other", "iEEGCoordinateUnits": "n/a",
               "iEEGCoordinateSystemDescription": "No electrode coordinates are released; electrodes.tsv lists the SEEG contact names with x/y/z = n/a. Coordinates can be derived from the defaced T1w and the CT in sourcedata."},
              open(os.path.join(sd, "ieeg", f"{sub}_space-Other_coordsystem.json"), "w"), indent=2)
cj = os.path.join(OUT, "task-visualawareness_channels.json"); d = json.load(open(cj))
d["source_label"] = {"Description": "Channel label in the BDF header, verbatim. Where a label occurs twice in one file (sub-04: LDELT1 at channels 1 and 251, different signals) the later occurrence is renamed <label>_ch<index>."}
json.dump(d, open(cj, "w"), indent=2, ensure_ascii=False)
r = os.path.join(OUT, "README"); t = open(r).read()
if "half" not in t:
    t = t.replace("  the BDF gain: physical values are identical to the BDF (lossless; checked by round-trip).",
                  "  the BDF gain. The BDF digital range is asymmetric (-8388608..8388607 for a symmetric physical range), so the BDF\n"
                  "  physical value = digital x gain + half a digital step (about 0.045 µV); that constant is not representable in\n"
                  "  BrainVision and is dropped. The digital values are exact (checked by round-trip).\n"
                  "- sub-04: the BDF has the label LDELT1 twice (channels 1 and 251, different signals); channel 251 is named LDELT1_ch251\n"
                  "  (original label in channels.tsv column source_label).")
    open(r, "w").write(t)
shutil.copy(__file__, os.path.join(OUT, "code"))
print("FIXED renamed", ren)
