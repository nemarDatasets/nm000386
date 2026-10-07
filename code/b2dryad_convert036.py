"""IEEG036 (Dryad doi:10.5061/dryad.p8cz8w9xp; Fang et al. 2024 eLife 89076) -> iEEG-BIDS.

Raw sEEG (Neuracle, BDF 24-bit, 1 kHz) per session: data.bdf + evt.bdf (BDF+C annotations 'Trigger-In:<code>').
BDF is not an iEEG-BIDS format, so each data.bdf is written as BrainVision with BinaryFormat=INT_32 holding the exact
BDF digital values and per-channel Resolution = BDF gain (physical/digital); requires zero offset (checked), so
physical = digital * resolution exactly as in the BDF. Events: evt.bdf annotation onsets used as data latencies
(Neuracle's own reader readbdfdata.m convention); header start times of evt/data differ by 0-1 s (1-s resolution).
Dates: year/month kept, day set to 01. Images: defaced T1w (deface checked) -> anat; CT -> sourcedata only (no raw CT
suffix in BIDS); P5 CT excluded (deface not verifiable). sourcedata: release files with initials/dates removed from
names and BDF header day set to 01 (header-only), manifest of original sha256.
Usage: python b2dryad_convert036.py <extract_root> <bids_root>
"""
import csv, glob, gzip, hashlib, json, os, re, shutil, sys
import numpy as np, mne

X, OUT = sys.argv[1], sys.argv[2]
ROOT = glob.glob(os.path.join(X, "Dataset_*"))[0]
P = os.path.join(ROOT, "Patients Data")
mne.set_log_level("ERROR")
os.makedirs(OUT, exist_ok=True)
EXCLUDE_CT = {"P5"}


def wtsv(p, h, rows):
    with open(p, "w", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n"); w.writerow(h)
        for r in rows: w.writerow(["n/a" if v is None else v for v in r])


def wjson(p, o):
    with open(p, "w") as f: json.dump(o, f, indent=2, ensure_ascii=False); f.write("\n")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 24), b""): h.update(c)
    return h.hexdigest()


def bdf_header(p):
    b = open(p, "rb").read(256); ns = int(b[252:256]); hb = open(p, "rb").read(256 + 256 * ns)
    g = lambda off, w: [hb[256 + off * ns + i * w: 256 + off * ns + (i + 1) * w].decode("latin1").strip() for i in range(ns)]
    labels = g(0, 16); dim = [hb[256 + ns * (16 + 80) + i * 8:256 + ns * (16 + 80) + (i + 1) * 8].decode().strip() for i in range(ns)]
    o = 256 + ns * (16 + 80 + 8)
    pmin = [float(hb[o + i * 8:o + (i + 1) * 8]) for i in range(ns)]; o += ns * 8
    pmax = [float(hb[o + i * 8:o + (i + 1) * 8]) for i in range(ns)]; o += ns * 8
    dmin = [float(hb[o + i * 8:o + (i + 1) * 8]) for i in range(ns)]; o += ns * 8
    dmax = [float(hb[o + i * 8:o + (i + 1) * 8]) for i in range(ns)]; o += ns * 8
    o += ns * 80
    spr = [int(hb[o + i * 8:o + (i + 1) * 8]) for i in range(ns)]
    return dict(raw=b, ns=ns, labels=labels, dim=dim, pmin=pmin, pmax=pmax, dmin=dmin, dmax=dmax, spr=spr,
                nrec=int(b[236:244]), dur=float(b[244:252]), hbytes=int(b[184:192]), date=b[168:176].decode(), time=b[176:184].decode())


def read_digital(p, h):
    assert len(set(h["spr"])) == 1
    s = h["spr"][0]; ns = h["ns"]
    a = np.fromfile(p, dtype=np.uint8, offset=h["hbytes"])
    assert a.size == h["nrec"] * ns * s * 3, (p, a.size)
    a = a.reshape(h["nrec"], ns, s, 3).astype(np.int32)
    v = a[..., 0] | (a[..., 1] << 8) | (a[..., 2] << 16)
    v = np.where(v >= 1 << 23, v - (1 << 24), v)
    return v.transpose(1, 0, 2).reshape(ns, -1)  # (ns, n_times)


def chtype(n):
    if "DELT" in n: return "MISC"
    return "SEEG"


