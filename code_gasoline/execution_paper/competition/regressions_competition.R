library(plm)

#path.dir.data <- "C:\\Users\\etna\\Desktop\\Etienne_work\\Data"
path.dir.data <- "W:\\Bureau\\Etienne_work\\Data"
path.file.data <- "\\data_gasoline\\data_built\\data_paper\\data_csv\\price_panel_data.csv"
full.path <- paste(path.dir.data, path.file.data, sep = "")
df.price <- read.csv(full.path, encoding = "UTF-8")
head(df_price)

#df.price <- plm.data(df.price, indexes = c("id", "date))
#http://stackoverflow.com/questions/3169371/large-scale-regression-in-r-with-a-sparse-feature-matrix

library(MatrixModels)
res <- glm4(formula = price ~ factor(id) + factor(date), data = df_price, sparse = TRUE)
str(res, max.lev = 4)
length(res@pred@coef)
res@pred@coef[0:10]

## To see more
example(glm4)

## RESULTS
#res@pred@X@Dimnames[2]
#plot(res@pred@coef[seq(length=500, from=length(res@pred@coef)-500+1, by=1)], type = "o")

# Check how to create dataframe... can use aschar but not clear how to get list of variables

# TODO: get estimated coeffs and use to predict cleaned prices in pandas
