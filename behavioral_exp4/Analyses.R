##----------------------------------------------------------------#
# INITIALISATION####
##----------------------------------------------------------------#
library('readxl')
library("writexl")
library('foreach')
library('doParallel')
library('psych')
library('dplyr')
library('tidyverse')

## Set working directory
thisFilePath<-rstudioapi::getSourceEditorContext()$path
thisDir = dirname(thisFilePath)
setwd(thisDir)

# Import data ####
df <- read_excel("AllResponses.xlsx")
df_list <- read_excel("List_Texforms_Exp3.xlsx")
summary(df)

# Optional, to restrict the analyses to the 350 images used in Experiment 3
filtered_df <- df %>%
  filter(stim %in% df_list$Stim)
rm(df, df_list)

df <- filtered_df
rm(filtered_df)
####

SDT_Animacy_CPS <- df %>%
  filter(Group == "CPS") %>%
  mutate(Hit = ifelse(Cat == "A" & check == 1, 1, 0)) %>%
  mutate(FA = ifelse(Cat == "I" & check == 0, 1, 0)) %>%
  mutate(Miss = ifelse(Cat == "A" & check == 0, 1, 0)) %>%
  mutate(CR = ifelse(Cat == "I" & check == 1, 1, 0)) %>%
  group_by(subject) %>%
  summarise(nHit = sum(Hit) + 0.5,
            nFA = sum(FA) + 0.5,
            nMiss = sum(Miss) + 0.5,
            nCR = sum(CR) + 0.5) %>%
  mutate(dPrime = psycho::dprime(nHit, nFA, nMiss, nCR)[["dprime"]]) %>%
  mutate(beta = psycho::dprime(nHit, nFA, nMiss, nCR)[["beta"]])

SDT_Animacy_GPS <- df %>%
  filter(Group == "GPS") %>%
  mutate(Hit = ifelse(Cat == "A" & check == 1, 1, 0)) %>%
  mutate(FA = ifelse(Cat == "I" & check == 0, 1, 0)) %>%
  mutate(Miss = ifelse(Cat == "A" & check == 0, 1, 0)) %>%
  mutate(CR = ifelse(Cat == "I" & check == 1, 1, 0)) %>%
  group_by(subject) %>%
  summarise(nHit = sum(Hit) + 0.5,
            nFA = sum(FA) + 0.5,
            nMiss = sum(Miss) + 0.5,
            nCR = sum(CR) + 0.5) %>%
  mutate(dPrime = psycho::dprime(nHit, nFA, nMiss, nCR)[["dprime"]]) %>%
  mutate(beta = psycho::dprime(nHit, nFA, nMiss, nCR)[["beta"]])

SDT_Animacy_Tex <- df %>%
  filter(Group == "Tex") %>%
  mutate(Hit = ifelse(Cat == "A" & check == 1, 1, 0)) %>%
  mutate(FA = ifelse(Cat == "I" & check == 0, 1, 0)) %>%
  mutate(Miss = ifelse(Cat == "A" & check == 0, 1, 0)) %>%
  mutate(CR = ifelse(Cat == "I" & check == 1, 1, 0)) %>%
  group_by(subject) %>%
  summarise(nHit = sum(Hit) + 0.5,
            nFA = sum(FA) + 0.5,
            nMiss = sum(Miss) + 0.5,
            nCR = sum(CR) + 0.5) %>%
  mutate(dPrime = psycho::dprime(nHit, nFA, nMiss, nCR)[["dprime"]]) %>%
  mutate(beta = psycho::dprime(nHit, nFA, nMiss, nCR)[["beta"]])

write_xlsx(SDT_Animacy_CPS,"D:/Minimal_features/Exp4/Results\\SDT_CPS.xlsx")
write_xlsx(SDT_Animacy_GPS,"D:/Minimal_features/Exp4/Results\\SDT_GPS.xlsx")
write_xlsx(SDT_Animacy_Tex,"D:/Minimal_features/Exp4/Results\\SDT_Tex.xlsx")

# If restricted to 350 stimuli:
write_xlsx(SDT_Animacy_CPS,"D:/Minimal_features/Exp4/Results\\SDT_CPS_listTex.xlsx")
write_xlsx(SDT_Animacy_GPS,"D:/Minimal_features/Exp4/Results\\SDT_GPS_listTex.xlsx")
write_xlsx(SDT_Animacy_Tex,"D:/Minimal_features/Exp4/Results\\SDT_Tex_listTex.xlsx")
