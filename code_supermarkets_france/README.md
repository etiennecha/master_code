## Supermarkets in France

Supermarkets typically cary several thousand products and implement promotions of various types which make price comparison an intricate issue. Even more than in the single product case (e.g. gasoline), it seems reasonable to except that the cost associated with an accurate price comparison leads a significant portion of consumers to give up searching and shop at random or following various rules of thumb.
This project aims at studying how price dispersion and levels vary with the degree of competition and demand characteristics across markets. The characterization of markets is a crucial issue and its influence on results is thus to be thoroughly analyzed and discussed (in progress). The following sections describe the sources of data used in the project, emphasizing their pros and cons.

----------

### Prices from Quiestlemoinscher.com

[Quiestlemoinscher.com](http://www.quiestlemoinscher.com) (literally "who is the cheapest") is a price comparison website launched by the supermarket chain Leclerc in 2006. 

Prior to 2012, prices from a sample of stores from the largest retail chains in France were collected and used to compute brand price indexes. This was used by Leclerc to advertise its low price policy. Price were made available on the website in large pdf files. They are built into a large database in the following project. 

Since 2012, the website offers the possibility to compare each Leclerc to some of its potential competitors. An index is computed based on a sample of products, and the possibility is offered to make one's own comparison by chosing products within the available sample. All pairs were scraped once to build a database.

The main interest of such data is the fact that product names have been harmonized. Indeed, data collected directly from retail chain websites online typically do not contain barcodes and it is then difficult to compare prices across stores as product names are subject to small variations.
Shortcomings include the fact that promotions are typically excluded, that price samples chosen can be manipulated by Leclerc, and that the absence of data about quantities sold does not offer the opportunity to weigh prices when comparing.

### Prices from drive stores

The development of "drive" stores dates back to 2007. Most retail French chains have since then largely advertised "drive" as a way to benefit from low prices posted by traditional outlets while gaining on flexibility. Indeed, "drive" offers the opportunity to order on the internet and collect purchases in a very flexible way (vs. home delivery which typically requires to be at home over a large time slot). As a consequence, prices of virtually all products in physical stores to which a "drive" is attached are posted on the internet.

Price data collected drom drive websites offer the opportunity to observe all prices posted by a store over time, including promotions. On the other hand, comparison between stores is difficult as product names need to be harmonized. Drive price data are thus somewhat complementary with data obtained from quiestlemoinscher.com.

### Store data purchased from LSA

LSA is a firm that collects and sells data about the French supermarket industry. Data about French supermarkets, hypermarkets and hard discount stores were purchased from them so as to obtain exact store locations, and various store characteristics such as store surface, number of checkouts, employees, parking slots etc. (The following [document](https://github.com/etiennecha/master_code/blob/master/papers/french_supermarkets/report.pdf) describes supermarket chains in France and provide a brief overview of competition based on store location and size vs. demand).

### Other sources

Data about store locations and characteristics were collected from retail store websites (and from OpenStreetMap) but are currently unused. Data purchased from LSA have been preferred in the analysis as they tend to be more comprehensive and/or accurate.
