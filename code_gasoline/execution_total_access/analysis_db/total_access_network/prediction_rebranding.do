drop _all

local path_data = "\\ulysse\users\echamayou\Bureau\Etienne_work\Data"
local folder_ta = "\data_gasoline\data_built\data_paper_total_access\data_csv"
local file_name = "\df_rebranding_logit.csv"

import delimited "`path_data'`folder_ta'`file_name'", delim(",", asstring)
describe, numbers
drop _all

import delimited "`path_data'`folder_ta'`file_name'", delim(",", asstring) ///
       stringcols(1)

encode statut_2010, generate(mun_status)
logit rebranded i.mun_status cb dist_cl dist_cl_sup nb_comp_3km crowded

/* Odd ratio */
logit rebranded i.mun_status i.cb i.crowded dist_cl dist_cl_sup nb_comp_3km, or

margins mun_status, atmeans

predict p
summarize rebranded p

estat classification
