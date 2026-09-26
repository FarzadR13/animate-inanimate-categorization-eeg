
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
			Analyses
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
The dPrime computations are done in Rstudio, executing the Analyses.R code.
Comp.m is a matlab code comparing the dPrime results versus chance-level as well as across stimulus sets.

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
			Excel files
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Accuracy_ByStim.xlsx is an excel file of the average accuracy per stimuli, for each stimulus set.

AllResponses.xlsx is an excel file of all the responses of Experiment 4.
Rows are the trials.
Columns:
	- subject: informing about the subject, anonymised code per subjects.
	- Group: informing about the stimulus set the subject have seen (CPS stand for colorfull phase-scramble, GPS for grayscale phase-scramble and Tex for texforms).
	- Cat: inform about the category of the images shown (A for animate, I for inanimate).
	- check: inform about the accuracy of the response. 1 if the stimulus has been identified as an animate and is indeed an animate, or if it has been identified as not being an animate and is indeed an inanimate, 0 otherwise.
	- stim: inform about the images shown, with the name of the images.
	- button1: inform about the left button (YES or NO).
	- button2: inform about the right button (YES or NO).
	- response: inform about which button has been pressed by the subject (left (1) or right (2)).
	- RT: inform about the time taken by the subject to choose the button.

List_Texforms_Exp3.xlsx is an excel file of all texform images shown in the ft-EEG Experiment 3.

Results_dPrime.xlsx is an excel with the dPrime results per subjects (rows) and stimulus set (columns).

SDT_CPS.xlsx, SDT_GPS.xlsx & SDT_Tex.xlsx are excel files informing about each stimulus set results per participant (rows), for the entire stimulus set (640 images).
SDT_CPS_listTex.xlsx, SDT_GPS_listTex.xlsx & SDT_Tex_listTex.xlsx are excel files informing about each stimulus set results per participant (rows), for the stimulus set used in Experiment 3 (350 images).
Those last excel files results from the Analyses.R code.