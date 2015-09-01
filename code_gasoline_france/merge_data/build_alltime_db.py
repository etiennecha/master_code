#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
import datetime

# DATA SOURCES
# ------------
# - my scraped data: include all stations (at the time) and brands
# - plp scraped data: include all stations (at the time) and brands but weekly
# - open data: prices backward (not if station discontinued) and no brands
# Also open data have not been really fixed (id reconciliations + errors in prices)

# OUTPUT DESIRED
# --------------
# Dynamic (index date, cols id_station): price dataframe, brand dataframe (not sure?)
# Static: station brand info with dates of changes
# Static: station location info (name, address, gps... c_insee...)
# Dyna low frequency (?): services, opening hours...

# METHOD
# ------
# - concat open data before + my scraped data when available (id reconciliations?)
# - add missing stations from plp (fill prices using dates?)
# - brand info from plp
