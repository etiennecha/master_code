chcp 65001
set PYTHONIOENCODING=utf-8

set var1=\\ulysse\users\echamayou\Bureau\Etienne_work\Code\code_gasoline\execution_total_access\creation_db\creation_db_gouv\build_master_info_raw.py

set var2=\\ulysse\users\echamayou\Bureau\Etienne_work\Code\code_gasoline\execution_total_access\creation_db\creation_db_gouv\build_master_price_raw.py

FOR %%G IN (%var1%, %var2%) DO \\ulysse\users\echamayou\Etienne\WinPython-64bit-2.7.6.4\python-2.7.6.amd64\python.exe %%G >> \\ulysse\users\echamayou\Bureau\Etienne_work\Code\code_gasoline\execution_total_access\creation_db\creation_db_gouv\log.txt
