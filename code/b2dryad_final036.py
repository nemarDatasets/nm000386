"""IEEG036 final metadata enrichment (text only; run AFTER b2dryad_events036.py apply and b2dryad_fixsrc036.py apply).
Sources: Fang et al. 2024 eLife 13:RP89076 (PMC10945701 full text: Methods 'Data acquisition', 'Experimental task',
'Data analysis'; Additional information 'Ethics'; 'Funding Information'); Dryad README (release).
Usage: python b2dryad_final036.py <bids>"""
import csv, json, os, shutil, sys
OUT = sys.argv[1]


def rj(p): return json.load(open(p))
def wj(p, o):
    with open(p, "w") as f: json.dump(o, f, indent=2, ensure_ascii=False); f.write("\n")


dd = rj(os.path.join(OUT, "dataset_description.json"))
dd["EthicsApprovals"] = ["All subjects provided informed consent to participate in this study. The Ethics Committee of Chinese PLA General Hospital "
                         "approved the experimental procedures (approval numbers S2022-457-01). [Fang et al. 2024, eLife 13:RP89076, "
                         "doi:10.7554/eLife.89076; Additional information, Ethics (Human subjects), identical in Methods, Data acquisition]"]
dd["Funding"] = ["Ministry of Science and Technology of the People's Republic of China STI2030-Major Projects+2021ZD0204300 to Mingsha Zhang",
                 "National Natural Science Foundation of China 32061143004 to Mingsha Zhang",
                 "National Natural Science Foundation of China 32030045 to Mingsha Zhang",
                 "State Key Laboratory of Cognitive Neuroscience and Learning Open Research Fund CNLZD2202 to Yongzheng Han"]
dd["Acknowledgements"] = "We thank the participants for volunteering to take part in the study. (Fang et al. 2024, Acknowledgements)"
dd["GeneratedBy"] = [{"Name": "NEMAR iEEG batch-2 conversion (b2dryad_*036.py)",
                      "Description": "BDF -> BrainVision INT_32 with the exact BDF digital values and gains; events from evt.bdf, enriched per trial "
                                     "from the release behaviour MAT files; dates day -> 01; code in code/."}]
dd["Keywords"] = ["sEEG", "stereo-EEG", "intracranial EEG", "visual awareness", "consciousness", "prefrontal cortex", "saccade", "epilepsy"]
wj(os.path.join(OUT, "dataset_description.json"), dd)

# participants: per-patient facts the article gives
P = os.path.join(OUT, "participants.tsv")
rows = list(csv.DictReader(open(P), delimiter="\t"))
bil = {"P1", "P5", "P6"}
for r in rows:
    r["implantation"] = "bilateral" if r["source_id"] in bil else "unilateral"
    r["grating_side"] = "right" if r["source_id"] in bil else "n/a"
    r["max_response_duration_ms"] = "5000" if r["source_id"] == "P6" else "2000"
    r["diagnosis"] = "drug-resistant epilepsy"
h = ["participant_id", "source_id", "sex", "age", "diagnosis", "implantation", "grating_side", "max_response_duration_ms", "n_runs"]
with open(P, "w", newline="") as f:
    w = csv.DictWriter(f, h, delimiter="\t", lineterminator="\n", extrasaction="ignore"); w.writeheader(); w.writerows(rows)
pj = rj(os.path.join(OUT, "participants.json"))
pj["diagnosis"] = {"Description": "Article, Methods 'Data acquisition': 'Six adult patients with drug-resistant epilepsy'"}
pj["implantation"] = {"Description": "Article, 'Experimental task': 'For patients 1, 5, and 6, the electrodes were implanted in both hemispheres'; the other patients had one hemisphere implanted (side not stated in the article).",
                      "Levels": {"bilateral": "electrodes in both hemispheres", "unilateral": "electrodes in one hemisphere"}}
pj["grating_side"] = {"Description": "Screen side of the grating. Article: opposite to the implanted hemisphere; 'For patients 1, 5, and 6 ... the grating is set on the right side.' For unilateral patients the side is not stated in the article (it is recorded per trial in the behaviour MAT files, Trial.Sti.LocX)."}
pj["max_response_duration_ms"] = {"Description": "Maximum saccadic response window used for trial exclusion in the article ('2000ms for most patients, 5000ms for patient 6')", "Units": "ms"}
pj["n_runs"] = {"Description": "Number of recordings (release 'SessionN' folders); stored as runs. Article: 'each patient completed five to seven sessions' (P3 has 12 session folders in the release; P5 'Session6-7' is one recording of two sessions)."}
wj(os.path.join(OUT, "participants.json"), pj)

