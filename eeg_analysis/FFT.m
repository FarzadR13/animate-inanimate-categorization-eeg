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
load(fullfile(Preprocess_folder,'Data'));

%% Computation of the Fourier transform on the average of participants and trials
%%%% Average trials for each participants
for s=1:size(Data,2)
    blcAnim(:,:,s)=nanmean(Data(s).Anim(:,:,:),3);
    blcIna(:,:,s)=nanmean(Data(s).Ina(:,:,:),3);
    blcScrAnim(:,:,s)=nanmean(Data(s).ScrAnim(:,:,:),3);
    blcScrIna(:,:,s)=nanmean(Data(s).ScrIna(:,:,:),3);
end
%%%% Average participants
MblcAnim=nanmean(blcAnim,3);
MblcIna=nanmean(blcIna,3);
MblcScrAnim=nanmean(blcScrAnim,3);
MblcScrIna=nanmean(blcScrIna,3);
clearvars blcAnim blcIna blcScrAnim blcScrIna
%%%% Compute Fourier transform at each electrodes
Fs=1000;                    % Sampling frequency
T=1/Fs;                     % Sample time
L=round(size(MblcAnim,2));       % Length of signal
f = Fs/2*linspace(0,1,L/2);
for e=1:size(MblcAnim,1)
    Anim(1,:)=MblcAnim(e,:);
    Ina(1,:)=MblcIna(e,:);
    AnimScr(1,:)=MblcScrAnim(e,:);
    InaScr(1,:)=MblcScrIna(e,:);
    
    fftAnim(1,:)=fft(Anim(1,:))/L;
    fftIna(1,:)=fft(Ina(1,:))/L;
    fftScrAnim(1,:)=fft(AnimScr(1,:))/L;
    fftScrIna(1,:)=fft(InaScr(1,:))/L;
    
    FTransform(1).MeanSubj.Anim(e,:)=abs(fftAnim(1,1:L/2));
    FTransform(1).MeanSubj.Ina(e,:)=abs(fftIna(1,1:L/2));
    FTransform(1).MeanSubj.ScrAnim(e,:)=abs(fftScrAnim(1,1:L/2));
    FTransform(1).MeanSubj.ScrIna(e,:)=abs(fftScrIna(1,1:L/2));
    
    clearvars Anim Ina AnimScr InaScr fftAnim fftIna fftScrAnim fftScrIna
end
%%%% Average the Fourier transform of the two type of sequences (Animate and Inanimate) together
Img(:,:,1)=FTransform(1).MeanSubj.Anim;
Img(:,:,2)=FTransform(1).MeanSubj.Ina;
FTransform(1).MeanSubj.Img=nanmean(Img,3);
Scr(:,:,1)=FTransform(1).MeanSubj.ScrAnim;
Scr(:,:,2)=FTransform(1).MeanSubj.ScrIna;
FTransform(1).MeanSubj.Scramble=nanmean(Scr,3);
clearvars Img Scr

%% Compute Fourier transform for each participant, at each electrode
for s=1:size(Data,2)
    %%%% Average the trials for each participants
    blcAnim=nanmean(Data(s).Anim(:,:,:),3);
    blcIna=nanmean(Data(s).Ina(:,:,:),3);
    blcScrAnim=nanmean(Data(s).ScrAnim(:,:,:),3);
    blcScrIna=nanmean(Data(s).ScrIna(:,:,:),3);
    %%%% Compute Fourier transform at each electrode
    Fs=1000;                    % Sampling frequency
    T=1/Fs;                     % Sample time
    L=round(size(blcAnim,2));       % Length of signal
    f = Fs/2*linspace(0,1,L/2);
    for e=1:size(blcAnim,1)
        Anim(1,:)=blcAnim(e,:);
        Ina(1,:)=blcIna(e,:);
        AnimScr(1,:)=blcScrAnim(e,:);
        InaScr(1,:)=blcScrIna(e,:);
        
        fftAnim(1,:)=fft(Anim(1,:))/L;
        fftIna(1,:)=fft(Ina(1,:))/L;
        fftScrAnim(1,:)=fft(AnimScr(1,:))/L;
        fftScrIna(1,:)=fft(InaScr(1,:))/L;
        
        FTransform(e).Anim(s,:)=abs(fftAnim(1,1:L/2));
        FTransform(e).Ina(s,:)=abs(fftIna(1,1:L/2));
        FTransform(e).ScrAnim(s,:)=abs(fftScrAnim(1,1:L/2));
        FTransform(e).ScrIna(s,:)=abs(fftScrIna(1,1:L/2));
        %%%% Average the type of sequences
        Img(1,:)=FTransform(e).Anim(s,:);
        Img(2,:)=FTransform(e).Ina(s,:);
        FTransform(e).Img(s,:)=nanmean(Img,1);
        Scr(1,:)=FTransform(e).ScrAnim(s,:);
        Scr(2,:)=FTransform(e).ScrIna(s,:);
        FTransform(e).Scramble(s,:)=nanmean(Scr,1);
        clearvars Img Scr Anim Ina AnimScr InaScr fftAnim fftIna fftScrAnim fftScrIna
    end
 end
save(fullfile(Preprocess_folder,'FFT'),'FTransform','f')


