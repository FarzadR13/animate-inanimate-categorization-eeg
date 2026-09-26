clc
clear all
close all
current_folder=fullfile(fileparts(mfilename('fullpath'))); 
load(fullfile(current_folder,'Data_Exp1','Preprocess','FFT'));
load(fullfile(current_folder,'Data_Exp1','Preprocess','BSA'));
BSA_Exp1=BSA;
clearvars BSA
load(fullfile(current_folder,'Data_Exp2','Preprocess','BSA'));
BSA_Exp2=BSA;
clearvars BSA
load(fullfile(current_folder,'Data_Exp3','Preprocess','BSA'));
BSA_Exp3=BSA;
clearvars BSA
subj=size(FTransform(1).Img,1);
n_gap=1;
n_bin=12;
% return

listeElec=1:128;
Harm=[31,61,91,121,181,211,241,271];
for s=1:subj
    for h=1:length(Harm)
        bsaImg_Exp1(s,:,h)=BSA_Exp1(s).Img(listeElec,Harm(1,h));
        bsaScramble_Exp1(s,:,h)=BSA_Exp1(s).Scramble(listeElec,Harm(1,h));
        bsaImg_Exp2(s,:,h)=BSA_Exp2(s).Img(listeElec,Harm(1,h));
        bsaScramble_Exp2(s,:,h)=BSA_Exp2(s).Scramble(listeElec,Harm(1,h));
        bsaImg_Exp3(s,:,h)=BSA_Exp3(s).Img(listeElec,Harm(1,h));
        bsaScramble_Exp3(s,:,h)=BSA_Exp3(s).Scramble(listeElec,Harm(1,h));
    end
end
BSAImg_Exp1(:,:)=sum(bsaImg_Exp1(:,:,:),3);BsaImg_Exp1(:,:)=nanmean(BSAImg_Exp1(:,:,:),2);
BSAScramble_Exp1(:,:)=sum(bsaScramble_Exp1(:,:,:),3);BsaScramble_Exp1(:,:)=nanmean(BSAScramble_Exp1(:,:,:),2);
BSAImg_Exp2(:,:)=sum(bsaImg_Exp2(:,:,:),3);BsaImg_Exp2(:,:)=nanmean(BSAImg_Exp2(:,:,:),2);
BSAScramble_Exp2(:,:)=sum(bsaScramble_Exp2(:,:,:),3);BsaScramble_Exp2(:,:)=nanmean(BSAScramble_Exp2(:,:,:),2);
BSAImg_Exp3(:,:)=sum(bsaImg_Exp3(:,:,:),3);BsaImg_Exp3(:,:)=nanmean(BSAImg_Exp3(:,:,:),2);
BSAScramble_Exp3(:,:)=sum(bsaScramble_Exp3(:,:,:),3);BsaScramble_Exp3(:,:)=nanmean(BSAScramble_Exp3(:,:,:),2);
clearvars bsaImg_Exp1 bsaImg_Exp2 bsaImg_Exp3 bsaScramble_Exp1 bsaScramble_Exp2 bsaScramble_Exp3
clearvars BSAImg_Exp1 BSAImg_Exp2 BSAImg_Exp3 BSAScramble_Exp1 BSAScramble_Exp2 BSAScramble_Exp3


%% ANOVA
data(:,1)=BsaImg_Exp1;data(13:24,1)=BsaScramble_Exp1;data(:,2)=1;data(1:12,3)=1;data(13:24,3)=2;
data(25:36,1)=BsaImg_Exp2;data(37:48,1)=BsaScramble_Exp2;data(25:48,2)=2;data(25:36,3)=1;data(37:48,3)=2;
data(49:60,1)=BsaImg_Exp3;data(61:72,1)=BsaScramble_Exp3;data(49:72,2)=3;data(49:60,3)=1;data(61:72,3)=2;
data(1:12,4)=[1:12];data(13:24,4)=[1:12];data(25:36,4)=[13:24];data(37:48,4)=[13:24];data(49:60,4)=[25:36];data(61:72,4)=[25:36];
[Results.Anova.SSQs, Results.Anova.DFs, Results.Anova.MSQs, Results.Anova.Fs, Results.Anova.Ps]=mix_anova(data);

%% Following ttest - Comparison between Exp 1, 2 and 3
BsaExp_1=[BsaImg_Exp1 BsaScramble_Exp1];
BsaExp_2=[BsaImg_Exp2 BsaScramble_Exp2];
BsaExp_3=[BsaImg_Exp3 BsaScramble_Exp3];