ej = {
    "onset": {"Description": "Trigger onset from evt.bdf, used as data latency (Neuracle convention)", "Units": "s"},
    "duration": {"Description": "Annotation duration in evt.bdf", "Units": "s"},
    "trial_type": {"Description": "trigger_<code>"},
    "value": {"Description": "Trigger code from evt.bdf 'Trigger-In:<code>' (verbatim)."},
    "sample": {"Description": "Sample index (0-based) = round(onset x 1000)"},
    "source_annotation": {"Description": "Annotation text in evt.bdf, verbatim"},
    "trial": {"Description": "Trial number within the recording: ordinal of the preceding trial_start (code 101). In matched runs it is also the index into the session's MAT Trial struct (for P5 Session6-7: Session6 trials 1-180, then Session7)."},
    "event_name": {"Description": "Meaning of the code, inferred by us (not documented by the authors): for 11/21/20/31 the trigger intervals match the MAT EventTime intervals FpOn/CueOn/CueOff/TargetOn relative to PreFpOn (median abs. difference 1.2-1.8 ms, 99th percentile < 5 ms over 7,100+ trials); for 201/203/204 the code co-occurs exclusively with MAT trial_complete=1 / trial_complete=0 without fixation break / trial_FPbreak=1. Codes 255 and 192 (17 occurrences) are not interpreted (n/a).",
                   "Levels": {"trial_start": "101: trial start (MAT EventTime.PreFpOn)", "fixation_point_on": "11: fixation point on", "grating_on": "21: grating (cue) onset; on absent-stimulus trials the trigger is still sent",
                              "grating_off": "20: grating offset (50 ms after onset)", "targets_on_fp_color_change": "31: fixation point turns red/green and the two saccade targets appear (after the 600 ms delay)",
                              "trial_end_completed": "201: trial completed", "trial_end_not_completed": "203: trial not completed (no fixation break)", "trial_end_fixation_break": "204: fixation break"}},
    "stim_presence": {"Description": "MAT Trial.StiPresence", "Levels": {"staircase": "1: grating contrast near threshold (1 up/1 down staircase)", "salient": "2: salient grating with fixed high contrast", "absent": "3: no grating (zero contrast)"}},
    "contrast": {"Description": "MAT Trial.Sti.Contrast: grating contrast value as stored by the task software (Weber contrast in task units; see article)"},
    "fp_color": {"Description": "MAT Trial.TG.RespFP1G2R: fixation-point colour cue", "Levels": {"green": "1: aware -> right target, unaware -> left target", "red": "2: aware -> left target, unaware -> right target"}},
    "response": {"Description": "MAT Trial.Resp1L2R: saccade direction", "Levels": {"left": "1", "right": "2"}},
    "awareness": {"Description": "MAT Trial.AwareType1U2A: subject's report derived from saccade direction and colour", "Levels": {"unaware": "1", "aware": "2"}},
    "trial_complete": {"Description": "MAT Trial.trial_complete: 1 = trial completed correctly, 0 = aborted"},
    "fixation_break": {"Description": "MAT Trial.trial_FPbreak: 1 = fixation break, 0 = none"},
}
wj(os.path.join(OUT, "task-visualawareness_events.json"), ej)

