clc
clear all
close all
main_folder=fullfile(fileparts(mfilename('fullpath')));
%%%%% Choose the experiment to analyze
% current_folder=fullfile(main_folder,'Data_Exp1');
% current_folder=fullfile(main_folder,'Data_Exp2');
% current_folder=fullfile(main_folder,'Data_Exp3');
%%%%%
Preprocess_folder=fullfile(current_folder,'Preprocess');
load(fullfile(Preprocess_folder,'FFT'));
subj=size(FTransform(1).Img,1);

n_gap=1;
n_bin=12;
limit=1251; % up to 50Hz

%% Compute Z-score averaged across participants and electrodes
%%%% Average the Fourier transform over electrodes and pre-allocate
meanPpt(1).Img=nanmean(FTransform(1).MeanSubj.Img,1);
meanPpt(1).Scramble=nanmean(FTransform(1).MeanSubj.Scramble,1);
Zscore(1).MoyElec.Img=zeros(1,size(meanPpt(1).Img,2));
Zscore(1).MoyElec.Scramble=zeros(1,size(meanPpt(1).Img,2));
%%%% Computing Z-score on each amplitudes up to 50Hz using 24 surrounding bins
for t = (n_bin+1+n_gap):limit
    MAllMoyElecImg=[meanPpt(1).Img(1,t-(n_bin+n_gap):t-n_gap-1) meanPpt(1).Img(1,t+n_gap+1:t+n_bin+n_gap)];
    MAllMoyElecScr=[meanPpt(1).Scramble(1,t-(n_bin+n_gap):t-n_gap-1) meanPpt(1).Scramble(1,t+n_gap+1:t+n_bin+n_gap)];
    %%%% Removing maximum and minimum
    MaxAllImg=max(MAllMoyElecImg);
    MinAllImg=min(MAllMoyElecImg);
    MaxAllScr=max(MAllMoyElecScr);
    MinAllScr=min(MAllMoyElecScr);
    for v=1:length(MAllMoyElecImg)
        if MAllMoyElecImg(1,v)==MaxAllImg || MAllMoyElecImg(1,v)==MinAllImg
            MAllMoyElecImg(1,v)=NaN;
        end
        if MAllMoyElecScr(1,v)==MaxAllScr || MAllMoyElecScr(1,v)==MinAllScr
            MAllMoyElecScr(1,v)=NaN;
        end
    end
    Zscore(1).MoyElec.Img(1,t) =  (meanPpt(1).Img(1,t) - (nanmean(MAllMoyElecImg,2))) / std(MAllMoyElecImg,0,2,'omitnan');
    Zscore(1).MoyElec.Scramble(1,t) =  (meanPpt(1).Scramble(1,t) - (nanmean(MAllMoyElecScr,2))) / std(MAllMoyElecScr,0,2,'omitnan');
    clearvars MAllMoyElecImg MAllMoyElecScr MaxAllImg MinAllImg MaxAllScr MinAllScr
end
clearvars meanPpt

%% Compute Z-score at each electrode averaged across participants
for e=1:size(FTransform,2)
    meanPpt(1).Img=FTransform(1).MeanSubj.Img(e,:);
    meanPpt(1).Scramble=FTransform(1).MeanSubj.Scramble(e,:);
    Zscore(1).Elec.Img(e,:)=zeros(1,size(meanPpt(1).Img,2));
    Zscore(1).Elec.Scramble(e,:)=zeros(1,size(meanPpt(1).Img,2));
    for t = (n_bin+1+n_gap):limit
        MAllMoyElecImg=[meanPpt(1).Img(1,t-(n_bin+n_gap):t-n_gap-1) meanPpt(1).Img(1,t+n_gap+1:t+n_bin+n_gap)];
        MAllMoyElecScr=[meanPpt(1).Scramble(1,t-(n_bin+n_gap):t-n_gap-1) meanPpt(1).Scramble(1,t+n_gap+1:t+n_bin+n_gap)];
        MaxAllImg=max(MAllMoyElecImg);
        MinAllImg=min(MAllMoyElecImg);
        MaxAllScr=max(MAllMoyElecScr);
        MinAllScr=min(MAllMoyElecScr);
        for v=1:length(MAllMoyElecImg)
            if MAllMoyElecImg(1,v)==MaxAllImg || MAllMoyElecImg(1,v)==MinAllImg
                MAllMoyElecImg(1,v)=NaN;
            end
            if MAllMoyElecScr(1,v)==MaxAllScr || MAllMoyElecScr(1,v)==MinAllScr
                MAllMoyElecScr(1,v)=NaN;
            end
        end
        Zscore(1).Elec.Img(e,t) =  (meanPpt(1).Img(1,t) - (nanmean(MAllMoyElecImg,2))) / std(MAllMoyElecImg,0,2,'omitnan');
        Zscore(1).Elec.Scramble(e,t) =  (meanPpt(1).Scramble(1,t) - (nanmean(MAllMoyElecScr,2))) / std(MAllMoyElecScr,0,2,'omitnan');
        clearvars MAllMoyElecImg MAllMoyElecScr MaxAllImg MinAllImg MaxAllScr MinAllScr
    end
    clearvars meanPpt
end

