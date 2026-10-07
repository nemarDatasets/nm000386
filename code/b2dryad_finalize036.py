"""IEEG036 text files. Usage: python b2dryad_finalize036.py <extract_root> <bids>"""
import glob, json, os, shutil, sys
X, OUT = sys.argv[1], sys.argv[2]
ROOT = glob.glob(os.path.join(X, "Dataset_*"))[0]


def wjson(p, o):
    with open(p, "w") as f: json.dump(o, f, indent=2, ensure_ascii=False); f.write("\n")


AUTH = ["Zepeng Fang", "Yuanyuan Dang", "Zhipei Ling", "Yongzheng Han", "Hulin Zhao", "Xin Xu", "Mingsha Zhang"]
ETH = ("All subjects provided informed consent to participate in this study. The Ethics Committee of Chinese PLA General Hospital approved "
       "the experimental procedures (approval numbers S2022-457-01). [Fang et al. 2024, eLife 13:RP89076, Ethics statement; doi:10.7554/eLife.89076]")
wjson(os.path.join(OUT, "dataset_description.json"), {
    "Name": "The involvement of the human prefrontal cortex in the emergence of visual awareness (Fang et al., 2024): sEEG, 6 patients",
    "BIDSVersion": "1.10.0", "DatasetType": "raw", "License": "CC0-1.0", "Authors": AUTH, "EthicsApprovals": [ETH],
    "Funding": ["Ministry of Science and Technology of the People's Republic of China STI2030-Major Projects 2021ZD0204300",
                "National Natural Science Foundation of China 32061143004", "National Natural Science Foundation of China 32030045",
                "Open Research Fund of the State Key Laboratory of Cognitive Neuroscience and Learning CNLZD2202"],
    "HowToAcknowledge": "Cite Fang Z, Dang Y, Ling Z, Han Y, Zhao H, Xu X, Zhang M (2024) The involvement of the human prefrontal cortex in the emergence of visual awareness. eLife 13:RP89076, doi:10.7554/eLife.89076; and Dryad doi:10.5061/dryad.p8cz8w9xp.",
    "ReferencesAndLinks": ["https://doi.org/10.7554/eLife.89076", "https://doi.org/10.5061/dryad.p8cz8w9xp"],
    "SourceDatasets": [{"DOI": "doi:10.5061/dryad.p8cz8w9xp", "URL": "https://datadryad.org/dataset/doi:10.5061/dryad.p8cz8w9xp", "Version": "Dryad version 6 (published 2024-01-18)"}],
    "GeneratedBy": [{"Name": "b2dryad_convert036.py", "Description": "BDF -> BrainVision INT_32 with the exact BDF digital values and gains (lossless); events from evt.bdf; dates day -> 01. Code in code/."}],
    "Keywords": ["sEEG", "visual awareness", "consciousness", "prefrontal cortex", "saccade", "high-gamma"],
})
wjson(os.path.join(OUT, "participants.json"), {
    "source_id": {"Description": "Patient folder name in the release (P1-P6)"},
    "sex": {"Description": "Article: 'Six adult patients with drug-resistant epilepsy (6 males, 32.33±4.75 years old, mean ± SEM)'", "Levels": {"M": "male"}},
    "age": {"Description": "Per-patient age not given (article reports 32.33±4.75 years, mean ± SEM)", "Units": "year"},
    "n_runs": {"Description": "Number of task sessions (release 'SessionN' folders), stored as runs"}})
wjson(os.path.join(OUT, "task-visualawareness_events.json"), {
    "onset": {"Description": "Onset of the trigger from evt.bdf, used as data latency (Neuracle convention)", "Units": "s"},
    "duration": {"Description": "Annotation duration in evt.bdf", "Units": "s"},
    "trial_type": {"Description": "trigger_<code>; trigger codes are not documented in the release or the article"},
    "value": {"Description": "Trigger code from 'Trigger-In:<code>'. Observed codes: 11, 20, 21, 31, 101, 201, 203, 204, 255, 100 (meanings not documented; per-trial task details are in the eye-position .mat files in sourcedata)"},
    "sample": {"Description": "Sample index (0-based) = round(onset * 1000)"},
    "source_annotation": {"Description": "Annotation text in evt.bdf, verbatim"}})
