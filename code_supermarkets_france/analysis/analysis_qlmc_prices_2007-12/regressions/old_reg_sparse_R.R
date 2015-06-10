library(plm)
library(MatrixModels)

#path.dir.data <- "C:\\Users\\etna\\Desktop\\Etienne_work\\Data"
path.dir.data <- "W:\\Bureau\\Etienne_work\\Data"

path.file.data <- "\\data_qlmc\\data_built\\data_csv\\df_qlmc_per_0.csv"
path.file.data.out <- "\\data_gasoline\\data_built\\data_csv\\df_qlmc_per_0_R.csv"

full.path <- paste(path.dir.data, path.file.data, sep = "")
full.path.out <- paste(path.dir.data, path.file.data.out, sep = "")

df.qlmc <- read.csv(full.path, encoding = "UTF-8") # latin1
head(df.qlmc)
nrow(df.qlmc)
summary(df.qlmc)

# REGRESSION
#http://stackoverflow.com/questions/3169371/large-scale-regression-in-r-with-a-sparse-feature-matrix
res <- glm4(formula = Prix ~ factor(Produit) + factor(Magasin), data = df.qlmc, sparse = TRUE)
str(res, max.lev = 4)

## RESULTS (Not clear that much value... check alternatives)
## Inspect result help: example(glm4)
#df.coeffs <- data.frame(res@pred@X@Dimnames[[2]], res@pred@coef)
#head(df.coeffs)
#tail(df.coeffs)

## Stores
#df.coeffs[2326:2668,]

## Residuals
#price.resid <- resid(res)
#length(price.resid) 
## 5390749 => question: which?
#
## BUILD DF FOR OUTPUT
#df.price.nona <- df.qlmc[!is.na(df.qlmc$Prix),]
#df.price.nona['price.cl'] <- price.resid
##plot(df.price.nona[df.price.nona$id_a == 1500007,]$price_cl, type = "o")
#
#df.price.nona.out <- subset(df.price.nona, select = c(id, date, price, price.cl))
#write.csv(df.price.nona.out, file = full.path.out, row.names = FALSE)
