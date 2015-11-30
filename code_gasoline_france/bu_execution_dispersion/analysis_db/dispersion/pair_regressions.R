library(quantreg)

data <- read.csv("C:\\Users\\etna\\Desktop\\Etienne_work\\Data\\data_gasoline\\data_built\\data_paper\\data_csv\\data_ppd.csv")
#data <- '//ulysse/users/echamayou/Bureau/Etienne_work/Data/data_gasoline/data_built/data_paper/data_csv/data_ppd_reg.csv'

ppd <- na.omit(data)
ppd.nodiff <- subset(ppd, abs(ppd$avg_spread) <= 0.02)

fitavgspread <- lm(abs_avg_spread ~ distance, ppd.nodiff)
fitpctrrdist <- lm(pct_rr ~ distance, ppd.nodiff)

summary(fitavgspread)
summary(fitpctrrdist)

#TODO: introduce controls for type of stations in pair and environment

fitpctrrsc <- lm(pct_rr ~ sc_500, ppd.nodiff)
fit25 <- rq(formula = pct_rr ~ sc_500, tau = 0.25, data = ppd.nodiff)
fit50 <- rq(formula = pct_rr ~ sc_500, tau = 0.5, data = ppd.nodiff)
fit75 <- rq(formula = pct_rr ~ sc_500, tau = 0.75, data = ppd.nodiff)
fit90 <- rq(formula = pct_rr ~ sc_500, tau = 0.90, data = ppd.nodiff)

summary(fitpctrrsc)
summary(fit25)
summary(fit50)
summary(fit75)
summary(fit90)