R = os.path.join(OUT, "README"); t = open(R).read()
cut = t.find("## Source")
head = """# Human prefrontal cortex and the emergence of visual awareness: sEEG (Fang et al., 2024)

Raw stereo-EEG of 6 adult male patients with drug-resistant epilepsy (Department of Neurosurgery, PLA General Hospital,
Beijing) performing a visual awareness task with saccadic report, with per-trial behaviour, defaced T1 MRI, and (in
sourcedata) post-implantation CT and the eye-position/behaviour files of the patients and of 10 healthy controls.

## Cohort (article, Methods 'Data acquisition')
- Patients: 6 (6 males, 32.33 ± 4.75 years, mean ± SEM; per-patient ages not given). Electrodes in both hemispheres
  for patients 1, 5 and 6, one hemisphere for patients 2-4 (participants.tsv). Patients were on their usual
  anti-epileptic medication. Electrode placement was based on clinical requirements only.
- Healthy controls: 10 (4 males, 6 females, 27.80 ± 3.92 years), behaviour/eye position only (no neural data);
  their files are in `sourcedata/dryad-p8cz8w9xp/HealthyControls/` (C01-C10, release order).

## Task (article, 'Experimental task')
Fixation (white cross) for 600 ms, then a 2° Gabor grating for 50 ms at 7° eccentricity, contralateral to the implanted
hemisphere (right side for the bilateral patients 1, 5, 6). In 70% of trials the contrast tracks the perceptual
threshold (1 up/1 down staircase), in 10% it is well above threshold, in 20% no grating is shown. After another 600 ms
the fixation point turns green or red and two saccade targets appear at 10° left and right. Seen + green -> right
target, seen + red -> left target; not seen inverts the rule. 180 trials per session, ITI 800 ms. Patients' stimuli:
24-inch 144 Hz screen; eye position by an infrared eye tracker (Jsmz EM2000C) at 1 kHz; controls: 27-inch 120 Hz
screen, EyeLink 1000 at 1 kHz. MATLAB + Psychtoolbox-3.

## Recording
Depth electrodes (SINOVATION, 8-20 contacts, 0.8 mm diameter, 2 mm length, 1.5 mm spacing), NEURACLE amplifier,
1 kHz, hardware filter 1-250 Hz and 50 Hz notch, reference: a contact in white matter. 108-254 channels per recording.

"""
t = head + t[cut:]
t = t.replace("""- Events come from `evt.bdf` (Neuracle 'Trigger-In:<code>' annotations). The onsets are used as data latencies, as
  Neuracle's own reader does; the two files' header start times (1-s resolution) differ by 0-1 s. Trigger codes are
  not documented in the release; they are kept verbatim (`value`).""",
"""- Events come from `evt.bdf` (Neuracle 'Trigger-In:<code>' annotations). The onsets are used as data latencies, as
  Neuracle's own reader does; the two files' header start times (1-s resolution) differ by 0-1 s. Codes are kept
  verbatim (`value`). The authors do not document them; `event_name` gives our reading, checked against the release
  behaviour files (see `task-visualawareness_events.json`).
- Per-trial behaviour from the release MAT files (stimulus presence, contrast, colour cue, saccade direction, awareness
  report, completion, fixation break) is added to every event of the trial. A recording is matched to its MAT file
  only when the number of trial starts (code 101) equals the number of MAT trials and the trigger intervals agree
  with the MAT event times (99th percentile < 25 ms; observed < 9 ms): 39 of 41 runs. Not matched (behaviour columns
  n/a; raw MAT files in sourcedata): sub-03 run-11 (117 trial starts in the recording vs 180 MAT trials) and sub-04
  run-06 (178 vs 180).""")
t = t.replace("""- Dates: year and month kept, day set to 01 (scans.tsv; BDF headers in sourcedata).""",
"""- Dates: year and month kept, day set to 01 (scans.tsv; BDF headers and MAT-file header creation dates in
  sourcedata; times of day kept).""")
t = t.replace("""- Behaviour/eye position (.mat, per session) for patients and the 10 healthy controls (behaviour only, no neural data)
  are in sourcedata with neutral names; their struct fields are described in `sourcedata/dryad-p8cz8w9xp/README.md`.""",
"""- Behaviour/eye position (.mat, per session) for patients and the 10 healthy controls (behaviour only, no neural data)
  are in sourcedata with neutral names; their struct fields are described in `sourcedata/dryad-p8cz8w9xp/README.md`
  (the release README, byte for byte).
- The release zip itself is not redistributed: its file names carry patient initials and recording dates, and the BDF
  and MAT headers carry full recording dates. Every original file is in sourcedata under a neutral name, byte-identical
  except for those header dates; `MANIFEST.tsv` lists the sha256 of each original release file and what was changed.""")
t += """
## How to load
```python
import mne, pandas as pd
raw = mne.io.read_raw_brainvision("sub-01/ieeg/sub-01_task-visualawareness_run-01_ieeg.vhdr", preload=True)  # volts
ev = pd.read_csv("sub-01/ieeg/sub-01_task-visualawareness_run-01_events.tsv", sep="\\t")
cues = ev[ev.event_name == "grating_on"]  # one row per trial with stim_presence/contrast/awareness
```
MNE-BIDS: `mne_bids.read_raw_bids(BIDSPath(root=".", subject="01", task="visualawareness", run="01", datatype="ieeg"))`.
Behaviour MAT files: `scipy.io.loadmat(path, squeeze_me=True, struct_as_record=False)["Trial"]`.

## References
- Fang Z, Dang Y, Ling Z, Han Y, Zhao H, Xu X, Zhang M (2024). The involvement of the human prefrontal cortex in the
  emergence of visual awareness. eLife 13:RP89076. doi:10.7554/eLife.89076
- Data: Dryad doi:10.5061/dryad.p8cz8w9xp (CC0 1.0).
"""
open(R, "w").write(t)
c = os.path.join(OUT, "CHANGES"); open(c, "w").write(
    "1.0.0 2026-10-07\n  - Conversion of Dryad doi:10.5061/dryad.p8cz8w9xp to iEEG-BIDS for NEMAR (lossless BDF -> BrainVision, events,"
    " per-trial behaviour, defaced T1w, sourcedata with dates reduced to year-month).\n")
shutil.copy(__file__, os.path.join(OUT, "code"))
for f in ["b2dryad_events036.py", "b2dryad_fixsrc036.py", "b2dryad_finalize036.py", "b2dryad_inspect036.py"]:
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), f)
    if os.path.exists(src): shutil.copy(src, os.path.join(OUT, "code"))
print("FINAL036 done")
