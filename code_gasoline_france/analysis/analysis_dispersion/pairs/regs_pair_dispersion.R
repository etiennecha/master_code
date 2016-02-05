library(quantreg)

path.data <- 'C:/Users/etna/Desktop/Etienne_work/Data'
#path.data <- '//ulysse/users/echamayou/Bureau/Etienne_work/Data'
path.file <- file.path(path.data, 'data_gasoline/data_built/data_dispersion/data_csv/df_pair_final.csv')
data <- read.csv(path.file)

# Prepare data
ppd <- na.omit(data)

ppd <- subset(ppd, cat == 'no_mc')
ppd <- subset(ppd, (group_1 != group_2) & (group_last_1 != group_last_2))

ppd$sc_500  <- ifelse(ppd$distance <= 0.50, 1, 0)
ppd$sc_750  <- ifelse(ppd$distance <= 0.75, 1, 0)
ppd$sc_1000 <- ifelse(ppd$distance <= 1.00, 1, 0)

ppd.nodiff <- subset(ppd, abs_mean_spread <= 0.01)

fitmeanspread <- lm(abs_mean_spread ~ distance, ppd.nodiff)
fitpctrrdist <- lm(pct_rr ~ distance, ppd.nodiff)
fitsc500 <- lm(pct_rr ~ sc_500, ppd.nodiff)

summary(fitmeanspread)
summary(fitpctrrdist)
summary(fitsc500)

#TODO: introduce controls for type of stations in pair and environment

sc <- paste("sc_", 750, sep="")
fitpctrrsc <- lm(pct_rr ~ get(sc), ppd.nodiff)
fit25 <- rq(formula = pct_rr ~ get(sc), tau = 0.25, data = ppd.nodiff)
fit50 <- rq(formula = pct_rr ~ get(sc), tau = 0.5, data = ppd.nodiff)
fit75 <- rq(formula = pct_rr ~ get(sc), tau = 0.75, data = ppd.nodiff)
fit90 <- rq(formula = pct_rr ~ get(sc), tau = 0.90, data = ppd.nodiff)

summary(fitpctrrsc)
summary(fit25)
summary(fit50)
summary(fit75)
summary(fit90)

# Kolmogorov Smirnov
# https://stat.ethz.ch/R-manual/R-devel/library/stats/html/ks.test.html

ks.test(ppd.nodiff[which(ppd.nodiff$distance <= 0.5), c('pct_rr')],
        ppd.nodiff[which(ppd.nodiff$distance > 0.5 & ppd.nodiff$distance <= 3),
                   c('pct_rr')])

ks.test(ppd.nodiff[which(ppd.nodiff$distance <= 0.5), c('pct_rr')],
        ppd.nodiff[which(ppd.nodiff$distance > 0.5 & ppd.nodiff$distance <= 3),
                   c('pct_rr')],
        alternative = c('greater'))

ks.test(ppd.nodiff[which(ppd.nodiff$distance <= 0.5), c('pct_rr')],
        ppd.nodiff[which(ppd.nodiff$distance > 0.5 & ppd.nodiff$distance <= 3),
                   c('pct_rr')],
        alternative = c('less'))

