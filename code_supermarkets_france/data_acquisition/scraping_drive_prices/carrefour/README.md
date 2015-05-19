## Carrefour drive data

----------

### Scraping

The daily collect of Carrefour drive prices started with a script dedicated to the collect of one store prices (Carrefour Market in Voisins le Bretonneux) on 2013/04/18 and lasted until 2013/11/28. 

The script was updated on 2013/11/29 to include promotions and ran until 2014/12/05. A change in the website then interupted the collect.

The latest script dates back to 2015/05/05 and collects prices from several stores. 

Unfortunately, I have really started looking at the data only in 2015 and realized that:

 - The first version of the script had not captured promotions
 - Both the first and second version did not capture product brand for most products. Unfortunately, many products are not identified by the mere product title (e.g. a bottle of water of 1L) making inter-period comparison difficult.
 - Both the first (check it) and second version did not go beyond the first product page i.e. only captured the first 100 products displayed for each subdpartments.

### Data

Data captured with the first version of the script were not further processed (available on demand).

Data captured with the second version were cleaned and product brand was added (from future files) whenever it was possible. The result is a dataset of 2,109,682 lines for 323 days (out of ? if no day was missing between 2013/11/29  and 2014/12/05), hence an average 6,531 lines per day.  Importantly, this figure can not be read as the average number of products available at the stores since i) not all products were collected for above mentioned technical reasons ii) many products are listed under several department/sub-departments.

Data captured with the third (latest) version of the script have been cleaned and aggregated on 2015/05/19 (starting date is 2015/05/05 hence a length of 14 days). On 2015/05/05 and 06, the collect covered 10 stores. Since then it covers only 5 for no particular reason.

For each period covered, processed-data are stored (/are to be) in three files:

 - The first contains all lines
 - The second contains prices of products which are well identified at the store level (allows products to be listed several times by the same store but only if listed in distinct departments and/or sub-departments, only one line is then kept in this file)
 - The third contains the departments and sub-departments which list these well identified products (hence there are typically several lines for one product)

### Todo

Add brand to (for now only in df_dsd_voisins_2013_2014.csv):

- df_carrefour_voisins_2013_2014.csv
- df_prices_voisins_2013_2014.csv 

Add brand in 2015 data (separate from product title and harmonize) and create (unique) product and price datasets.

### Analysis (in progress)

With 2013-2014 data:

- Check how many product prices are (likely) missing vs. 2015 on (also check the nb/share of promotions) i.e. how bad the missing product issue and product identification problems are.
- Analyse timing/length of promotions and price changes (by departments/sub-departments?/brands?)
- Analyse promotion types and amount (by dpt etc.)

With 2015 data:

- Compare store prices (close and far? collect all store prices on a (few) given day(s) ?)
- Compare store promotion strategies
