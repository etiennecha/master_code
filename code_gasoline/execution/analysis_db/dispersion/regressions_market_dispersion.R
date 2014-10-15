importeddata = read.csv("C:\\Users\\etna\\Desktop\\Etienne_work\\Data\\data_gasoline\\data_built\\data_paper\\data_csv\\data_test.csv")

newdata <- na.omit(importeddata)

mclx <-
function(fm, dfcw, cluster1, cluster2){
library(sandwich)
library(lmtest)
cluster12 = paste(cluster1,cluster2, sep="")
M1 <- length(unique(cluster1))
M2 <- length(unique(cluster2))
M12 <- length(unique(cluster12))
N <- length(cluster1)
K <- fm$rank
dfc1 <- (M1/(M1-1))*((N-1)/(N-K))
dfc2 <- (M2/(M2-1))*((N-1)/(N-K))
dfc12 <- (M12/(M12-1))*((N-1)/(N-K))
u1 <- apply(estfun(fm), 2,
function(x) tapply(x, cluster1, sum))
u2 <- apply(estfun(fm), 2,
function(x) tapply(x, cluster2, sum))
u12 <- apply(estfun(fm), 2,
function(x) tapply(x, cluster12, sum))
vc1 <- dfc1*sandwich(fm, meat=crossprod(u1)/N )
vc2 <- dfc2*sandwich(fm, meat=crossprod(u2)/N )
vc12 <- dfc12*sandwich(fm, meat=crossprod(u12)/N)
vcovMCL <- (vc1 + vc2 - vc12)*dfcw
coeftest(fm, vcovMCL)}

cl <- function(dat,fm, cluster){
          attach(dat, warn.conflicts = F)
          library(sandwich)
          M <- length(unique(cluster))   
          N <- length(cluster)  	        
          K <- fm$rank		             
          dfc <- (M/(M-1))*((N-1)/(N-K))  
          uj  <- apply(estfun(fm),2, function(x) tapply(x, cluster, sum));
          vcovCL <- dfc*sandwich(fm, meat=crossprod(uj)/N)
          coeftest(fm, vcovCL) }

regtest <- lm(std ~ nb_comp + price, data = newdata)
cl(newdata, regtest, date)
cl(newdata, regtest, id)
mclx(regtest, 1, newdata$id, newdata$date)


#SITE <- "http://www.kellogg.northwestern.edu/faculty/petersen/"
#URLdata <- paste(SITE, "/htm/papers/se/test_data.txt", sep="")
#VarNames <- c("firmid", "year", "x", "y")
#test <- read.table(file=URLdata, col.names=VarNames)
#fm <- lm(y ~ x, data=test)
#
#mclx(fm,1, test$firmid, test$year)