%% Computation Baseline-subtracted Amplitudes (BSA) for each subject at each electrode
for s=1:subj
    disp(s)
    for e=1:size(FTransform,2)
        BSA(s).Img(e,:)=zeros(1,size(FTransform(e).Img(s,:),2));
        BSA(s).Scramble(e,:)=zeros(1,size(FTransform(e).Img(s,:),2));
        
        BSA(s).Anim(e,:)=zeros(1,size(FTransform(e).Anim(s,:),2));
        BSA(s).ScrAnim(e,:)=zeros(1,size(FTransform(e).ScrAnim(s,:),2));
        BSA(s).Ina(e,:)=zeros(1,size(FTransform(e).Ina(s,:),2));
        BSA(s).ScrIna(e,:)=zeros(1,size(FTransform(e).ScrIna(s,:),2));
        for t = (n_bin+1+n_gap):limit
            MElecAllImg=[FTransform(e).Img(s,t-(n_bin+n_gap):t-n_gap-1) FTransform(e).Img(s,t+n_gap+1:t+n_bin+n_gap)];
            MElecAllScr=[FTransform(e).Scramble(s,t-(n_bin+n_gap):t-n_gap-1) FTransform(e).Scramble(s,t+n_gap+1:t+n_bin+n_gap)];
            
            MElecAllAnim=[FTransform(e).Anim(s,t-(n_bin+n_gap):t-n_gap-1) FTransform(e).Anim(s,t+n_gap+1:t+n_bin+n_gap)];
            MElecAllScrAnim=[FTransform(e).ScrAnim(s,t-(n_bin+n_gap):t-n_gap-1) FTransform(e).ScrAnim(s,t+n_gap+1:t+n_bin+n_gap)];
            MElecAllIna=[FTransform(e).Ina(s,t-(n_bin+n_gap):t-n_gap-1) FTransform(e).Ina(s,t+n_gap+1:t+n_bin+n_gap)];
            MElecAllScrIna=[FTransform(e).ScrIna(s,t-(n_bin+n_gap):t-n_gap-1) FTransform(e).ScrIna(s,t+n_gap+1:t+n_bin+n_gap)];
            
            MaxAllImg=max(MElecAllImg);
            MinAllImg=min(MElecAllImg);
            MaxAllScr=max(MElecAllScr);
            MinAllScr=min(MElecAllScr);
            
            MaxAllAnim=max(MElecAllAnim);
            MinAllAnim=min(MElecAllAnim);
            MaxAllScrAnim=max(MElecAllScrAnim);
            MinAllScrAnim=min(MElecAllScrAnim);
            MaxAllIna=max(MElecAllIna);
            MinAllIna=min(MElecAllIna);
            MaxAllScrIna=max(MElecAllScrIna);
            MinAllScrIna=min(MElecAllScrIna);
            for v=1:length(MElecAllImg)
                if MElecAllImg(1,v)==MaxAllImg || MElecAllImg(1,v)==MinAllImg
                    MElecAllImg(1,v)=NaN;
                end
                if MElecAllScr(1,v)==MaxAllScr || MElecAllScr(1,v)==MinAllScr
                    MElecAllScr(1,v)=NaN;
                end
                
                if MElecAllAnim(1,v)==MaxAllImg || MElecAllAnim(1,v)==MinAllImg
                    MElecAllAnim(1,v)=NaN;
                end
                if MElecAllScrAnim(1,v)==MaxAllScr || MElecAllScrAnim(1,v)==MinAllScr
                    MElecAllScrAnim(1,v)=NaN;
                end
                if MElecAllIna(1,v)==MaxAllImg || MElecAllIna(1,v)==MinAllImg
                    MElecAllIna(1,v)=NaN;
                end
                if MElecAllScrIna(1,v)==MaxAllScr || MElecAllScrIna(1,v)==MinAllScr
                    MElecAllScrIna(1,v)=NaN;
                end
            end
            BSA(s).Img(e,t) =  FTransform(e).Img(s,t) - (nanmean(MElecAllImg,2));
            BSA(s).Scramble(e,t) =  FTransform(e).Scramble(s,t) - (nanmean(MElecAllScr,2));
            
            BSA(s).Anim(e,t) =  FTransform(e).Anim(s,t) - (nanmean(MElecAllAnim,2));
            BSA(s).ScrAnim(e,t) =  FTransform(e).ScrAnim(s,t) - (nanmean(MElecAllScrAnim,2));
            BSA(s).Ina(e,t) =  FTransform(e).Ina(s,t) - (nanmean(MElecAllIna,2));
            BSA(s).ScrIna(e,t) =  FTransform(e).ScrIna(s,t) - (nanmean(MElecAllScrIna,2));
            clearvars MaxAllImg MinAllImg MaxAllScr MinAllScr MElecAllImg MElecAllScr
            clearvars MaxAllAnim MinAllAnim MaxAllScrAnim MinAllScrAnim  MElecAllAnim MElecAllScrAnim
            clearvars MaxAllIna MinAllIna MaxAllScrIna MinAllScrIna  MElecAllIna MElecAllScrIna
        end
    end
end
save(fullfile(Preprocess_folder,'BSA'),'BSA','Zscore')