wjson(os.path.join(OUT, "task-visualawareness_channels.json"), {"notes": {"Description": "Conversion notes per channel"}})
open(os.path.join(OUT, "README"), "w").write("""# Human prefrontal cortex and the emergence of visual awareness: sEEG (Fang et al., 2024)

Stereo-EEG from 6 adult male patients with drug-resistant epilepsy (PLA General Hospital, Beijing) performing a visual
awareness task with saccadic report (near-threshold, salient or absent grating; 600 ms delay; fixation-colour cue).
Recorded with a NEURACLE system at 1 kHz (hardware filter 1-250 Hz, 50 Hz notch), referenced to a white-matter contact.

## Source
- Dryad doi:10.5061/dryad.p8cz8w9xp (version 6, 2024-01-18), CC0 1.0. Authors: Zepeng Fang, Yuanyuan Dang, Zhipei Ling,
  Yongzheng Han, Hulin Zhao, Xin Xu, Mingsha Zhang (Beijing Normal University / PLA General Hospital).
- Article: Fang et al. (2024) eLife 13:RP89076, doi:10.7554/eLife.89076.

## Ethics (verbatim from the article)
"All subjects provided informed consent to participate in this study. The Ethics Committee of Chinese PLA General Hospital
approved the experimental procedures (approval numbers S2022-457-01)."

## Conversion
- Each release session (`SEEG Data/Pn/SessionK/data.bdf`) is one run. BDF is not an iEEG-BIDS format, so the data are
  written as BrainVision with 32-bit integer samples holding the exact BDF digital values, and per-channel resolution =
  the BDF gain: physical values are identical to the BDF (lossless; checked by round-trip). No filtering or resampling.
- Events come from `evt.bdf` (Neuracle 'Trigger-In:<code>' annotations). The onsets are used as data latencies, as
  Neuracle's own reader does; the two files' header start times (1-s resolution) differ by 0-1 s. Trigger codes are
  not documented in the release; they are kept verbatim (`value`).
- P5 'Session6-7' is a single file in the release (two sessions in one recording) and is kept as one run.
- Channels named *DELT* (present for some patients) are typed MISC: the name suggests deltoid EMG but the release does
  not say. All other channels are SEEG. No electrode coordinates are released (only defaced MRI/CT).
- Dates: year and month kept, day set to 01 (scans.tsv; BDF headers in sourcedata). Patient initials and recording dates
  in release file names were removed from sourcedata names (see `sourcedata/dryad-p8cz8w9xp/MANIFEST.tsv`, which lists the
  sha256 of every original file).
- Images: the authors' defaced T1 MRI is in `anat/` (T1w). Defacing was checked by surface rendering for all 12 images.
  CT has no raw BIDS suffix and is kept in sourcedata; the CT of P5 is excluded because its defacing could not be
  verified (it remains available from Dryad).
- Behaviour/eye position (.mat, per session) for patients and the 10 healthy controls (behaviour only, no neural data)
  are in sourcedata with neutral names; their struct fields are described in `sourcedata/dryad-p8cz8w9xp/README.md`.
- Age per patient is not given (article: 32.33 ± 4.75 years, mean ± SEM); all six are male (article).
""")
shutil.copy(glob.glob(os.path.join(X, "..", "sourcedata_dl", "README.md"))[0], os.path.join(OUT, "sourcedata", "dryad-p8cz8w9xp", "README.md"))
open(os.path.join(OUT, "CHANGES"), "w").write("1.0.0 2026-10-07\n  - Conversion of Dryad doi:10.5061/dryad.p8cz8w9xp to iEEG-BIDS for NEMAR.\n")
open(os.path.join(OUT, ".bidsignore"), "w").write("code/\n")
print("FINALIZED")
