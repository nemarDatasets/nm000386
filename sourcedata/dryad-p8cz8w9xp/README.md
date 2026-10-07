# Dataset for the eLife article entitled 'The involvement of the human prefrontal cortex in the emergence of visual awareness'

<https://doi.org/10.5061/dryad.p8cz8w9xp>

The dataset contains raw eye position data and sEEG data obtained within the study "The involvement of the human prefrontal cortex in the emergence of visual awareness". The dataset was produced to assess the involvement of the man prefrontal cortex in the emergence of visual awareness.

## Description of the data and file structure

In this dataset, the healthy control data includes eye position data, while the patient data includes the eye position data, the seeg data and the brain image data.

Details for the dataset:

There  are two folders in the Dataset, including the 'Healthy Control Data' and 'Patients Data' folder.

Healthy Control Data: There are ten folders named 'xx_VisualAwareData' and each contains the behavioral data of each healthy control. The '.mat' files contain the raw behavioral data that required to analyze behavioral performance in each experimental session. The detailed information of the variables in '.mat' files is as follows:

1.  Struct 'Trial', the detailed information for each trial: [1] trial_complete, 1- trial completed correctly; 0-trial aborted. [2] FP, the detailed information of the Fixation Point. [3] Sti, the detailed information of the cue stimulus (the grating). [4] StiPresence, a customized index indicating the experimental conditions. '1'- stimulus with varied contrast, adjusting according to staircase method ; '2'-salient stimulus with fixed high contrast; '3'-no stimulus. [5] TG, the detailed information of the target. The variable 'RespFP1G2R': 1- Fixation color became green 2-fixation color became red; [6] realtimes, the time point for each event. [7] trial_abort, 1-trial aborted, 0- trial completed correctly; [8] trial_FPbreak, 1- fixation break, 0- no fixation break. [9] Resp1L2R, subjects' saccadic response, 1- left, 2-right; [10] AwareType1U2A, subjects' report, 1- 'Unaware',2-'Aware' [11] eyePos, eye position data, eyeX/eyeY - eye position corresponded to the pixels in the screen. 'time', corresponded time points to the eye position. time1, redundant variables.
2.  Struct 'SessionSet', the setup information of this session. [1] num_trial, Number of prearranged trials. [2] max_itrial, number of finished trials. [3]screen, the detailed information of the screen that presented the visual stimulus [4] RespFpColorDir, the prearranged color of fixation point,1- green, 2-red. [5]StiPresence_Dir,  the prearranged StiPresence Index,'1'- stimulus with varied contrast, adjusting according to staircase method ; '2'-salient stimulus with fixed high contrast; '3'-no stimulus. [5] xx_Frames, information that not relevant to current study.
3.  Struct 'Record', the information that extract from the 'Trial' struct to make a brief online analysis, not necessary for the offline analysis. [1] Contrast, the stimulus contrast [2] RevContrast, the contrast value in each reversal during the staircase procedure. [3] Resp1L2R, subjects' saccadic response, 1- left, 2-right; [4] Threshold, the determined threshold.
4.  Struct 'Picture',  the information that extract from the 'Trial' struct to make a brief online analysis, not necessary for the offline analysis. [1]StiContrast, the different value of each stimulus contrast type; [2]SticontrastNum, the trial number of each contrast type. [3]AwareNum, the trial number with reported 'aware' of each contrast type; [4]UnAwareNum, the trial number with reported 'unaware' of each contrast type; [5]AwarePercent, the percent with reported 'aware' in each contrast type;[6]StairFigContrast, the contrast values in the near-threhold trials. [7]ResEachContrast, subjects' response in each contrast levels. 1-unaware,2-aware;

Patients Data:  There are three folders in this file. In the 'EyePositionData' folder, the data are similarly organized as above Healthy Control Data.

In the 'ImageData' folder, the deidentified Magnetic Resonance Imaging (MRI), computer tomography (CT), which are required to reconstruct the brain and implanted electrodes, are contained in each patient's folder.

In the 'SEEG Data' folder, the stereotactic electroencephalogram (sEEG) data (data.bdf), along with the event information (evt.bdf), is stored separately for each experimental session of each patient.

## Sharing/Access information

Links to other publicly accessible locations of the data: <https://doi.org/10.7554/eLife.89076.2>

Data was derived from the following sources: Beijing Normal University
