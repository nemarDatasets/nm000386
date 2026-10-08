[![DOI](https://img.shields.io/badge/DOI-10.82901%2Fnemar.nm000386-blue)](https://doi.org/10.82901/nemar.nm000386)

# Human prefrontal cortex and the emergence of visual awareness: sEEG (Fang et al., 2024)

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
  the BDF gain. The BDF digital range is asymmetric (-8388608..8388607 for a symmetric physical range), so the BDF
  physical value = digital x gain + half a digital step (about 0.045 µV); that constant is not representable in
  BrainVision and is dropped. The digital values are exact (checked by round-trip).
- sub-04: the BDF has the label LDELT1 twice (channels 1 and 251, different signals); channel 251 is named LDELT1_ch251
  (original label in channels.tsv column source_label). No filtering or resampling.
- Events come from `evt.bdf` (Neuracle 'Trigger-In:<code>' annotations). The onsets are used as data latencies, as
  Neuracle's own reader does; the two files' header start times (1-s resolution) differ by 0-1 s. Codes are kept
  verbatim (`value`). The authors do not document them; `event_name` gives our reading, checked against the release
  behaviour files (see `task-visualawareness_events.json`).
- Per-trial behaviour from the release MAT files (stimulus presence, contrast, colour cue, saccade direction, awareness
  report, completion, fixation break) is added to every event of the trial. A recording is matched to its MAT file
  only when the number of trial starts (code 101) equals the number of MAT trials and the trigger intervals agree
  with the MAT event times (99th percentile < 25 ms; observed < 9 ms): 39 of 41 runs. Not matched (behaviour columns
  n/a; raw MAT files in sourcedata): sub-03 run-11 (117 trial starts in the recording vs 180 MAT trials) and sub-04
  run-06 (178 vs 180).
- P5 'Session6-7' is a single file in the release (two sessions in one recording) and is kept as one run.
- Channels named *DELT* (present for some patients) are typed MISC: the name suggests deltoid EMG but the release does
  not say. All other channels are SEEG. No electrode coordinates are released (only defaced MRI/CT).
- Dates: year and month kept, day set to 01 (scans.tsv; BDF headers and MAT-file header creation dates in
  sourcedata; times of day kept). Patient initials and recording dates
  in release file names were removed from sourcedata names (see `sourcedata/dryad-p8cz8w9xp/MANIFEST.tsv`, which lists the
  sha256 of every original file).
- Images: the authors' defaced T1 MRI is in `anat/` (T1w). Defacing was checked by surface rendering for all 12 images.
  CT has no raw BIDS suffix and is kept in sourcedata; the CT of P5 is excluded because its defacing could not be
  verified (it remains available from Dryad).
- Behaviour/eye position (.mat, per session) for patients and the 10 healthy controls (behaviour only, no neural data)
  are in sourcedata with neutral names; their struct fields are described in `sourcedata/dryad-p8cz8w9xp/README.md`
  (the release README, byte for byte).
- The release zip itself is not redistributed: its file names carry patient initials and recording dates, and the BDF
  and MAT headers carry full recording dates. Every original file is in sourcedata under a neutral name, byte-identical
  except for those header dates; `MANIFEST.tsv` lists the sha256 of each original release file and what was changed.
- Age per patient is not given (article: 32.33 ± 4.75 years, mean ± SEM); all six are male (article).

## How to load
```python
import mne, pandas as pd
raw = mne.io.read_raw_brainvision("sub-01/ieeg/sub-01_task-visualawareness_run-01_ieeg.vhdr", preload=True)  # volts
ev = pd.read_csv("sub-01/ieeg/sub-01_task-visualawareness_run-01_events.tsv", sep="\t")
cues = ev[ev.event_name == "grating_on"]  # one row per trial with stim_presence/contrast/awareness
```
MNE-BIDS: `mne_bids.read_raw_bids(BIDSPath(root=".", subject="01", task="visualawareness", run="01", datatype="ieeg"))`.
Behaviour MAT files: `scipy.io.loadmat(path, squeeze_me=True, struct_as_record=False)["Trial"]`.

## References
- Fang Z, Dang Y, Ling Z, Han Y, Zhao H, Xu X, Zhang M (2024). The involvement of the human prefrontal cortex in the
  emergence of visual awareness. eLife 13:RP89076. doi:10.7554/eLife.89076
- Data: Dryad doi:10.5061/dryad.p8cz8w9xp (CC0 1.0).
