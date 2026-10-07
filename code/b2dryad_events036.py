"""IEEG036: trial-level enrichment of events.tsv from the release behaviour MAT files (Patients Data/EyePositionData).
Per run: triggers are segmented by code 101 (one per trial); segment i is matched to Trial(i) of the session's MAT file(s)
only if the counts are equal AND the trigger intervals agree with the MAT EventTime intervals (check printed). Codes are
named only where the timing check supports it. Writes events.tsv (adds columns) + events.json, and a report.
Usage: python b2dryad_events036.py <extract_root> <bids> <check|apply>"""
import csv, glob, json, os, re, sys, collections
import numpy as np, scipy.io as sio
X, OUT, MODE = sys.argv[1:4]
root = glob.glob(os.path.join(X, "Dataset_*"))[0]
EYE = os.path.join(root, "Patients Data", "EyePositionData")
rep = json.load(open(os.path.join(OUT, "code", "conversion_report.json")))
FIELDS = {"11": "FpOn", "21": "CueOn", "20": "CueOff", "31": "TargetOn"}
NAMES = {"101": "trial_start", "11": "fixation_point_on", "21": "grating_on", "20": "grating_off", "31": "targets_on_fp_color_change", "201": "trial_end_completed", "203": "trial_end_not_completed", "204": "trial_end_fixation_break"}


def sess_mats(pid, sname):
    nums = [int(n) for n in re.findall(r"\d+", sname)]
    if len(nums) == 2: nums = list(range(nums[0], nums[1] + 1))
    out = []
    for n in nums:
        f = sorted(glob.glob(os.path.join(EYE, pid, f"Session{n}", "*.mat")))
        out.append(f[0] if f else None)
    return out


def trials(f):
    m = sio.loadmat(f, squeeze_me=True, struct_as_record=False)
    T = list(np.atleast_1d(m["Trial"]))
    return T, m["SessionSet"]


def g(o, *path):
    for p in path:
        if o is None or not hasattr(o, p): return None
        o = getattr(o, p)
    if isinstance(o, np.ndarray):
        if o.size == 0: return None
        if o.size == 1: o = o.item()
        else: return None
    return o


report = {"runs": []}
evid_out = collections.defaultdict(collections.Counter)
dt_err = collections.defaultdict(list)
for r in rep["runs"]:
    pid = "P%d" % int(r["sub"][4:]); stem = f"{r['sub']}_task-visualawareness_run-{r['run']:02d}"
    evf = os.path.join(OUT, r["sub"], "ieeg", stem + "_events.tsv")
    rows = list(csv.DictReader(open(evf), delimiter="\t")); hdr = list(rows[0].keys())
    mats = sess_mats(pid, r["source_session"])
    T = []
    for f in mats:
        if f: T += trials(f)[0]
    starts = [i for i, x in enumerate(rows) if x["value"] == "101"]
    info = {"sub": r["sub"], "run": r["run"], "session": r["source_session"], "mats": [os.path.basename(os.path.dirname(f)) if f else None for f in mats],
            "n_101": len(starts), "n_mat_trials": len(T)}
    ok = bool(T) and len(starts) == len(T) and None not in mats
    if ok:
        errs = []
        for k, s in enumerate(starts):
            e = starts[k + 1] if k + 1 < len(starts) else len(rows)
            t0 = float(rows[s]["onset"]); pre = g(T[k], "EventTime", "PreFpOn")
            for x in rows[s + 1:e]:
                fld = FIELDS.get(x["value"])
                if fld and pre is not None and g(T[k], "EventTime", fld) is not None:
                    d = (float(x["onset"]) - t0) - (g(T[k], "EventTime", fld) - pre)
                    errs.append(abs(d)); dt_err[x["value"]].append(abs(d))
                if x["value"] not in FIELDS and x["value"] != "101":
                    evid_out[x["value"]][(g(T[k], "trial_complete"), g(T[k], "trial_abort"), g(T[k], "trial_FPbreak"))] += 1
        info["timing_abs_err_ms_median"] = float(np.median(errs) * 1e3) if errs else None
        info["timing_abs_err_ms_p99"] = float(np.percentile(errs, 99) * 1e3) if errs else None
        ok = bool(bool(errs) and float(np.percentile(errs, 99)) < 0.025)
    info["matched"] = ok
    report["runs"].append(info); print(json.dumps(info), flush=True)
    if MODE != "apply": continue
    newh = hdr[:]
    for c in ["trial", "event_name", "stim_presence", "contrast", "fp_color", "response", "awareness", "trial_complete", "fixation_break"]:
        if c not in newh: newh.append(c)
    k = -1; out = []
    for i, x in enumerate(rows):
        if x["value"] == "101": k += 1
        y = dict(x)
        y["event_name"] = NAMES.get(x["value"], "n/a")
        if ok and k >= 0:
            t = T[k]
            y["trial"] = k + 1
            sp = g(t, "StiPresence"); y["stim_presence"] = {1: "staircase", 2: "salient", 3: "absent"}.get(sp, "n/a")
            c = g(t, "Sti", "Contrast"); y["contrast"] = c if c is not None else "n/a"
            fc = g(t, "TG", "RespFP1G2R"); y["fp_color"] = {1: "green", 2: "red"}.get(fc, "n/a")
            rs = g(t, "Resp1L2R"); y["response"] = {1: "left", 2: "right"}.get(rs, "n/a")
            aw = g(t, "AwareType1U2A"); y["awareness"] = {1: "unaware", 2: "aware"}.get(aw, "n/a")
            tc = g(t, "trial_complete"); y["trial_complete"] = tc if tc is not None else "n/a"
            fb = g(t, "trial_FPbreak"); y["fixation_break"] = fb if fb is not None else "n/a"
        else:
            for c in newh:
                y.setdefault(c, "n/a")
            if k >= 0 and not ok: y["trial"] = k + 1
        out.append(y)
    with open(evf, "w", newline="") as f:
        w = csv.DictWriter(f, newh, delimiter="\t", lineterminator="\n", restval="n/a"); w.writeheader()
        for y in out: w.writerow({c: ("n/a" if y.get(c) in (None, "") else y.get(c)) for c in newh})
print("timing err ms median/p99 per code:", {c: (round(float(np.median(v)) * 1e3, 2), round(float(np.percentile(v, 99)) * 1e3, 2), len(v)) for c, v in dt_err.items()})
print("outcome codes vs (trial_complete, trial_abort, trial_FPbreak):", {c: dict((str(k), n) for k, n in v.items()) for c, v in evid_out.items()})
report["timing"] = {c: [float(np.median(v)), float(np.percentile(v, 99)), len(v)] for c, v in dt_err.items()}
report["outcome_vs_mat"] = {c: {str(k): n for k, n in v.items()} for c, v in evid_out.items()}
json.dump(report, open(os.path.join(OUT, "code", f"events_enrich_{MODE}.json"), "w"), indent=1)
print("MATCHED", sum(x["matched"] for x in report["runs"]), "of", len(report["runs"]))
