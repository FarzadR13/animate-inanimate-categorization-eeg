****************************************************************************************************************************************************
	- This repository contains data, codes and images required to replicate the analyses.
	- A local README.txt file is included in Exp4 to guide the reader in replicating the analysis.
****************************************************************************************************************************************************

You will need Matlab with EEGlab for the analyses of Experiments 1 to 3, and Rstudio for the analyses of Experiment 4.

---------------------------------------------------------------------------
---------------------------------------------------------------------------
Here is an overview of the folders.


|
-- README.txt

|
-- /Data_Exp1
	> Folder for the Experiment 1 (intact original images and impoverished phase-scramble versions).
	|
	------ /Preprocess
		|
		------ /BSA.mat
			> Baseline-subtracted amplitudes for Experiment 1.
		|
		------ /Data.mat
			> Data of the group in the time domain, after preprocessing and before FFT.
		|
		------ /FFT.mat
			> Data of the group after the fast fourier transform (FFT) and before the baseline correction.
	|
	------ /Rawdata
		> All participants EEG rawdata.
|
-- /Data_Exp2
	> This folder is for the Experiment 2 (intact grayscale images and impoverished grayscale phase-scramble versions), and is organized as the folder for Experiment 1.
|
-- /Data_Exp3
	> This folder is for the Experiment 3 (intact grayscale images and impoverished texform versions), and is organized as the folder for Experiment 1.

|
-- Analyses_Exps.m
	> Matlab code for analysing the Experiments, after baseline correction.
|
-- BSA_SNR_Zscore.m
	> Matlab code for baseline correction computation (computation of baseline subtracted amplitudes), SNR and Zscore.
|
-- Comparison_Exps.m
	> Matlab code for comparing the experiment.
|
-- FFT.m
	> Matlab code for performing the fast fourier transform (FFT) on the data after preprocessing.
|
-- mix_anova.m
	> Function necessary to perform the mix-ANOVA, to compare the experiments.
|
-- Preprocess_Exp1.m
	> Matlab code for preprocessing the EEG data of Experiment 1.
|
-- Preprocess_Exp2.m
	> Matlab code for preprocessing the EEG data of Experiment 2.
|
-- Preprocess_Exp3.m
	> Matlab code for preprocessing the EEG data of Experiment 3.
|
-- repanova.m
	> Function necessary to perform a repeated measure ANOVA to compare the conditions, in Analyses_Exps.m.
