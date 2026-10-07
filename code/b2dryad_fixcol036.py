import csv,glob,os,sys
OUT=sys.argv[1]; n=0
for c in glob.glob(os.path.join(OUT,"sub-*","ieeg","*_channels.tsv")):
    rows=list(csv.reader(open(c),delimiter="\t")); h=rows[0]
    if "source_label" not in h: continue
    i=h.index("source_label")
    rows=[r[:i]+r[i+1:]+[r[i]] for r in rows]
    with open(c,"w",newline="") as f: csv.writer(f,delimiter="\t",lineterminator="\n").writerows(rows)
    n+=1
print("moved source_label to last column in",n,"files")
