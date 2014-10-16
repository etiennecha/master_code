"""
Pour Python 2.7
"""

import httplib
import urllib
import json

hostName = "rdf.insee.fr"
headers = {"Accept" : "application/json"}

# VARIABLE NAMES:
# http://rdf.insee.fr/def/geo
# http://rdf.insee.fr/def/demo

#queryString = """PREFIX idemo:<http://rdf.insee.fr/def/demo#>
#PREFIX igeo:<http://rdf.insee.fr/def/geo#>
# 
#SELECT ?departement ?nom ?population WHERE {
#    ?departement a igeo:Departement .
#    ?departement igeo:nom ?nom .
#    ?departement idemo:population ?popLeg .
#    ?popLeg idemo:populationTotale ?population .
#}
#ORDER BY ?population
#"""
#LIMIT 3

queryString = """PREFIX idemo:<http://rdf.insee.fr/def/demo#>
PREFIX igeo:<http://rdf.insee.fr/def/geo#>
 
SELECT ?commune ?nom ?arrondissement ?population WHERE {
    ?commune a igeo:Commune .
    ?commune igeo:nom ?nom .
    ?commune igeo:Arrondissement ?arrondissement .
    ?commune idemo:population ?popLeg .
    ?popLeg idemo:populationTotale ?population .
}
ORDER BY ?population
"""

params = {"query" : queryString}
encodedQuery = urllib.urlencode(params)

connection = httplib.HTTPConnection(hostName)
connection.request("GET","/sparql?" + encodedQuery, "", headers)

resp = connection.getresponse()

if resp.status == httplib.OK :
	jsonData = json.JSONDecoder().decode(resp.read())

	for binding in jsonData["results"]["bindings"] :
		dep = binding["nom"]["value"]
		pop = binding["population"]["value"]
		print("Nom : %s ; Population : %s" %(dep,pop))
else :
	print("Erreur : " + str(resp.status))
