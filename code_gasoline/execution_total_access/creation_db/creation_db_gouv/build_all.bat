chcp 65001
set PYTHONIOENCODING=utf-8

::set var_python=\\ulysse\users\echamayou\Etienne\WinPython-64bit-2.7.6.4\python-2.7.6.amd64\python.exe
set var_python=C:\Users\etna\Desktop\Etienne_work\Programming\WinPython-64bit-2.7.6.4\python-2.7.6.amd64\python.exe

set var_scripts_dir=%~dp0
set list_build=build_master_info_raw.py build_master_price_raw.py
set list_fix=fix_master_price_diesel.py fix_master_price_gas.py
set list_get_dfs=get_df_insee_codes.py get_df_geocoding.py get_df_characteristics.py get_df_brand_activity.py get_df_station_info.py get_df_prices.py get_rid_of_duplicates.py

FOR %%G IN (%list_get_dfs%) DO %var_python% %var_scripts_dir%%%G >> %var_scripts_dir%log.txt
