clc
clear all
close all
main_folder=fullfile(fileparts(mfilename('fullpath')));
current_folder=fullfile(main_folder,'Data_Exp1');
data_folder=fullfile(current_folder,'Rawdata');
Preprocess_folder=fullfile(current_folder,'Preprocess');

filenames={'Sujet1_FM_24_20210325_124210.raw',...
    'Sujet2_WP_34_20210325_040655.raw',...
    'Sujet3_JG_30_20210326_113043.raw',...
    'Sujet4_GF_20_20210326_043018.raw',...
    'Sujet6_AC_28_20210408_031404.raw',...
    'Sujet8_HT_19_20210414_113602.raw',...
    'Sujet10_MG_23_20210420_034202.raw',...
    'Sujet11_GR_23_20210421_013954.raw',...
    'Sujet12_FVF_28_20210421_051426.raw',...
    'Subject13_CT_21_20210615_102705.raw',...
    'Subject14_RB_33_20220216_024709.raw',...
    'Subject15_MV_25_20220222_103501.raw'};
listeSubj=[1 2 3 4 6 8 10 11 12 13 13 14];
nb_trial=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16];

for s=1:length(filenames)
%% Read file
filename=cell2mat(filenames(s));
EEG=pop_readegi(fullfile(data_folder,filename));
name_folder=dir(fullfile(current_folder,'Data','Subject*'));
name_folder=natsortfiles(name_folder);
subj_folder=fullfile(current_folder,'Data',name_folder(s).name);
name=dir(fullfile(subj_folder,'Sujet*.mat'));
load(fullfile(subj_folder,name(1).name))
clearvars name_folder name

%% Bandpass filter using a butterworth filter
EEG=pop_tesa_filtbutter(EEG,.1,[],4,'highpass');  %zero-phase, 4th-order high pass butterworth filter allowing frequencies above .01 Hz
EEG=pop_tesa_filtbutter(EEG,[],100,4,'lowpass');  %zero-phase, 4th-order low pass butterworth filter allowing frequencies below 100 Hz

%% Rereference electrodes taking the average as reference
EEGOUT = pop_reref( EEG, [], 'refstate',0);  %%% OUTEEG or EEG
clearvars EEG

%% Extract start and end of each trials
cnt_b=0;
cnt_t=0;
for ev=1:length(EEGOUT.event)
    if (EEGOUT.event(ev).type==['BLC',num2str(cnt_b+1)])
        cnt_t=1;
        cnt_b=cnt_b+1;
    end
    for t=1:length(nb_trial)
        if cnt_t<10
            if (EEGOUT.event(ev).type==['TR',num2str(0),num2str(cnt_t)])
                blockStart(cnt_t,cnt_b)=EEGOUT.event(ev+1).latency;
                blockEnd(cnt_t,cnt_b)=EEGOUT.event(ev+2).latency;
                cnt_t=cnt_t+1;
            end
        elseif cnt_t>=10
            if (EEGOUT.event(ev).type==['TR',num2str(cnt_t)])
                blockStart(cnt_t,cnt_b)=EEGOUT.event(ev+1).latency;
                blockEnd(cnt_t,cnt_b)=EEGOUT.event(ev+2).latency;
                cnt_t=cnt_t+1;
            end
        end
    end
end
block=blockEnd-blockStart;
Scramble=sujet(1).freq(listeSubj(s),:);
Anim=sujet(1).block(listeSubj(s),:);
data=EEGOUT.data;
clearvars EEGOUT

%% Extract data trial per trial, for all, posterior or occipital electrodes
for t=1:16
    bl1(t,:)=blockStart(t,1)+2500:blockStart(t,1)+(27500-1);
    bl2(t,:)=blockStart(t,2)+2500:blockStart(t,2)+(27500-1);
    bl3(t,:)=blockStart(t,3)+2500:blockStart(t,3)+(27500-1);
    bl4(t,:)=blockStart(t,4)+2500:blockStart(t,4)+(27500-1);
    if Anim(1,1)==1 && Scramble(1,1)==1
        Data(s).Anim(:,:,t)=data(:,bl3(t,:));
        Data(s).Ina(:,:,t)=data(:,bl4(t,:));
        Data(s).ScrAnim(:,:,t)=data(:,bl1(t,:));
        Data(s).ScrIna(:,:,t)=data(:,bl2(t,:));
    elseif Anim(1,1)==1 && Scramble(1,1)==2
        Data(s).Anim(:,:,t)=data(:,bl1(t,:));
        Data(s).Ina(:,:,t)=data(:,bl2(t,:));
        Data(s).ScrAnim(:,:,t)=data(:,bl3(t,:));
        Data(s).ScrIna(:,:,t)=data(:,bl4(t,:));
    elseif Anim(1,1)==2 && Scramble(1,1)==1
        Data(s).Anim(:,:,t)=data(:,bl4(t,:));
        Data(s).Ina(:,:,t)=data(:,bl3(t,:));
        Data(s).ScrAnim(:,:,t)=data(:,bl2(t,:));
        Data(s).ScrIna(:,:,t)=data(:,bl1(t,:));
    elseif Anim(1,1)==2 && Scramble(1,1)==2
        Data(s).Anim(:,:,t)=data(:,bl2(t,:));
        Data(s).Ina(:,:,t)=data(:,bl1(t,:));
        Data(s).ScrAnim(:,:,t)=data(:,bl4(t,:));
        Data(s).ScrIna(:,:,t)=data(:,bl3(t,:));
    end
end
clearvars data
end
save(fullfile(Preprocess_folder,'Data'),'Data','-v7.3')
