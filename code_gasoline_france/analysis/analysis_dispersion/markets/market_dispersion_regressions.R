require(plm)
require(lmtest)

# todo: check with STATA
# http://www.people.hbs.edu/igow/GOT/
coeftest.cluster <- function(data, fm, cluster1, cluster2=NULL) {

  require(sandwich)
  require(lmtest)

  # Calculation shared by covariance estimates
  est.fun <- estfun(fm)
  # est.fun <- sweep(fm$model,MARGIN=2,fm$residuals,`*`)   

  # Need to identify observations used in the regression (i.e.,
  # non-missing) values, as the cluster vectors come from the full 
  # data set and may not be in the regression model.
  # I use complete.cases following a suggestion from 
  # Francois Cocquemas <francois.cocquemas@gmail.com>
  inc.obs <- complete.cases(data[,names(fm$model)])
  # inc.obs <- !is.na(est.fun[,1])
  # est.fun <- est.fun[inc.obs,]

  # Shared data for degrees-of-freedom corrections
  N  <- dim(fm$model)[1]
  NROW <- NROW(est.fun)
  K  <- fm$rank

  # Calculate the sandwich covariance estimate
  cov <- function(cluster) {
    cluster <- factor(cluster)

    # Calculate the "meat" of the sandwich estimators
    u <- apply(est.fun, 2, function(x) tapply(x, cluster, sum))
    meat <- crossprod(u)/N

    # Calculations for degrees-of-freedom corrections, followed 
    # by calculation of the variance-covariance estimate.
    # NOTE: NROW/N is a kluge to address the fact that sandwich uses the
    # wrong number of rows (includes rows omitted from the regression).
    M <- length(levels(cluster))
    dfc <- M/(M-1) * (N-1)/(N-K)
    dfc * NROW/N * sandwich(fm, meat=meat)
  }

  # Calculate the covariance matrix estimate for the first cluster.
  cluster1 <- data[inc.obs,cluster1]
  cov1  <- cov(cluster1)

  if(is.null(cluster2)) {
    # If only one cluster supplied, return single cluster
    # results
    return(coeftest(fm, cov1))
  } else {
    # Otherwise do the calculations for the second cluster
    # and the "intersection" cluster.
    cluster2 <- data[inc.obs,cluster2]
    cluster12 <- paste(cluster1,cluster2, sep="")

    # Calculate the covariance matrices for cluster2, the "intersection"
    # cluster, then then put all the pieces together.
    cov2   <- cov(cluster2)
    cov12  <- cov(cluster12)
    covMCL <- (cov1 + cov2 - cov12)

    # Return the output of coeftest using two-way cluster-robust
    # standard errors.
    return(coeftest(fm, covMCL))
  }
}

path.data <- 'C:/Users/etna/Desktop/Etienne_work/Data'
if (file.exists(file.path(path.data))){
    path.data <- path.data
}else{
    path.data <- '//ulysse/users/echamayou/Bureau/Etienne_work/Data'
}
path.data.disp <- file.path(path.data, 'data_gasoline/data_built/data_dispersion/data_csv')

file.names <- c('df_market_dispersion_3km_Raw_prices.csv',
                'df_market_dispersion_3km_Residuals.csv',
                'df_market_dispersion_1km_Residuals.csv',
                'df_market_dispersion_5km_Raw_prices.csv',
                'df_market_dispersion_5km_Residuals.csv',
                'df_market_dispersion_3km_Rest_Residuals',
                'df_market_dispersion_Stable_Markets_Raw_prices',
                'df_market_dispersion_Stable_Markets_Residuals')

# Loop on 1, 2, 4, 5, 7, 8
path.file <- file.path(path.data.disp, file.names[[1]])

data <- read.csv(path.file, colClasses=c('date'='Date'))

## restrict to one day per week
data$dow <- weekdays(data$date)
data <- data[data$dow == 'vendredi',]

data_before <- data[data$date <= "2012-07-01",]
data_after <- data[data$date >= "2013-02-01",]

nrow(data_before)
nrow(data_after)

dfList <- list(all=data, bf=data_before, af=data_after)
dfListNames <- names(dfList)
for (name in dfListNames) {
  print(name)
  cat('\n')
  df <- dfList[[name]]
  reg_range <- lm(range ~ cost + nb_comp, df)
  # print(summary(reg_range))
  reg_std <- lm(std ~ cost + nb_comp, df)
  # print(summary(reg_std))
  
  # Clustered std errors: one way
  df_plm <- plm.data(df,index=c("id","date"))
  reg_std_plm <- plm(std ~ cost + nb_comp, data = df_plm, model = 'pooling')
  G <- length(unique(df_plm$id))
  N <- length(df_plm$id)
  dfa <- (G/(G - 1)) * (N - 1)/reg_std_plm$df.residual
  # display with cluster VCE and df-adjustment
  date_c_vcov <- dfa * vcovHC(reg_std_plm, type = "HC0", cluster = "group", adjust = T)
  # print(coeftest(reg_std_plm, vcov = date_c_vcov))
  
  # Clustered std errors: two ways
  print(coeftest.cluster(df, reg_range, cluster1 = 'id', cluster2 = 'date'))
  print(coeftest.cluster(df, reg_std, cluster1 = 'id', cluster2 = 'date'))
}