
## Scraped data 2011-2014

The following folder contains scripts used to aggregate and clean files created to store data scraped from the French gasoline price comparison website [prix-carburants.gouv.fr](http://prix-carburants.gouv.fr). On the one hand, a script was run on a daily basis between September 4, 2011 and December 4, 2014 to collect gas prices and station brands. Other scripts were run a few times over the period to obtain the location of the stations (address, gps coordinates) and their amenities.

Each gas station is identified by an 8 digit id assigned by the website (first five digits are the gas station zip code and the three last digits appear to simply reflect the order of registration for the given zip code e.g. first station to register in Paris' first district was assigned 75001001). As it turns out, in many cases, gas stations have been registered several over the period. It is therefore a priori not reasonable to interpret the disappearance of a gas station as a business termination. An effort is thus undertaken to reconcile ids which are found to refer to the same gas station. However, since gas stations which have sold less than 500m3 of gasoline are not required to keep prices posted on the website, data obtained are not fit for entry/exit analysis.

A brief description of the formatting process is provided below. The general philosophy is that each script produces either an intermediary output, which is then used by another script, or a final output. The process is organised and described in steps (titles below), the order of which matters. However, scripts can be executed in any order within each step.

----------

### Data aggregation

- build_master_price_raw: aggregates daily prices files in one python dictionary stored as json. The components of the latter are prices (observed price), dates (date on which price observed was set), brand (observed station brand i.e. station chain to which it belongs) and station info (one dict by station containing city and station name: information is overwritten if found different). The script actually generates two dictionaries/json files: one which contains diesel prices, and one which contains unleaded gas prices (sp95 and sp95_e10, a mix of gas and ethanol).

- build_master_info_raw: aggregates station info files in a dictionary (keys are station ids) stored as json which contains station amenities, opening days/hours, a dummy signaling highway gas stations, gps coordinates, and available gasoline types.

### Data corrections

- fix_master_info: harmonizes information and corrects some minor data issues (e.g. no address or invalid address)

- fix_master_price_diesel: uses dates at which prices are set to fill missing observations, detects and corrects price inconsistencies when possible (price too high/low, too high price variations, too rigid prices). The same processes are applied to unleaded prices in fix_master_price_gas.

### Creation of intermediary station info dataframes

- get_df_brand_activity: generates a dataframe which contains station brands (i.e. retail chains to which they belong) including changes (new brand and date of change), and their periods of activity.

- get_df_characteristics: generates a dataframe to describe station location, amenities, opening hours, gps, presence on highway.

- get_df_insee_codes: generates a dataframe which contains insee codes, which are found based on gas station zip codes and city names

- get_df_geocoding: generates a dataframe which contains gps coordinates obtained via station address geocoding with google geocoding API. Indeed, gps coordinates provided by the governmental website are found to be relatively inaccurate.

### Creation of info and price dataframes

- get_df_prices: generates two dataframes which respectively contain diesel prices before and after tax (todo: unleaded)

- get_df_info: generates a station info dataframe through the merger of intermediate station info dataframes

### Reconcilation of duplicates

- get_reconciled_duplicates: reconcile duplicate ids. Station entries are merged (price series, brands etc.) and stored under the most recent ids. Id reconciliations are stored to allow interaction with other sources (useless though?).