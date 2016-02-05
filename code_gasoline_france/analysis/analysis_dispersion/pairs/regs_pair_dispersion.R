library(quantreg)
options("scipen"=100, "digits"=1)
digits.option <- 3

path.data <- 'C:/Users/etna/Desktop/Etienne_work/Data'
if (file.exists(file.path(path.data))){
    path.data <- path.data
}else{
    path.data <- '//ulysse/users/echamayou/Bureau/Etienne_work/Data'
}
path.data.disp <- file.path(path.data, 'data_gasoline/data_built/data_dispersion/data_csv')
path.file <- file.path(path.data.disp, 'df_pair_final.csv')

market.dist <- 3

sink(file.path(path.data.disp,
               paste(c('R_pair_regs_', market.dist, 'km.txt'), collapse = '')))

data <- read.csv(path.file)

# Prepare data
ppd <- na.omit(data)

ppd <- subset(ppd, cat == 'no_mc')
ppd <- subset(ppd, (group_1 != group_2) & (group_last_1 != group_last_2))

ppd$sc_500  <- ifelse(ppd$distance <= 0.50, 1, 0)
ppd$sc_750  <- ifelse(ppd$distance <= 0.75, 1, 0)
ppd$sc_1000 <- ifelse(ppd$distance <= 1.00, 1, 0)

ppd.nodiff <- subset(ppd, abs_mean_spread <= 0.01)
ppd.nodiff <- subset(ppd, distance <= market.dist)

# Preliminary OLS

print('Preliminary OLS regs')
fitmeanspread <- lm(abs_mean_spread ~ distance, ppd.nodiff)
fitpctrrdist <- lm(pct_rr ~ distance, ppd.nodiff)
cat('\n')
print(summary(fitmeanspread, digits = digits.option))
cat('\n')
print(summary(fitpctrrdist, digits = digits.option))

# OLS and quantile regressions with same corner variables

cat('\n')
print('OLS and Quantile regs (loop on same corner dist and quantiles)')
for(sc_distance in c(0.5, 0.75, 1.00)) {
  cat('\n')
  print(paste(replicate(40, '-'), collapse = ''))
  print(paste('Distance:', sc_distance))
  sc <- paste("sc_", 750, sep="")
  res_lm <- lm(pct_rr ~ get(sc), ppd.nodiff)
  #print(summary(res_lm))
  print('Simple OLS')
  print(summary(res_lm, digits = digits.option)$coefficients[2,1:4])
  for(tau_option in c(0.25, 0.5, 0.75, 0.90))
  {
    res_rq <- rq(formula = pct_rr ~ get(sc), tau = tau_option, data = ppd.nodiff)
    cat('\n')
    # print(summary(res_rq))
    print(paste('Quantile:', tau_option))
    print(summary(res_rq, digits = digits.option)$coefficients[2,1:4])
  }
}

# Kolmogorov Smirnov tests
# https://stat.ethz.ch/R-manual/R-devel/library/stats/html/ks.test.html

cat('\n')
print('KS test (loop on same corner dist and hypotheses)')
for(sc_distance in c(0.5, 0.75, 1.00)) {
  cat('\n')
  print(paste(replicate(40, '-'), collapse = ''))
  print(paste('Distance:', sc_distance))
  for(alternative_option in c('two.sided', 'less', 'greater'))
  {
    rr.close <- ppd.nodiff[which(ppd.nodiff$distance <= sc_distance), c('pct_rr')]
    rr.further <- ppd.nodiff[which(ppd.nodiff$distance > sc_distance & ppd.nodiff$distance <= market.dist), c('pct_rr')]
    res_ks <- ks.test(rr.close, rr.further, alternative = c(alternative_option))
    print(res_ks)
  }
}

sink()
#unlink(file.path(path.data.disp, 'R_pair_regs.txt'))