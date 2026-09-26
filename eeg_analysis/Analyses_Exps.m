clc
clear all
close all
current_folder=fullfile(fileparts(mfilename('fullpath'))); 

Preprocess_folder=fullfile(current_folder,'Data_Exp1','Preprocess'); %%%% Change lines 142 & 197
% Preprocess_folder=fullfile(current_folder,'Data_Exp2','Preprocess'); %%%% Change lines 142 & 197
% Preprocess_folder=fullfile(current_folder,'Data_Exp3','Preprocess'); %%%% Change lines 134, 142, 192, 197, 229 & 250

load(fullfile(Preprocess_folder,'FFT'));
load(fullfile(Preprocess_folder,'BSA'));
subj=size(FTransform(1).Img,1);
n_gap=1;
n_bin=12;

%% Harmonics Selection
%%%% Determine each bin number corresponding to each frequence of interest
freq_vect=f;
harmobr=2:8; fbrate=10;
frefresh=59.95;
fb=frefresh/fbrate; f_harmobr=fb*harmobr; fundbr=[fb f_harmobr];
for f=1:numel(fundbr)
    [~,target_ix] = min(abs(fundbr(f)-freq_vect'));
    target_freqbr(f)=target_ix;
end
harmo=2:40; frate=50;
frefresh=59.95;
fi=frefresh/frate; f_harmo=fi*harmo; fund=[fi f_harmo];
for f=1:numel(fund)
    [~,target_ix] = min(abs(fund(f)-freq_vect'));
    target_freq(f)=target_ix;
end
f=freq_vect;
clearvars freq_vect harmobr fbrate frefresh fb f_harmobr fundbr target_ix harmo frate fi f_harmo fund
%%%% Selecting harmonics significant
harmImg=[];
hm=[];
for h=1:length(target_freq)
    ha=target_freq(1,h);
    if Zscore.MoyElec.Img(1,ha)>1.64
        harmImg=[harmImg ha];
        hm=[hm h];
    end
end
harmbrImg=[];
hbr=[];
for h=1:length(target_freqbr)
    habr=target_freqbr(1,h);
    if Zscore.MoyElec.Img(1,habr)>1.64
        harmbrImg=[harmbrImg habr];
        hbr=[hbr h];
    end
end
harmImg(2,:)=hm;
harmbrImg(2,:)=hbr;
for j=1:length(target_freqbr)
    for i=1:size(harmImg,2)
        if harmImg(1,i)==target_freqbr(1,j)
            harmImg(1,i)=NaN;
        end
    end
end
cnt=0;
for i=1:size(harmImg,2)
    if isnan(harmImg(1,i))==0
        cnt=cnt+1;
        HarmImgAll(1,cnt)=harmImg(1,i);
    end
end
clearvars harmImg hm hbr


harmScr=[];
hm=[];
for h=1:length(target_freq)
    ha=target_freq(1,h);
    if Zscore.MoyElec.Scramble(1,ha)>1.64
        harmScr=[harmScr ha];
        hm=[hm h];
    end
end
harmbrScr=[];
hbr=[];
for h=1:length(target_freqbr)
    habr=target_freqbr(1,h);
    if Zscore.MoyElec.Scramble(1,habr)>1.64
        harmbrScr=[harmbrScr habr];
        hbr=[hbr h];
    end
end
harmbrScr(2,:)=hbr;
harmScr(2,:)=hm;
for j=1:length(target_freqbr)
    for i=1:size(harmScr,2)
        if harmScr(1,i)==target_freqbr(1,j)
            harmScr(1,i)=NaN;
        end
    end
end
cnt=0;
HarmScrAll=[];
for i=1:size(harmScr,2)
    if isnan(harmScr(1,i))==0
        cnt=cnt+1;
        HarmScrAll(1,cnt)=harmScr(1,i);
    end
end
clearvars harmScr hm hbr

%% Electrodes Selection / Number of harmonics to change accordingly
listeImgBR = [];
listeScrBR = [];
for i = 1:size(Zscore.Elec.Img,1)
    for h = 1:8
        zscore3(i,h) = Zscore.Elec.Img(i,harmbrImg(1,h));
    end
    if nanmean(zscore3(i,:),2) > 3.33
        listeImgBR = [listeImgBR i];
    end
end
for i = 1:size(Zscore.Elec.Scramble,1)
    for h = 1:8
        zscorescr3(i,h) = Zscore.Elec.Scramble(i,harmbrScr(1,h));
    end
    if nanmean(zscorescr3(i,:),2) > 3.33
        listeScrBR = [listeScrBR i];
    end
end
clearvars zscore3 zscorescr3 i h

listeImg=[];
listeScr=[];
for i=1:size(Zscore.Elec.Img,1)
    for h=1:7 %%% 1:8 for Exps 1 & 2; 1:7 for Exp3
        zscore3(i,h)=Zscore.Elec.Img(i,HarmImgAll(1,h));
    end
    if nanmean(zscore3(i,:),2)>3.33
        listeImg=[listeImg i];
    end
end
for i=1:size(Zscore.Elec.Scramble,1)
    for h=1:2 %%% 1:4 for Exp1; 1 for Exp2; 1:2 for Exp3
        zscorescr3(i,h)=Zscore.Elec.Scramble(i,HarmScrAll(1,h));
    end
    if nanmean(zscorescr3(i,:),2)>3.33
        listeScr=[listeScr i];
    end
end
clearvars zscore3 zscorescr3 i e

%% Ttests / Number of harmonics to change accordingly
%%%%% Base response
for s=1:subj
    for e=1:length(listeImgBR)
        for h=1:8
            bsaImgBR(s,e,h)=BSA(s).Img(listeImgBR(1,e),harmbrImg(1,h));
        end
    end
    for e=1:length(listeScrBR)
        for h=1:8
            bsaScrBR(s,e,h)=BSA(s).Scramble(listeScrBR(1,e),harmbrScr(1,h));
        end
    end
end
BSAImgBR(:,:)=sum(bsaImgBR(:,:,:),3);
BsaImgBR=nanmean(BSAImgBR(:,:),2);
BSAScrBR(:,:)=sum(bsaScrBR(:,:,:),3);
BsaScrBR(:,:)=nanmean(BSAScrBR(:,:),2);
clearvars s e h bsaImgBR bsaScrBR BSAImgBR BSAScrBR

M=0; %%%% one-tail ttest versus 0 (noise-level)
[h Results.ImgBR.p Results.ImgBR.ci sta]=ttest(BsaImgBR,M,'tail','right');
Results.ImgBR.t=sta.tstat;
Results.ImgBR.df=sta.df;
Results.ImgBR.mean=nanmean(BsaImgBR);
Results.ImgBR.sd=sta.sd;
Results.ImgBR.d=Results.ImgBR.mean/Results.ImgBR.sd;
clearvars h sta

[h Results.ScrBR.p Results.ScrBR.ci sta]=ttest(BsaScrBR,M,'tail','right');
Results.ScrBR.t=sta.tstat;
Results.ScrBR.df=sta.df;
Results.ScrBR.mean=nanmean(BsaScrBR);
Results.ScrBR.sd=sta.sd;
Results.ScrBR.d=Results.ScrBR.mean/Results.ScrBR.sd;
clearvars h sta

%%%% Target response
%%%% Extract BSA for each participant, each electrode, each harmonic, each condition
for s=1:subj
    for e=1:length(listeImg)
        for h=1:8  %%% 1:8 for Exps 1 & 2; 1:7 for Exp3
            bsaImgCImg(s,e,h)=BSA(s).Img(listeImg(1,e),HarmImgAll(1,h));
        end
    end
    for e=1:length(listeScr)
        for h=1:4 %%% 1:4 for Exp1; 1 for Exp2; 1:2 for Exp3
            bsaScrCScr(s,e,h)=BSA(s).Scramble(listeScr(1,e),HarmScrAll(1,h));
        end
    end
end
%%%% Sum over harmonic, average over electrodes
BSAImgCImg(:,:)=sum(bsaImgCImg(:,:,:),3);
BsaImgCImg=nanmean(BSAImgCImg(:,:),2);
BSAScrCScr(:,:)=sum(bsaScrCScr(:,:,:),3);
BsaScrCScr(:,:)=nanmean(BSAScrCScr(:,:),2);
clearvars s e h bsaImgCImg bsaScrCScr BSAImgCImg BSAScrCScr

M=0; %%%% one-tail ttest versus 0 (noise-level)
[h Results.Img.p Results.Img.ci sta]=ttest(BsaImgCImg,M,'tail','right');
Results.Img.t=sta.tstat;
Results.Img.df=sta.df;
Results.Img.mean=nanmean(BsaImgCImg);
Results.Img.sd=sta.sd;
Results.Img.d=Results.Img.mean/Results.Img.sd;
clearvars h sta

[h Results.Scr.p Results.Scr.ci sta]=ttest(BsaScrCScr,M,'tail','right');
Results.Scr.t=sta.tstat;
Results.Scr.df=sta.df;
Results.Scr.mean=nanmean(BsaScrCScr);
Results.Scr.sd=sta.sd;
Results.Scr.d=Results.Scr.mean/Results.Scr.sd;
clearvars h sta

%% Comparison conditions
%%%%% Base response
Harm=harmbrImg(1,1:8);
for s=1:subj
    for h=1:8
        bsaImg(s,:,h)=BSA(s).Img(:,Harm(1,h));
        bsaScr(s,:,h)=BSA(s).Scramble(:,Harm(1,h));
    end
end
BSAImg(:,:)=sum(bsaImg(:,:,:),3);
BSAScr(:,:)=sum(bsaScr(:,:,:),3);
BsaImg=nanmean(BSAImg(:,:,:),2);
BsaScr(:,:)=nanmean(BSAScr(:,:,:),2);
clearvars bsaImg bsaScr s h BSAImg BSAScr

[h Results.DiffBR.p Results.DiffBR.ci sta]=ttest(BsaImg,BsaScr);
Results.DiffBR.t=sta.tstat;
Results.DiffBR.df=sta.df;
Results.DiffBR.mean=nanmean(BsaImg-BsaScr);
Results.DiffBR.sd=sta.sd;
Results.DiffBR.d=Results.DiffBR.mean/Results.DiffBR.sd;
clearvars h sta BsaImg BsaScr
%%%% Target response
Harm=HarmImgAll(1,1:8);
for s=1:subj
    for h=1:8   %%% 1:8 for Exps 1 & 2; 1:7 for Exp3
        bsaImg(s,:,h)=BSA(s).Img(:,Harm(1,h));
        bsaScr(s,:,h)=BSA(s).Scramble(:,Harm(1,h));
    end
end
BSAImg(:,:)=sum(bsaImg(:,:,:),3);
BSAScr(:,:)=sum(bsaScr(:,:,:),3);
BsaImg=nanmean(BSAImg(:,:,:),2);
BsaScr(:,:)=nanmean(BSAScr(:,:,:),2);
clearvars bsaImg bsaScr s h BSAImg BSAScr

[h Results.Diff.p Results.Diff.ci sta]=ttest(BsaImg,BsaScr);
Results.Diff.t=sta.tstat;
Results.Diff.df=sta.df;
Results.Diff.mean=nanmean(BsaImg-BsaScr);
Results.Diff.sd=sta.sd;
Results.Diff.d=Results.Diff.mean/Results.Diff.sd;
clearvars h sta

%% ANOVA
for s=1:subj
    for h=1:8  %%% 1:8 for Exps 1 & 2; 1:7 for Exp3
        bsaAnim(s,:,h)=BSA(s).Anim(:,Harm(1,h));
        bsaScrAnim(s,:,h)=BSA(s).ScrAnim(:,Harm(1,h));
        bsaIna(s,:,h)=BSA(s).Ina(:,Harm(1,h));
        bsaScrIna(s,:,h)=BSA(s).ScrIna(:,Harm(1,h));
    end
end
BSAAnim(:,:)=sum(bsaAnim(:,:,:),3);
BSAScrAnim(:,:)=sum(bsaScrAnim(:,:,:),3);
BSAIna(:,:)=sum(bsaIna(:,:,:),3);
BSAScrIna(:,:)=sum(bsaScrIna(:,:,:),3);
BsaAnim(:,:)=nanmean(BSAAnim(:,:,:),2);
BsaScrAnim(:,:)=nanmean(BSAScrAnim(:,:,:),2);
BsaIna(:,:)=nanmean(BSAIna(:,:,:),2);
BsaScrIna(:,:)=nanmean(BSAScrIna(:,:,:),2);
clearvars bsaAnim bsaScrAnim bsaIna bsaScrIna s h Harm BSAAnim BSAScrAnim BSAIna BSAScrIna

OBM(:,1)=BsaAnim;OBM(:,2)=BsaIna;OBM(:,3)=BsaScrAnim;OBM(:,4)=BsaScrIna;
D=[2 2];
[e,Results.Diff.AnovaF,c,Results.Diff.AnovaP,efs,Results.Diff.Anovadfs]=repanova(OBM,D);
clearvars D e c efs