set more off
drop _all

local path_data = "\\ulysse\users\echamayou\Bureau\Etienne_work\Data"
local folder_ta = "\data_gasoline\data_built\data_paper_total_access\data_csv"
local file_name = "\df_long_elf.csv"

/*
import delimited "`path_data'`folder_ta'`file_name'", delim(",", asstring)
describe, numbers
drop _all
*/

import delimited "`path_data'`folder_ta'`file_name'", delim(",", asstring) ///
       stringcols(2)

gen date = date(time, "YMD")
encode reg, generate(c_reg)

xtset id_station date

set matsize 1500

/* too big: reduce period */
*drop if date <= 18992
*drop if date >= 19875

*xtreg price treatment i.date, fe
*xtreg price treatment i.date, fe vce(robust)

replace price = price * 100
xtreg price treatment i.date, fe vce(cluster id_station)
