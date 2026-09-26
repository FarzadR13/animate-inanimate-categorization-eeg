clc
clear all
close all

current_folder=fullfile(fileparts(mfilename('fullpath')));

[num,txt,raw]=xlsread(fullfile(current_folder,'SDT_CPS')); %% column 5
[num2,txt,raw]=xlsread(fullfile(current_folder,'SDT_GPS'));
[num3,txt,raw]=xlsread(fullfile(current_folder,'SDT_Tex'));

%%% If only restricted to 350 stimuli:
% [num,txt,raw]=xlsread(fullfile(current_folder,'SDT_CPS_listTex')); %% column 5
% [num2,txt,raw]=xlsread(fullfile(current_folder,'SDT_GPS_listTex'));
% [num3,txt,raw]=xlsread(fullfile(current_folder,'SDT_Tex_listTex'));


%%% CPS
M=0;
[h p ci sta]=ttest(num(:,5),M,'tail','right')
Moy=nanmean(num(:,5))
d=Moy/sta.sd

%%% GPS
M=0;
[h p ci sta]=ttest(num2(:,5),M,'tail','right')
Moy=nanmean(num2(:,5))
d=Moy/sta.sd

%%% Tex
M=0;
[h p ci sta]=ttest(num3(:,5),M,'tail','right')
Moy=nanmean(num3(:,5))
d=Moy/sta.sd


%%% CPS vs GPS
[h p ci sta]=ttest2(num(:,5),num2(:,5))
Moy=nanmean(num(:,5)-num2(:,5))
d=Moy/sta.sd

%%% Tex vs CPS
[h p ci sta]=ttest2(num3(:,5),num(:,5))
Moy=nanmean(num3(:,5)-num(:,5))
d=Moy/sta.sd

%%% Tex vs GPS
[h p ci sta]=ttest2(num3(:,5),num2(:,5))
Moy=nanmean(num3(:,5)-num2(:,5))
d=Moy/sta.sd

