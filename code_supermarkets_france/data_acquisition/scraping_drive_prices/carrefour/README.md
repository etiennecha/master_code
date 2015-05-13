## Carrefour drive data

The daily collect of Carrefour drive prices started with a script dedicated to the collect of one store prices (Carrefour Market in Voisins le Bretonneux) on 2013/04/18 and lasted until 2013/11/28. 

The script was updated on 2013/11/29 to include promotions and ran until 2014/12/05. A change in the website then interupted the collect.

The latest script dates back to 2015/05/05. I have then started looking into the data and realized that:

 - the first version of the script had not captured promotions
 - both the first and second version did not capture product brand for most products (which inflates the number of products which cannot be differentiated in collected data because they have the same product title e.g. a bottle of water of 1L)
 - both the first (?) and second version did not go beyond the first product page i.e. only captured the first 100 products displayed for each subdepartments (work in progress: checking that this is the case and how bad it is for the representativeness of descriptive statistics des about price changes and promotions)
