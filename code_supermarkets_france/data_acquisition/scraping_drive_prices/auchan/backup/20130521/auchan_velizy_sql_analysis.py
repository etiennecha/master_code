import os
import json
import sqlite3
from datetime import date, timedelta
import datetime

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_stock_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

# path = r'C:\Users\etna\Desktop\Code\Auchan'
path = r'\\ulysse\users\echamayou\Etienne\Python_mydocs\Scrapping_Auchan'
json_folder = r'\auchan_velizy_json'
sql_folder = r'\auchan_velizy_sql'

conn = sqlite3.connect(path + sql_folder +r'\auchan_velizy_sql.db')
cursor = conn.cursor()

# see tables in sql master
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cursor.fetchall())

# see column infos of a table
cursor.execute("PRAGMA table_info(auchan_velizy)")
print cursor.fetchall()

# see number of records in a table
cursor.execute("SELECT COUNT(*) FROM auchan_velizy")
print cursor.fetchall()[0][0]

# get distinct values of a column
list_products = []
for row in cursor.execute("SELECT DISTINCT product_title FROM auchan_velizy"):
  list_products.append(row[0])

# count distinct values in a column
cursor.execute("SELECT COUNT(DISTINCT product_title) FROM auchan_velizy")
print cursor.fetchall()[0][0]

"""
# too slow
list_duplicates_2 = []
for row in cursor.execute("SELECT x.product_title, x.sub_department FROM auchan_velizy x\
                           WHERE EXISTS(SELECT NULL FROM auchan_velizy t\
                                        WHERE t.product_title = x.product_title\
                                        AND t.period = x.period\
                                        GROUP BY t.product_title\
                                        HAVING COUNT(*) > 1)\
                           ORDER BY x.product_title"):
  list_duplicates_2.append(row)


list_duplicates = []
for row in cursor.execute("SELECT product_title, sub_department, COUNT(product_title) AS NumOccurrences FROM auchan_velizy GROUP BY product_title, sub_department HAVING (COUNT(product_title) > 1)"):
  list_duplicates.append(row)

"""