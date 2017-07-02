## Drive data

This folder contains code used to scrap and clean price data from French supermarket chains Leclerc, Auchan and Carrefour. Such data allow to observe the price strategies, including promotions, of several (physical) stores over various time periods. 

Some general data issues:

- Except in the case of Leclerc, products do not come with an identifier, and information on products (e.g. product brand, name and size) is not always sufficient to uniquely identify a product (typically the picture would allow to disambiguate but was not collected). This implies that there can be two rows for a given store on a given day which are similar except for product price (resp. price per unit and promotion if any).
- One product can be listed under several sections and families within a store (not an issue)
- One product can be listed twice under the very same section/family within one store (probably an error from the store/website)
- A promotion can be signaled through a change in product name (or recorded with a new identified), in which case the promotion translates as a new product in the collected data

Generic data treatment (for each store):

- Elimination of trivial duplicates (completely similar rows)
- Elimination of products which can not be uniquely identified (not so bad given that the issue has a limited scale)
- Verification that products listed under several sections/families are the very same (product price/promotion)
- Once products are uniquely identified, a natural way to organize data is to build a price table (index = dates, columns = products) and a product table (index = section/family/product, columns = product info).
