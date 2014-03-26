set more off

local pathdata = "\\ulysse\users\echamayou\Bureau\Etienne_work\Data"
local dircsv   = "\data_gasoline\data_built\data_paper\data_csv"
local pathfile = "\price_panel_data.csv"
insheet using "`pathdata'`dircsv'`pathfile'"

drop if highway == 1
keep price id date
tostring(date), replace
tostring(id), replace

#drop if price == .
quietly  gen test = regexs(0) if(regexm(date, "[0-9][0-9][0-9][0-9]"))
drop if test == "2013"
tab(date), gen(date_)

# areg price date_*, absorb(id)
