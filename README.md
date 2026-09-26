# Animate-Inanimate Object Categorization from Minimal Visual Information

This repository contains the data, stimuli, and analysis code for the study:
**"Animate-Inanimate Object Categorization from Minimal Visual Information in the Human Brain, Human Behavior, and Deep Neural Networks"** 
by *Céline Spriet, Farzad Rostami, Jean-Rémy Hochmann, and Liuba Papeo* (Published in *Journal of Cognitive Neuroscience*).

**Paper Link:** [https://doi.org/10.1162/jocn_a_02220](https://doi.org/10.1162/jocn_a_02220)

## Overview
This project investigates the necessary and sufficient visual features required to discriminate between animate and inanimate objects. By using rapid sequences of images (frequency-tagging EEG) and degrading images to retain only specific low- and mid-level visual features (e.g., grayscale, texform, and phase-scrambled), we tracked the animate-inanimate distinction across human brain activity, behavioral responses, and Deep Neural Networks (DNNs).

## Repository Structure

&#x20;   animate-inanimate-categorization-eeg/
&#x20;   ├── stimuli/                  # Image sets used across all experiments
&#x20;   ├── eeg_analysis/             # MATLAB scripts and processed EEG data
&#x20;   ├── behavioral_exp4/          # Behavioral data (SDT) and R scripts
&#x20;   └── dnn_analysis/             # Python/R scripts and results for DNN RSA

## Details by Section

### 1. EEG Analysis (`/eeg_analysis`)
Contains the MATLAB scripts for preprocessing and statistical analysis of the frequency-tagging EEG data.
* `Preprocess_Exp[1-3].m`: Preprocessing pipelines.
* `Analyses_Exps.m` & `Comparison_Exps.m`: Core statistical modeling.
* `Data_Exp[1-3]/`: Contains the processed `.mat` files.

### 2. Behavioral Experiment (`/behavioral_exp4`)
Contains the Signal Detection Theory (SDT) data and analysis scripts.
* `Analyses.R`: Main R script for analyzing behavioral accuracy and d-prime.

### 3. Deep Neural Network RSA (`/dnn_analysis`)
Contains the code for extracting DNN activations and computing the Representational Similarity Analysis (RSA).

**Methodological Details:**
* **Stimulus Order:** Deterministic sorting (320 animate, 320 inanimate).
* **Preprocessing:** RGB, resized to 256x256, center-cropped to 224x224, ImageNet normalization.
* **DNN Architectures:** `THINGSVision` where feasible, `torchvision` as fallback.
* **Distance Metrics:** `1 - Pearson correlation`. 
* **RSA:** `Spearman correlation`.
* **Statistics:** 1000 permutations (seed: `20240517`), FDR correction.

## Data Access
Large files (e.g., raw continuous EEG recordings or large feature extraction `.mat` files) are hosted on our Open Science Framework (OSF) repository:
**OSF dataset:** https://osf.io/e6fjn/

## Dependencies
* **MATLAB**
* **R**
* **Python 3.x**

## License and Citation
If you use the data or code in this repository, please cite our paper:
> Spriet, C., Rostami, F., Hochmann, J.-R., & Papeo, L. (2026). Animate-Inanimate Object Categorization from Minimal Visual Information in the Human Brain, Human Behavior, and Deep Neural Networks. *Journal of Cognitive Neuroscience*. https://doi.org/10.1162/jocn_a_02220