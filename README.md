## My econ research repository

This repository contains the code of virtually all the economic research projects I have been or am currently working on. Some of them are not really meant to be public (tests, drafts etc) and are thus not listed or adequately described in the overview provided below.

----------

### code_gasoline_france

In 2007, a governmental website ([prix-carburants.gouv.fr](http://www.prix-carburants.gouv.fr)) was launched in France to increase transparency in the retail gasoline market. Data obtained from this website are used in two research projects:

- Consumer information and price dispersion ([Working paper](https://github.com/etiennecha/master_code/blob/master/papers/french_retail_gasoline_dispersion/report.pdf))
- Launch of the low cost chain "Total Access" by "Total" (a large oil company and historical gas station operator in France) and its impact on competition ([Working paper](https://github.com/etiennecha/master_code/blob/master/papers/french_retail_gasoline_total_access/report.pdf))

### code_supermarkets_france

Supermarkets typically cary several thousand products and implement promotions of various types which make price comparison an intricate issue. Even more than in the single product case (e.g. gasoline), it seems reasonable to except that the cost associated with an accurate price comparison leads a significant portion of consumers to give up searching and shop at random or following various rules of thumb.
This project aims at studying how price dispersion and levels vary with the degree of competition and demand characteristics across markets. A major source of data is the price comparison website ([quiestlemoinscher.com](http://www.quiestlemoinscher.com/)) launched by the supermarket chain Leclerc around 2006 with a view to prove the competitiveness of its prices as compared to other chains. More detail about the research project can be found [here](https://github.com/etiennecha/master_code/tree/master/code_supermarkets_france) and the following [document](https://github.com/etiennecha/master_code/blob/master/papers/french_supermarkets/report.pdf) describes supermarket chains in France and provide a brief analysis of competition based on store location and size vs. demand).

### code_physicians_france

The French national health insurance agency operates a website which lists physicians and prices. Data collected from the website are used to study physician locations and price levels (in the case of physicians with unregulated fees) compared to health demand approximated by population characteristics.

### code_insee

INSEE is the French national institute of statistics. It offers a lot of data at the municipality level with municipalities being identified by a unique code. The folder contains a module which allows to obtain this code from other information more commonly found such as city name, department, zip code etc. as well as various data extraction and processing scripts.

### code_maps

Small use cases of geographic data processing, and/or analysis (OSM data extraction, routing, display of Velib' bike availability etc.)

### code_test

Small tests of data display with Google Fusion Tables and Leaflet as well as wine price data scraping from large supermarket chains in France.
