library(quantreg)
options("scipen"=30, "digits"=4)
digits.option <- 4

path.data <- 'C:/Users/etna/Desktop/Etienne_work/Data'
if (file.exists(file.path(path.data))){
    path.data <- path.data
}else{
    path.data <- '//ulysse/users/echamayou/Bureau/Etienne_work/Data'
}
path.data.disp <- file.path(path.data, 'data_gasoline/data_built/data_dispersion/data_csv')
path.file <- file.path(path.data.disp, 'df_pair_comp_no_mc.csv')

market.dist <- 5

sink(file.path(path.data.disp,
               paste(c('R_pair_regs_', market.dist, 'km.txt'), collapse = '')))

data <- read.csv(path.file)
ppd <- data
#ppd <- subset(data, !is.na(pct_rr) &
#                    !is.na(abs_mean_spread) &
#                    !is.na(distance))
#ppd <- na.omit(data)

## Prepare data
#ppd <- subset(ppd, cat == 'no_mc')
#ppd <- subset(ppd, (group_1 != group_2) & (group_last_1 != group_last_2))
#ppd$sc_500  <- ifelse(ppd$distance <= 0.50, 1, 0)
#ppd$sc_750  <- ifelse(ppd$distance <= 0.75, 1, 0)
#ppd$sc_1000 <- ifelse(ppd$distance <= 1.00, 1, 0)

ppd <- subset(ppd, distance <= market.dist)
ppd.nodiff <- subset(ppd, abs_mean_spread <= 0.01)

# Preliminary OLS

oilind <- c('OIL', 'INDEPENDENT')
ls.all <- list(ppd = ppd,
               ppd.sup = subset(ppd, (group_type_1 == 'SUP') &
                                     (group_type_2 == 'SUP')),
               ppd.oil.ind = subset(ppd, (is.element(group_type_1, oilind)) &
                                         (is.element(group_type_2, oilind))),
               ppd.dis = subset(ppd, (group_type_1 == 'DIS') &
                                     (group_type_2 == 'DIS')),
               ppd.sup.dis = subset(ppd, ((group_type_1 == 'SUP') &
                                          (group_type_2 == 'DIS')) |
                                         ((group_type_1 == 'DIS') &
                                          (group_type_2 == 'SUP'))),
               ppd.oil.sup = subset(ppd, ((group_type_1 == 'SUP') &
                                          (is.element(group_type_2, oilind))) |
                                         ((is.element(group_type_1, oilind)) &
                                          (group_type_2 == 'SUP'))))

ls.nd <- lapply(ls.all, function(ppdtemp){
  ppdtemp <- subset(ppdtemp, abs_mean_spread <= 0.01)
})

ls.temp <- ls.all

print('Preliminary OLS regs')
ls.temp.names <- names(ls.temp)
for (name in ls.temp.names) {
  cat(replicate(20, '-'))
  cat("\n", name, "\n")
  ppdtemp <- ls.temp[[name]]
  fitmeanspread <- lm(abs_mean_spread ~ distance, ppdtemp)
  fitpctrrdist <- lm(pct_rr ~ distance, ppdtemp)
  cat("\n", "abs mean spread", "\n")
  #print(summary(fitmeanspread, digits = digits.option))
  print(summary(fitmeanspread, digits = digits.option)$coefficients[2,])
  cat("\n", "pct rr", "\n")
  #print(summary(fitpctrrdist, digits = digits.option))
  print(summary(fitpctrrdist, digits = digits.option)$coefficients[2,])
  
  cat("\n", "OLS and Quantile regs (loop on same corner dist and quantiles)", "\n")
  sc_distance <- 1000
  sc <- paste("sc_", sc_distance, sep="")
  res_lm <- lm(pct_rr ~ get(sc), ppdtemp)
  #print(summary(res_lm))
  #print('Simple OLS')
  #print(summary(res_lm, digits = digits.option)$coefficients[2,1:4])
  ls.qres <- list(summary(res_lm, digits = digits.option)$coefficients[2,1:4])
  for(tau_option in c(0.5, 0.75)) {
    res_rq <- rq(formula = pct_rr ~ get(sc), tau = tau_option, data = ppdtemp)
    #cat('\n')
    #print(summary(res_rq))
    #print(paste('Quantile:', tau_option))
    #print(summary(res_rq, digits = digits.option)$coefficients[2,1:4])
    ls.qres[[length(ls.qres)+1]] <- summary(res_rq)$coefficients[2,1:4]
  }
  df.qres <- data.frame(x = matrix(unlist(ls.qres), nrow=length(ls.qres), byrow=T))
  colnames(df.qres) <- c('coef', 'std', 'tval', 'pval')
  #rownames(df.qres) <- c('OLS', 'Q25', 'Q50', 'Q75', 'Q90')
  rownames(df.qres) <- c('OLS', 'Q50', 'Q75')
  print(df.qres)
  
}

# OLS and quantile regressions with same corner variables



## Kolmogorov Smirnov tests
## https://stat.ethz.ch/R-manual/R-devel/library/stats/html/ks.test.html
#
#cat('\n')
#print('KS test (loop on same corner dist and hypotheses)')
#for(sc_distance in c(0.5, 0.75, 1.00)) {
#  cat('\n')
#  print(paste(replicate(40, '-'), collapse = ''))
#  print(paste('Distance:', sc_distance))
#  for(alternative_option in c('two.sided', 'less', 'greater'))
#  {
#    rr.close <- ppd.nodiff[which(ppd.nodiff$distance <= sc_distance), c('pct_rr')]
#    rr.further <- ppd.nodiff[which(ppd.nodiff$distance > sc_distance & ppd.nodiff$distance <= market.dist), c('pct_rr')]
#    res_ks <- ks.test(rr.close, rr.further, alternative = c(alternative_option))
#    print(res_ks)
#  }
#}
#

sink()
#unlink(file.path(path.data.disp, 'R_pair_regs.txt'))
closeAllConnections()

## BACKUP
#cat("\n", "OLS and Quantile regs (loop on same corner dist and quantiles)", "\n")
#for(sc_distance in c(0.5, 0.75, 1.00)) {
#  cat('\n')
#  print(paste(replicate(40, '-'), collapse = ''))
#  print(paste('Distance:', sc_distance))
#  sc <- paste("sc_", 750, sep="")
#  res_lm <- lm(pct_rr ~ get(sc), ppd.nodiff)
#  #print(summary(res_lm))
#  print('Simple OLS')
#  print(summary(res_lm, digits = digits.option)$coefficients[2,1:4])
#  for(tau_option in c(0.25, 0.5, 0.75, 0.90))
#  {
#    res_rq <- rq(formula = pct_rr ~ get(sc), tau = tau_option, data = ppd.nodiff)
#    cat('\n')
#    # print(summary(res_rq))
#    print(paste('Quantile:', tau_option))
#    print(summary(res_rq, digits = digits.option)$coefficients[2,1:4])
#  }
#}