parts, report = [], {"runs": []}
for pdir in sorted(glob.glob(os.path.join(P, "SEEG Data", "P*")), key=lambda s: int(re.sub(r"\D", "", os.path.basename(s)))):
    pid = os.path.basename(pdir); sub = f"sub-{int(pid[1:]):02d}"
    sess = sorted(glob.glob(os.path.join(pdir, "Session*")), key=lambda s: int(re.findall(r"\d+", os.path.basename(s))[0]))
    od = os.path.join(OUT, sub, "ieeg"); os.makedirs(od, exist_ok=True)
    scans = []
    for ri, sd in enumerate(sess, 1):
        src = os.path.join(sd, "data.bdf"); h = bdf_header(src)
        gain = [(h["pmax"][i] - h["pmin"][i]) / (h["dmax"][i] - h["dmin"][i]) for i in range(h["ns"])]
        off = [h["pmin"][i] - h["dmin"][i] * gain[i] for i in range(h["ns"])]
        assert max(abs(o) for o in off) < 1e-6 * max(abs(x) for x in h["pmax"]), (src, max(off))
        sf = h["spr"][0] / h["dur"]
        dig = read_digital(src, h)
        stem = f"{sub}_task-visualawareness_run-{ri:02d}"
        np.ascontiguousarray(dig.T).astype("<i4").tofile(os.path.join(od, stem + "_ieeg.eeg"))
        units = [("µV" if d.lower() in ("uv", "µv") else d) for d in h["dim"]]
        vh = ["Brain Vision Data Exchange Header File Version 1.0", "; b2dryad_convert036.py: BDF digital values (INT_32), resolution = BDF gain", "",
              "[Common Infos]", "Codepage=UTF-8", f"DataFile={stem}_ieeg.eeg", f"MarkerFile={stem}_ieeg.vmrk", "DataFormat=BINARY",
              "DataOrientation=MULTIPLEXED", f"NumberOfChannels={h['ns']}", f"SamplingInterval={1e6 / sf!r}", "", "[Binary Infos]", "BinaryFormat=INT_32", "",
              "[Channel Infos]"] + [f"Ch{i + 1}={h['labels'][i].replace(',', chr(92) + '1')},,{gain[i]!r},{units[i]}" for i in range(h["ns"])]
        open(os.path.join(od, stem + "_ieeg.vhdr"), "w", encoding="utf-8").write("\n".join(vh) + "\n")
        ev = mne.io.read_raw_bdf(os.path.join(sd, "evt.bdf")).annotations
        vm = ["Brain Vision Data Exchange Marker File, Version 1.0", "", "[Common Infos]", "Codepage=UTF-8", f"DataFile={stem}_ieeg.eeg", "", "[Marker Infos]", "Mk1=New Segment,,1,1,0"]
        rows = []
        for a in ev:
            code = a["description"].split(":")[-1]; smp = int(round(a["onset"] * sf))
            rows.append(["%.3f" % a["onset"], "%.3f" % a["duration"], f"trigger_{code}", int(code) if code.isdigit() else code, smp, a["description"]])
            vm.append(f"Mk{len(vm) - 6}=Stimulus,S{code:>3},{smp + 1},1,0")
        open(os.path.join(od, stem + "_ieeg.vmrk"), "w", encoding="utf-8").write("\n".join(vm) + "\n")
        wtsv(os.path.join(od, stem + "_events.tsv"), ["onset", "duration", "trial_type", "value", "sample", "source_annotation"], rows)
        wtsv(os.path.join(od, stem + "_channels.tsv"), ["name", "type", "units", "low_cutoff", "high_cutoff", "sampling_frequency", "reference", "status", "notes"],
             [[h["labels"][i], chtype(h["labels"][i]), units[i], 1, 250, sf, "white-matter contact (per article)", "good",
               "label suggests deltoid EMG; type not documented in release" if "DELT" in h["labels"][i] else "n/a"] for i in range(h["ns"])])
        nseeg = sum(chtype(n) == "SEEG" for n in h["labels"])
        wjson(os.path.join(od, stem + "_ieeg.json"), {
            "TaskName": "visualawareness",
            "TaskDescription": "Visual awareness task with saccadic report: a near-threshold (staircase), salient or absent grating is shown; after a 600 ms delay the fixation colour cues a saccade, and subjects report aware/unaware (Fang et al. 2024).",
            "Manufacturer": "NEURACLE Technology Co., Ltd., Beijing, China", "SamplingFrequency": sf, "PowerLineFrequency": 50,
            "SoftwareFilters": "n/a", "HardwareFilters": {"Description": "Per article: filtered between 1 and 250 Hz and notched at 50 Hz"},
            "iEEGReference": "a site in white matter (article)", "ElectrodeManufacturer": "SINOVATION MEDICAL TECHNOLOGY CO., LTD., Beijing, China",
            "iEEGElectrodeInfo": "Depth electrodes with 8-20 sites; 0.8 mm diameter, 2 mm length, 1.5 mm spacing (article)",
            "RecordingType": "continuous", "RecordingDuration": dig.shape[1] / sf, "SEEGChannelCount": nseeg, "MiscChannelCount": h["ns"] - nseeg,
            "TriggerChannelCount": 0, "InstitutionName": "Department of Neurosurgery, PLA General Hospital, Beijing"})
        dd, mm, yy = h["date"].split("."); hh, mi, ss = h["time"].split(".")
        scans.append([f"ieeg/{stem}_ieeg.vhdr", f"20{yy}-{mm}-01T{hh}:{mi}:{ss}", os.path.basename(sd)])
        report["runs"].append({"sub": sub, "run": ri, "source_session": os.path.basename(sd), "nchan": h["ns"], "n_times": int(dig.shape[1]), "sfreq": sf,
                               "n_events": len(rows), "sha256_source_data_bdf": sha(src)})
        print(sub, ri, os.path.basename(sd), h["ns"], dig.shape, len(rows), flush=True)
    wtsv(os.path.join(OUT, sub, f"{sub}_scans.tsv"), ["filename", "acq_time", "source_session"], scans)
    t1 = glob.glob(os.path.join(P, "ImageData", pid, "MRI", "*.nii"))
    if t1:
        os.makedirs(os.path.join(OUT, sub, "anat"), exist_ok=True)
        with open(t1[0], "rb") as fi, open(os.path.join(OUT, sub, "anat", f"{sub}_T1w.nii.gz"), "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as fo: shutil.copyfileobj(fi, fo)
        wjson(os.path.join(OUT, sub, "anat", f"{sub}_T1w.json"), {"Description": "Preoperative T1 MRI, defaced by the data authors (release file *_deface.nii); deface visually checked before deposit."})
    parts.append([sub, pid, "M", "n/a", len(sess)])
wtsv(os.path.join(OUT, "participants.tsv"), ["participant_id", "source_id", "sex", "age", "n_runs"], parts)
# sourcedata (identifier-free names; BDF headers day -> 01)
SD = os.path.join(OUT, "sourcedata", "dryad-p8cz8w9xp"); man = []
def put(src, rel, fix_bdf=False):
    dst = os.path.join(SD, rel); os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copyfile(src, dst)
    if fix_bdf:
        with open(dst, "r+b") as f:
            hdr = bytearray(f.read(256)); dmy = hdr[168:176].decode(); hdr[168:170] = b"01"
            rec = hdr[88:168].decode("latin1"); rec2 = re.sub(r"Startdate \d\d-", "Startdate 01-", rec); hdr[88:168] = rec2.encode("latin1").ljust(80)
            f.seek(0); f.write(bytes(hdr))
    man.append([rel, os.path.relpath(src, ROOT).count("/") and re.sub(r"\d{6}_\d{4}_[a-z]+_", "<date>_<time>_<initials>_", re.sub(r"[a-z]+_VisualAwareData", "<initials>_VisualAwareData", os.path.relpath(src, ROOT))), sha(src), "header day-of-month set to 01" if fix_bdf else "unchanged"])
for pdir in sorted(glob.glob(os.path.join(P, "SEEG Data", "P*"))):
    pid = os.path.basename(pdir)
    for sd in glob.glob(os.path.join(pdir, "Session*")):
        for fn in ("data.bdf", "evt.bdf"): put(os.path.join(sd, fn), f"Patients/{pid}/sEEG/{os.path.basename(sd)}/{fn}", fix_bdf=True)
for p in glob.glob(os.path.join(P, "ImageData", "*", "*", "*.nii")):
    pid, kind = p.split(os.sep)[-3], p.split(os.sep)[-2]
    if kind == "CT" and pid in EXCLUDE_CT: man.append([None, f"Patients Data/ImageData/{pid}/CT/(excluded)", sha(p), "EXCLUDED: deface not verifiable; obtain from Dryad"]); continue
    put(p, f"Patients/{pid}/{kind}/{os.path.basename(p)}")
for p in glob.glob(os.path.join(P, "EyePositionData", "*", "*", "*.mat")):
    pid, ses = p.split(os.sep)[-3], p.split(os.sep)[-2]; side = "left" if p.endswith("_left.mat") else "right"
    put(p, f"Patients/{pid}/EyePosition/{ses}_VisualAware_{side}.mat")
hc = sorted(glob.glob(os.path.join(ROOT, "Healthy Control Data", "*")))
for k, d in enumerate(hc, 1):
    for j, p in enumerate(sorted(glob.glob(os.path.join(d, "*.mat"))), 1):
        put(p, f"HealthyControls/C{k:02d}/Session{j}_VisualAware_{'left' if p.endswith('_left.mat') else 'right'}.mat")
wtsv(os.path.join(SD, "MANIFEST.tsv"), ["path_in_sourcedata", "original_path_pattern (initials/dates redacted)", "sha256_of_original_release_file", "change"], man)
os.makedirs(os.path.join(OUT, "code"), exist_ok=True); shutil.copy(__file__, os.path.join(OUT, "code"))
json.dump(report, open(os.path.join(OUT, "code", "conversion_report.json"), "w"), indent=1)
print("DONE")
