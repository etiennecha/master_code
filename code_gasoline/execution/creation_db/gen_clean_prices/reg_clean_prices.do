set more off
clear

local pathdata = "\\ulysse\users\echamayou\Bureau\Etienne_work\Data"
local dircsv   = "\data_gasoline\data_built\data_paper\data_csv"
local pathfile = "\price_panel_data.csv"
insheet using "`pathdata'`dircsv'`pathfile'"

drop if highway == 1
keep price id date
tostring(date), replace
tostring(id), replace

drop if price == .
* quietly  gen test = regexs(0) if(regexm(date, "[0-9][0-9][0-9][0-9]"))
* drop if test == "2013"
tab(date), gen(date_)

set matsize 1000
areg price date_*, absorb(id)
predict e, resid
drop date_*
rename e price_cl

local pathfileout = "\price_cleaned_stata.csv"
outsheet id date price price_cl using ///
  "`pathdata'`dircsv'`pathfileout'", comma replace
