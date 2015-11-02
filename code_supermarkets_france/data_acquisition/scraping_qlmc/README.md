## QLMC Scraped data (2015)

This repository contains the code used to collect price data from the comparison website ([quiestlemoinscher.com](http://www.quiestlemoinscher.com/)) operated by the French retail group Leclerc. Prices were collected once in March 2015 (so far).
The website offers the possibility to compare prices between a given Leclerc store and one of its competitors (within a selection made by comparison website). An overall result is displayed as a percentage, which takes into account prices of all products available at both store in the website's data  (no weighting). The website also offers the possibility to create and compare bundles of goods.
Data obtained through the scraping of the website include a sample of prices at c. 1,800 supermarkets and hypermarkets across France in March 2015.

The first section provides a brief description of available data. The Scripts section gives an overview of the code contained in this repository.

----------

### Data

todo: add variables names of each file

- df_prices: contains all scraped prices
- df_stores: contains all stores for which prices were scraped
- df_stores_final: contains stores with insee codes and lsa_identifiers (allows matching with lsa store characteristic information)
- df_qlmc_competitors: contains all pairs of competitors as defined on the price comparison website, and the comparison result displayed on the website when the pair has been scraped

----------

### Scripts

#### Scraping

- scrap_leclerc_stores : fetches leclerc store identifiers by region and saves them in dict_reg_leclerc_stores.json (dictionary keys are regions).
- scrap_leclerc_competitors : fetches leclerc competitor identifiers of each leclerc store and saves them in dict_leclerc_comp.json (dictionary keys are leclerc store identifiers).
- scrap_all_comparisons: fetches price comparisons (i.e. prices of both stores through a double loop: each competitor of each leclerc store. However, in order to minimize the number of queries, price comparisons of pairs composed by stores which have already been collected previously (as parts of other pairs) are not fetched. This implies that scraped data obtained are (most likely) a subset of the data collected by Leclerc. Price comparisons are stored in one dictionary by region (e.g. dict_reg_comparisons_alsace.json ).

### Formatting

- check_pairs_not_scraped: gets a list of pairs not scraped (as a result of the minimization of scraping queries)
- build_df_qlmc_comparisons: contains all comparisons displayed on QLMC website (incl. stores' gps coordinates) at the time and the result (nb products compared, percent difference) for those which ended up being scraped
- build_df_prices: loops on dictionaries containing price comparisons and stores prices in one dataframe by region. The latter are then merged to build a dataframe with all scraped prices
- build_df_stores: builds store dataframe from dict_reg_leclerc_stores.json and dict_leclerc_comp.json
- get_store_insee_area: enrich df_stores with insee codes
- get_store_lsa_id: match stores in df_stores with df_lsa (database of supermarkets in France)
