## Auchan drive data

----------

### Scraping

The daily collect of Auchan drive prices started with a script dedicated to the collect of one store prices (Auchan in Velizy) on 2012/11/22. The first version of the script ran until 2013/04/11.

The script was updated on 2013/04/11 to collect data in more robust way and ran until 2013/08/09. A change in the website then interrupted the collect.

A third version of the script was short live (2013/12/12 to 2014/01/29).

The script was run with another store, Auchan Plaisir, from 2013/06/27 to 2013/08/08. There is consequently about 1 month and a half of data with both Auchan Plaisir and Auchan Velizy (both stores are located in Western Paris ).

The latest script dates back to 2015/05/06 and collects prices from several stores. 

### Data

Data collected with the first version of the script have a few flaws. Some products were collected with no information for sub-department. Investigations have suggested that these lines could be simply ignored. A somewhat more problematic issue is that some products were recorded with sub-departments while they shouldn't have (on top of the right sub-departments). The issue has been partially solved by comparison with more recent files and manual corrections.

Data collected with the second version of the script do not appear to have significant flaws. A small issue is the fact that some products under promotions are to be listed once with the regular price and once with the promotion price.

For each period covered, processed-data are stored (/are to be) in three files:

 - The first contains all lines
 - The second contains prices of products which are well identified at the store level (allows products to be listed several times by the same store but only if listed in distinct departments and/or sub-departments, only one line is then kept in this file)
 - The third contains the departments and sub-departments which list these well identified products (hence there are typically several lines for one product).
