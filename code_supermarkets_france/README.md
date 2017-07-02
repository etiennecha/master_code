## Supermarkets in France

Price comparison between supermarkets is particularly complex due to the number and variety of involved products. As a consequence, consumers may be tempted to follow rules of thumb or to give up searching for the best prices. This departure from standard economic theory hypotheses is bound to relax competition to an extent which is a priori difficult to measure for regulators. 

In a famous paper, Stigler (1961) has emphasised the relation between imperfect consumer information and price dispersion, namely the persistence of different prices within a market for a homogeneous good, in contradiction with the law of one price. This relation is of particular interest from an empirical prospect. It indeed implies that the difficulty of measuring consumer information, a key determinant of market efficiency, can be overcome by focusing on prices. 

The following repository contains scripts used to collect and study price data describing the French grocery store market over 2007-2015. The analysis aims at measuring local price levels and dispersion and studying how they vary with demand characteristics and HHI. The characterization of local markets is a crucial issue and its influence on results is thus carefuly evaluated. The following sections provide an overview of the data.

----------

### Prices from Quiestlemoinscher.com

[Quiestlemoinscher.com](http://www.quiestlemoinscher.com) ("who is the cheapest") is a price comparison website which was launched in 2006 by the French grocery store chain Leclerc (21% market share in France end of 2016 according to Kantar). 

Prior to 2012, stores from the largest national retail chains and products widely available were sampled in order to compute chain price indexes. Results were used by Leclerc to advertise its low price policy in mainstream media. Price records were made available on the price comparison website in pdf format. I collected the pdf files and extracted price records in order to build a first data set.

Since 2012, the website offers the possibility to compare each Leclerc store with a selection of its close competitors. An aggregate comparison is performed based on products the prices of which are available for both stores and the possibility is offered to restrict the set of products to consider. I scrapped all pairs onces, which constitutes a second data set.

A great merit of these data is that they contain readily usable price records from a large set of stores across France and for many products. Unfortunately, they also present some drawbacks such as the fact that they do not include promotions and store brand products.

### Prices from drive stores

The development of the drive concept (order online and collect products at a pickup point, generally next to a supermarket) in the French greocery industry dates back to 2007. Most retail French chains have since then largely advertised drive as a way to benefit from low prices posted by supermarkets while gaining on flexibility. Collecting prices from drive websites gives the opportunity to obtain exhaustive and accurated price observations. A drawback of these data is that barcodes are typically not provided and it is thus difficult to reconcile price records across chains.

### Store data purchased from LSA

LSA is a firm that collects and sells data about the French supermarket industry. Data about French supermarkets, hypermarkets and hard discount stores were purchased so as to obtain exact store locations, and various store characteristics such as store surface, number of checkouts, employees, parking slots etc. (The following [document](https://github.com/etiennecha/master_code/blob/master/papers/french_supermarkets/report.pdf) provides a brief overview of supermarket chains in France and competition based on store location and size vs. demand. Unfortunately, I cannot make these data available.

### Other sources

Data about store locations and characteristics were collected from retail store websites (and from OpenStreetMap) but are currently unused. Data purchased from LSA have been preferred in the analysis as they tend to be more comprehensive and/or accurate.
