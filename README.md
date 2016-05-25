## My econ research repository

This repository contains the code of virtually all the economic research projects I have been or am currently working on. 

----------

### Competition on the French retail gasoline market

The code_gasoline_france folder contains code used to collect, process and analyse data of two research projects:


- Price dispersion in the French retail gasoline market ([Working paper](https://github.com/etiennecha/master_code/blob/master/papers/french_retail_gasoline_dispersion/french_retail_gasoline_dispersion.pdf))
- Rebranding in the French retail gasoline market: local competitive effects of price decreases ([Working paper (update soon!)](https://github.com/etiennecha/master_code/blob/master/papers/french_retail_gasoline_total_access/french_retail_gasoline_total_access.pdf))

The main source of data is the governmental website ([prix-carburants.gouv.fr](http://www.prix-carburants.gouv.fr)). It was launched in 2006 by the French governement with a view to improve price transparency in the retail gasoline market.


### Competition between French grocery stores

The code_supermarkets_france folder contains code used to collect, process and analyse data described in:


- Competition between French grocery stores: Evidence from a price comparison website ([Working paper](https://github.com/etiennecha/master_code/blob/master/papers/french_supermarkets_competition/french_supermarkets_competition.pdf))

Supermarkets typically cary several thousand products and implement promotions of various types which make price comparison an intricate issue. Even more than in the single product case (e.g. gasoline), the cost of an accurate price comparison can be expected to easily lead consumers to shop at random or follow various rules of thumb. This project aims at studying how price dispersion and levels vary with the degree of competition and demand characteristics across markets. The main source of data is the price comparison website ([quiestlemoinscher.com](http://www.quiestlemoinscher.com/)) launched by the supermarket chain Leclerc around 2006 with a view to prove the competitiveness of its prices.

### Physician fees and locations in Paris

The code_physicians_france folder contains code used to collect, process and analyse data described in:

- Physician fees and locations in Paris ([Note](https://github.com/etiennecha/master_code/blob/master/papers/french_physicians/report.pdf))

The French national health insurance agency operates a website ([annuairesante.ameli.fr](http://annuairesante.ameli.fr/)) which lists physicians and prices. Data were collected from the website in 2014 to study physician locations and price levels (in the case of physicians whose fees are not regulated).

### Other

- code_insee : INSEE is the French national institute of statistics. It offers a lot of data at the municipality level with municipalities being identified by a unique code. The folder contains a module which allows to obtain this code from other information more commonly found such as city name, department, zip code etc. as well as various data extraction and processing scripts.
- code_test : small tests of data display with Google Fusion Tables and Leaflet, wine price data scraped from large supermarket chains in France etc.
- code_maps : small use cases of geographic data processing, and/or analysis e.g. OSM data extraction, routing, display of Velib' bike availability etc.
