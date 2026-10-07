"""IEEG036 inspection (in Job): extract zip, BDF headers, evt.bdf annotations, .mat string scan, deface renders.
Usage: python b2dryad_inspect036.py <zip> <extract_dir> <report_dir>"""
import glob, json, os, re, sys, zipfile, subprocess
import numpy as np, mne, scipy.io as sio
ZP, X, REP = sys.argv[1:4]
os.makedirs(REP, exist_ok=True)
if not os.path.exists(os.path.join(X, ".extracted")):
    zipfile.ZipFile(ZP).extractall(X); open(os.path.join(X, ".extracted"), "w").write("ok")
root = glob.glob(os.path.join(X, "Dataset_*"))[0]
out = {"bdf": [], "evt": [], "mat_strings": {}, "nii": []}
mne.set_log_level("ERROR")
for p in sorted(glob.glob(os.path.join(root, "Patients Data", "SEEG Data", "*", "*", "*.bdf"))):
    h = open(p, "rb").read(256).decode("latin1")
    rec = {"file": os.path.relpath(p, root), "patient": h[8:88].strip(), "recording": h[88:168].strip(), "startdate": h[168:176],
           "starttime": h[176:184], "header_bytes": h[184:192].strip(), "reserved": h[192:236].strip(), "nrec": h[236:244].strip(),
           "dur": h[244:252].strip(), "ns": h[252:256].strip()}
    try:
        r = mne.io.read_raw_bdf(p, preload=False)
        rec.update(sfreq=r.info["sfreq"], nchan=r.info["nchan"], n_times=r.n_times, ch=r.ch_names[:300],
                   n_annot=len(r.annotations), annot_sample=[(float(a["onset"]), a["description"]) for a in r.annotations[:15]])
        if p.endswith("evt.bdf"):
            rec["annot_counts"] = {d: int(c) for d, c in zip(*np.unique(r.annotations.description, return_counts=True))}
    except Exception as e:
        rec["mne_error"] = repr(e)
    (out["evt"] if p.endswith("evt.bdf") else out["bdf"]).append(rec)
    print(rec["file"], rec.get("sfreq"), rec.get("nchan"), rec.get("n_annot"), rec["startdate"], rec["patient"][:20], flush=True)
for p in sorted(glob.glob(os.path.join(root, "**", "*.mat"), recursive=True))[:200]:
    try:
        m = sio.loadmat(p, squeeze_me=True, struct_as_record=False)
    except NotImplementedError:
        out["mat_strings"][os.path.relpath(p, root)] = "v7.3"; continue
    strs = set()
    def walk(o, depth=0):
        if depth > 6: return
        if isinstance(o, str):
            if len(o) < 200: strs.add(o)
        elif hasattr(o, "_fieldnames"):
            for f in o._fieldnames: walk(getattr(o, f), depth + 1)
        elif isinstance(o, np.ndarray) and o.dtype == object:
            for v in o.ravel()[:50]: walk(v, depth + 1)
    for k, v in m.items():
        if not k.startswith("__"): walk(v)
    out["mat_strings"][os.path.relpath(p, root)] = sorted(strs)[:80]
for p in sorted(glob.glob(os.path.join(root, "Patients Data", "ImageData", "*", "*", "*.nii"))):
    rel = os.path.relpath(p, root); png = os.path.join(REP, "face_" + re.sub(r"[^A-Za-z0-9]+", "_", rel) + ".png")
    import nibabel as nib
    img = nib.load(p); out["nii"].append({"file": rel, "shape": list(img.shape), "zooms": [float(z) for z in img.header.get_zooms()[:3]],
                                          "descrip": img.header["descrip"].tobytes().rstrip(b"\0").decode("latin1"), "png": png})
    # reuse the lane's renderer (expects zip member; write a tiny wrapper zip-less call)
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    from scipy.ndimage import gaussian_filter, binary_opening
    d = np.asarray(nib.as_closest_canonical(img).dataobj, dtype=np.float32)
    ds = gaussian_filter(d, 1.5); thr = 0.15 * np.percentile(ds, 99.5); mk = binary_opening(ds > thr, iterations=2)
    fig, ax = plt.subplots(2, 3, figsize=(15, 10))
    for k, (name, axis, rev) in enumerate([("right", 0, False), ("left", 0, True), ("anterior", 1, True), ("posterior", 1, False), ("superior", 2, True), ("inferior", 2, False)]):
        mm = np.flip(mk, axis=axis) if rev else mk; hit = mm.any(axis=axis); depth = np.argmax(mm, axis=axis).astype(float); depth[~hit] = np.nan
        gy, gx = np.gradient(np.nan_to_num(depth, nan=np.nanmax(depth) if hit.any() else 0)); sh = 1 - np.clip(np.hypot(gx, gy) / 4, 0, 1); sh[~hit] = 0
        ax.flat[k].imshow(np.rot90(sh), cmap="gray"); ax.flat[k].set_title(name); ax.flat[k].axis("off")
    fig.suptitle(rel); fig.savefig(png, dpi=50); plt.close(fig)
    print("render", rel, flush=True)
json.dump(out, open(os.path.join(REP, "inspect036.json"), "w"), indent=1, default=str)
print("INSPECT_DONE")
