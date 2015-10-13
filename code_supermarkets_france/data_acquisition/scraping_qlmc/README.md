## QLMC Scraped data (2015)

This repository contains the code used to collect price data from the comparison website ([quiestlemoinscher.com](http://www.quiestlemoinscher.com/)).

----------

### scraping

- scrap_leclerc_stores : gets leclerc identifiers by region and save them in dict_reg_leclerc_stores.json
- scrap_leclerc_competitors : gets leclerc competitor identifies by region and save them in dict_leclerc_comp.json
- scrap_all_comparisons: gets price comparisons (not exhaustive, minimum required to observe all listed leclerc and competitors at least once) and stores them in one dict by region (e.g. dict_reg_comparisons_alsace.json ).

### formatting

- check_pairs_not_scraped: gets a list of pairs not scraped (as a result of the minimization of scraping queries)
- build_df_qlmc_comparisons: contains all comparisons displayed on QLMC website (incl. stores' gps coordinates) at the time and the result (nb products compared, percent difference) for those which ended up being scraped
- build_df_region: loops on dictionaries containing price comparisons and stores prices in one dataframe by region
- build df_region: concatenate region dataframes in one dataframe
- build_df_stores: builds store dataframe from dict_reg_leclerc_stores.json and dict_leclerc_comp.json
- get_store_insee_area: enrich df_stores with insee codes
- get_store_lsa_id: match stores in df_stores with df_lsa (database of supermarkets in France)

Caution: need to take into account pairs which were not scraped due to the wish to minimize the number of scraping queries when analysing competitors picked by Leclerc for each of its stores.
