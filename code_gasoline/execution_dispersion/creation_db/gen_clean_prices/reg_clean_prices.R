library(plm)
library(MatrixModels)

#path.dir.data <- "C:\\Users\\etna\\Desktop\\Etienne_work\\Data"
path.dir.data <- "W:\\Bureau\\Etienne_work\\Data"

#path.file.data <- "\\data_gasoline\\data_built\\data_paper\\data_csv\\price_panel_data.csv"
#path.file.data.out <- "\\data_gasoline\\data_built\\data_paper\\data_csv\\price_cleaned_R.csv"
path.file.data <- "\\data_gasoline\\data_built\\data_paper\\data_csv\\price_panel_data_light.csv"
path.file.data.out <- "\\data_gasoline\\data_built\\data_paper\\data_csv\\price_cleaned_light_R.csv"

full.path <- paste(path.dir.data, path.file.data, sep = "")
full.path.out <- paste(path.dir.data, path.file.data.out, sep = "")

df.price <- read.csv(full.path, encoding = "UTF-8")
head(df.price)
nrow(df.price)
#summary(df.price)

# REGRESSION
#http://stackoverflow.com/questions/3169371/large-scale-regression-in-r-with-a-sparse-feature-matrix
res <- glm4(formula = price ~ factor(id) + factor(date), data = df.price, sparse = TRUE)
str(res, max.lev = 4)

# RESULTS (Not clear that much value... check alternatives)
# Inspect result help: example(glm4)
df.coeffs <- data.frame(res@pred@X@Dimnames[[2]], res@pred@coef)
head(df.coeffs)
tail(df.coeffs)
#plot(res@pred@coef[seq(length=500, from=length(res@pred@coef)-500+1, by=1)], type = "o")

# Residuals
price.resid <- resid(res)
length(price.resid) 
# 5390749 => question: which?

# BUILD DF FOR OUTPUT
df.price.nona <- df.price[!is.na(df.price$price),]
df.price.nona['price.cl'] <- price.resid
#plot(df.price.nona[df.price.nona$id_a == 1500007,]$price_cl, type = "o")

df.price.nona.out <- subset(df.price.nona, select = c(id, date, price, price.cl))
write.csv(df.price.nona.out, file = full.path.out, row.names = FALSE)
