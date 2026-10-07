"""IEEG036 round-trip: per run, the BrainVision INT_32 digital values must equal the BDF digital values exactly
(read independently from the original data.bdf), the BrainVision resolution must equal the BDF gain, and MNE's physical
values of both files must agree up to the BDF constant offset (half LSB). Events: count vs evt.bdf.
Usage: python b2dryad_roundtrip036.py <extract_root> <bids>"""
import glob, json, os, re, sys
import numpy as np, mne
X, OUT = sys.argv[1], sys.argv[2]
mne.set_log_level("ERROR")
rep = json.load(open(os.path.join(OUT, "code", "conversion_report.json")))
root = glob.glob(os.path.join(X, "Dataset_*"))[0]


def bdf_digital(p):
    b = open(p, "rb").read(256); ns = int(b[252:256]); hb = open(p, "rb").read(256 + 256 * ns)
    o = 256 + ns * (16 + 80 + 8)
    f = lambda k: [float(hb[o + k * ns * 8 + i * 8:o + k * ns * 8 + (i + 1) * 8]) for i in range(ns)]
    pmin, pmax, dmin, dmax = f(0), f(1), f(2), f(3)
    spr = int(hb[o + 4 * ns * 8 + ns * 80:o + 4 * ns * 8 + ns * 80 + 8]); nrec = int(b[236:244])
    a = np.fromfile(p, dtype=np.uint8, offset=int(b[184:192])).reshape(nrec, ns, spr, 3).astype(np.int32)
    v = a[..., 0] | (a[..., 1] << 8) | (a[..., 2] << 16); v = np.where(v >= 1 << 23, v - (1 << 24), v)
    gain = [(pmax[i] - pmin[i]) / (dmax[i] - dmin[i]) for i in range(ns)]
    off = [pmin[i] - dmin[i] * gain[i] for i in range(ns)]
    return v.transpose(1, 0, 2).reshape(ns, -1), gain, off


bad = 0
for r in rep["runs"]:
    pid = "P%d" % int(r["sub"][4:]); sd = os.path.join(root, "Patients Data", "SEEG Data", pid, r["source_session"])
    v = os.path.join(OUT, r["sub"], "ieeg", f"{r['sub']}_task-visualawareness_run-{r['run']:02d}_ieeg.vhdr")
    dig, gain, off = bdf_digital(os.path.join(sd, "data.bdf"))
    bv = np.fromfile(v[:-5] + ".eeg", dtype="<i4").reshape(-1, dig.shape[0]).T
    res = [float(re.match(r"Ch\d+=[^,]*,[^,]*,([^,]*),", l).group(1)) for l in open(v, encoding="utf-8") if re.match(r"^Ch\d+=", l)]
    ok_dig = np.array_equal(dig, bv); ok_res = np.allclose(res, gain, rtol=0, atol=0)
    a = mne.io.read_raw_bdf(os.path.join(sd, "data.bdf"), preload=True).get_data()
    b = mne.io.read_raw_brainvision(v, preload=True).get_data()
    d = a - b - np.asarray(off)[:, None] * 1e-6
    ok_phys = float(np.max(np.abs(d))) < 1e-12
    ne = sum(1 for _ in open(v.replace("_ieeg.vhdr", "_events.tsv"))) - 1
    ok = ok_dig and ok_res and ok_phys and ne == r["n_events"]; bad += not ok
    print(r["sub"], r["run"], dig.shape, "digital_equal", ok_dig, "res_equal", ok_res, "phys_after_offset_maxdiff", float(np.max(np.abs(d))),
          "offset_uV", max(off), "events", ne, "OK" if ok else "BAD", flush=True)
print("ROUNDTRIP", len(rep["runs"]), "runs", bad, "bad"); sys.exit(1 if bad else 0)
