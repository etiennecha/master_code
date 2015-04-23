## Generation of price statistics

This folder contains scripts which are used to generate tables containing variables which describe gas station prices. A brief overview of each script is provided below.

----------

### Study of individual price series: build_df_station_stats.py

This script generates variables which describe the price series of each station present in the data. The focus is mainly on price rigidity i.e. measure of the frequency and size of price changes, detection of repeated inverse changes (which could reflect promotions as well as an obfuscation strategy etc.).

This script does not contain information regarding the price level ("station fixed effect") and its changes over time. These are (to be) covered in the scripts dedicated to price cleaning (should it be included in this folder?) and to the detection of price policy changes.

This script may generate aggregate measures regarding the daily volume of price changes and rigidty over time.

### Study of pairs of competitors: build_df_station_stats.py

This script generates variables which seek to describe price competition between stations which are likely share potential customers (essentially based on distance as the crow flies). 

Key variables include the average spread (difference in gas station fixed effects), its standard deviation (volatility) and rank reversals (cf paper for more details). Importantly, information regarding the frequency of rank reversals, their length and value are added so as to allow a documented discussion regarding the economic significance of price dispersion. 

Also, variables are generated with a view to describe competition between pairs of stations which display very similar patterns of prices.  These variables are meant to allow for an informed discussion as to whether we observe close competition or collusion.

### Study of market dispersion: build_df_dispersion.py

This script generates variables which seek to describe price competition between stations which operate in the same market. Variables accounting for market price dispersion are generated with various definitions of markets so as to allow robustness checks. The purpose is to allow for an investigation of the determinants of price dispersion: local market characteristics, cost level and variations, number of competitors etc.
