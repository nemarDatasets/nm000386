"""IEEG036 sourcedata privacy fix + NIfTI header audit.
 - MAT v5 text header 'Created on: Www Mmm DD HH:MM:SS YYYY' -> day 01 (weekday recomputed), same length; nothing else touched.
 - Prints NIfTI-1 header text fields (descrip/aux_file/db_name/intent_name) for every .nii/.nii.gz in the tree.
 - Updates MANIFEST.tsv 'change' column for MAT files.
Usage: python b2dryad_fixsrc036.py <bids> [apply]"""
import csv, datetime, glob, gzip, os, re, sys
OUT = sys.argv[1]; APPLY = len(sys.argv) > 2 and sys.argv[2] == "apply"
SD = os.path.join(OUT, "sourcedata", "dryad-p8cz8w9xp")
pat = re.compile(rb"Created on: (\w{3}) (\w{3}) +(\d{1,2}) (\d\d:\d\d:\d\d) (\d{4})")
n = 0; changed = set()
for f in sorted(glob.glob(os.path.join(SD, "**", "*.mat"), recursive=True)):
    with open(f, "r+b") as fh:
        h = fh.read(116); m = pat.search(h)
        if not m: print("NO_DATE", f, h[:116]); continue
        mon = m.group(2).decode(); yr = int(m.group(5))
        d1 = datetime.date(yr, datetime.datetime.strptime(mon, "%b").month, 1)
        new = f"Created on: {d1.strftime('%a')} {mon} {'01'.rjust(len(m.group(3)))} {m.group(4).decode()} {yr}".encode()
        if len(m.group(3)) == 1: new = f"Created on: {d1.strftime('%a')} {mon}  1 {m.group(4).decode()} {yr}".encode()
        old = m.group(0)
        new = new[:len(old)].ljust(len(old))
        assert len(new) == len(old)
        if n < 3: print(old, "->", new)
        if APPLY and new != old:
            h2 = h[:m.start()] + new + h[m.end():]; fh.seek(0); fh.write(h2); changed.add(os.path.relpath(f, SD))
        n += 1
print("MAT headers", n, "changed", len(changed))
for f in sorted(glob.glob(os.path.join(OUT, "**", "*.nii*"), recursive=True)):
    b = (gzip.open(f) if f.endswith(".gz") else open(f, "rb")).read(348)
    print("NIFTI", os.path.relpath(f, OUT), "descrip=%r aux=%r db=%r intent=%r" % (b[148:228].rstrip(b"\0"), b[228:252].rstrip(b"\0"), b[4:22].rstrip(b"\0"), b[328:344].rstrip(b"\0")))
if APPLY and changed:
    mf = os.path.join(SD, "MANIFEST.tsv"); rows = list(csv.reader(open(mf), delimiter="\t"))
    for r in rows[1:]:
        if r[0] in changed: r[3] = "MAT header creation date: day-of-month set to 01 (weekday recomputed)"
    with open(mf, "w", newline="") as fo: csv.writer(fo, delimiter="\t", lineterminator="\n").writerows(rows)
    print("MANIFEST updated")
