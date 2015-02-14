set more off
drop _all

local path_data = "\\ulysse\users\echamayou\Bureau\Etienne_work\Data"
local folder_ta = "\data_gasoline\data_built\data_paper_total_access\data_csv"
local file_name = "\df_long_elfc.csv"

/*
import delimited "`path_data'`folder_ta'`file_name'", delim(",", asstring)
describe, numbers
drop _all
*/

import delimited "`path_data'`folder_ta'`file_name'", delim(",", asstring) ///
       stringcols(2 5 6 7)

gen date = date(time, "YMD")
encode group_type, generate(c_group_type)
encode group, generate(c_group)
encode reg, generate(c_reg)

xtset id_station date

set matsize 1500

/* too big: reduce period */
drop if date <= 18992
*drop if date >= 19875

*xtreg price treatment i.date, fe
*xtreg price treatment i.date, fe vce(robust)
xtreg price treatment i.date, fe vce(cluster id_station)

/*
gen type_treatment = treatment * c_group_type
xtreg price i.type_treatment i.date, fe vce(cluster id_station)
gen group_treatment = treatment * c_group
xtreg price i.group_treatment i.date, fe vce(cluster id_station)
*/

replace c_group_type = 0 if treatment == 0
xtreg price i.c_group_type i.date, fe vce(cluster id_station)

replace c_group = 0 if treatment == 0
xtreg price i.c_group i.date, fe vce(cluster id_station)