[h Results.Exp_1_2.p Results.Exp_1_2.ci sta]=ttest2(nanmean(BsaExp_1,2),nanmean(BsaExp_2,2));
Results.Exp_1_2.t=sta.tstat;
Results.Exp_1_2.df=sta.df;
Results.Exp_1_2.mean=nanmean(nanmean(BsaExp_1,2)-nanmean(BsaExp_2,2));
Results.Exp_1_2.sd=sta.sd;
Results.Exp_1_2.d=Results.Exp_1_2.mean/Results.Exp_1_2.sd;
clearvars h sta
[h Results.Exp_1_3.p Results.Exp_1_3.ci sta]=ttest2(nanmean(BsaExp_1,2),nanmean(BsaExp_3,2));
Results.Exp_1_3.t=sta.tstat;
Results.Exp_1_3.df=sta.df;
Results.Exp_1_3.mean=nanmean(nanmean(BsaExp_1,2)-nanmean(BsaExp_3,2));
Results.Exp_1_3.sd=sta.sd;
Results.Exp_1_3.d=Results.Exp_1_3.mean/Results.Exp_1_3.sd;
clearvars h sta
[h Results.Exp_2_3.p Results.Exp_2_3.ci sta]=ttest2(nanmean(BsaExp_2,2),nanmean(BsaExp_3,2));
Results.Exp_2_3.t=sta.tstat;
Results.Exp_2_3.df=sta.df;
Results.Exp_2_3.mean=nanmean(nanmean(BsaExp_2,2)-nanmean(BsaExp_3,2));
Results.Exp_2_3.sd=sta.sd;
Results.Exp_2_3.d=Results.Exp_2_3.mean/Results.Exp_2_3.sd;
clearvars h sta

%% Following ttest - Comparison between Original (Or) Exp1, 2 and 3
[h Results.DOr_1_2.p Results.DOr_1_2.ci sta]=ttest2(BsaImg_Exp1,BsaImg_Exp2);
Results.DOr_1_2.t=sta.tstat;
Results.DOr_1_2.df=sta.df;
Results.DOr_1_2.mean=nanmean(BsaImg_Exp1-BsaImg_Exp2);
Results.DOr_1_2.sd=sta.sd;
Results.DOr_1_2.d=Results.DOr_1_2.mean/Results.DOr_1_2.sd;
clearvars h sta

[h Results.DOr_1_3.p Results.DOr_1_3.ci sta]=ttest2(BsaImg_Exp1,BsaImg_Exp3);
Results.DOr_1_3.t=sta.tstat;
Results.DOr_1_3.df=sta.df;
Results.DOr_1_3.mean=nanmean(BsaImg_Exp1-BsaImg_Exp3);
Results.DOr_1_3.sd=sta.sd;
Results.DOr_1_3.d=Results.DOr_1_3.mean/Results.DOr_1_3.sd;
clearvars h sta

[h Results.DOr_2_3.p Results.DOr_2_3.ci sta]=ttest2(BsaImg_Exp2,BsaImg_Exp3);
Results.DOr_2_3.t=sta.tstat;
Results.DOr_2_3.df=sta.df;
Results.DOr_2_3.mean=nanmean(BsaImg_Exp2-BsaImg_Exp3);
Results.DOr_2_3.sd=sta.sd;
Results.DOr_2_3.d=Results.DOr_2_3.mean/Results.DOr_2_3.sd;
clearvars h sta

%% Following ttest - Comparison between Impoverished (Tr) Exp1, 2 and 3
[h Results.DTr_1_2.p Results.DTr_1_2.ci sta]=ttest2(BsaScramble_Exp1,BsaScramble_Exp2);
Results.DTr_1_2.t=sta.tstat;
Results.DTr_1_2.df=sta.df;
Results.DTr_1_2.mean=nanmean(BsaScramble_Exp1-BsaScramble_Exp2);
Results.DTr_1_2.sd=sta.sd;
Results.DTr_1_2.d=Results.DTr_1_2.mean/Results.DTr_1_2.sd;
clearvars h sta

[h Results.DTr_1_3.p Results.DTr_1_3.ci sta]=ttest2(BsaScramble_Exp1,BsaScramble_Exp3);
Results.DTr_1_3.t=sta.tstat;
Results.DTr_1_3.df=sta.df;
Results.DTr_1_3.mean=nanmean(BsaScramble_Exp1-BsaScramble_Exp3);
Results.DTr_1_3.sd=sta.sd;
Results.DTr_1_3.d=Results.DTr_1_3.mean/Results.DTr_1_3.sd;
clearvars h sta

[h Results.DTr_2_3.p Results.DTr_2_3.ci sta]=ttest2(BsaScramble_Exp2,BsaScramble_Exp3);
Results.DTr_2_3.t=sta.tstat;
Results.DTr_2_3.df=sta.df;
Results.DTr_2_3.mean=nanmean(BsaScramble_Exp2-BsaScramble_Exp3);
Results.DTr_2_3.sd=sta.sd;
Results.DTr_2_3.d=Results.DTr_2_3.mean/Results.DTr_2_3.sd;
clearvars h sta
