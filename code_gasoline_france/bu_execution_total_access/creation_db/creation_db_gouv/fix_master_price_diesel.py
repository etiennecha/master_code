#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from params import *

path_dir_built_paper = os.path.join(path_data,
                                    'data_gasoline',
                                    'data_built',
                                    data_paper_folder)
path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')

master_price = dec_json(os.path.join(path_dir_built_json,
                                     'master_price_diesel_raw.json'))

master_price['diesel_price'] = get_num_ls_ls(master_price['diesel_price'])
master_price_bu = copy.deepcopy(master_price['diesel_price'])

ls_start_end_bu, ls_nan_bu, dict_dilettante_bu =\
  get_overview_reporting_bis(master_price['diesel_price'],
                             master_price['dates'], 
                             master_price['missing_dates'])

master_price['diesel_price'], dict_corrections, dict_errors =\
  fill_prices_using_dates(master_price['diesel_price'],
                          master_price['diesel_date'],
                          master_price['dates'])

master_price['diesel_price'], dict_corrections_gaps =\
  fill_short_gaps(master_price['diesel_price'], 5)
ls_abnormal_prices = get_abnormal_price_values(master_price['diesel_price'], 1.0, 2.0)
ls_abnormal_price_values = format_ls_abnormal_prices(ls_abnormal_prices,
                                                     master_price['ids'],
                                                     master_price['dates'])
# for indiv_ind, indiv_id, price, ls_day_inds, ls_day_dates in ls_abnormal_price_values:
  # print indiv_ind, ls_day_inds, (indiv_id, price, ls_day_dates)

# Over period '20110904/20120514, following corrections (seems valid => 20121204)
ls_corrections_diesel =  [(u'2400008' , 1.56 , [u'20120216', u'20120219']), # 0.156
                          (u'11000008', 1.46 , [u'20130219']),              #0.146
                          (u'19300004', 1.45 , [u'20110913', u'20110925']), #0.145
                          (u'22290002', 0.85 , [u'20111104', u'20111107']), #no chge..
                          (u'41100002', 1.41 , [u'20130417', u'20130419']), #0.141
                          (u'42800002', 1.5  , [u'20120319']),              #0.001
                          (u'45650001', 1.4  , [u'20121013', u'20121014']), #0.014
                          (u'47000001', 1.5  , [u'20111119', u'20111120']), #0.001
                          (u'49160003', 1.51 , [u'20121121', u'20121122']), #0.151
                          (u'57160005', 1.55 , [u'20120314']),              #0.155
                          (u'57210001', 1.48 , [u'20121023', u'20121028']), #0.148
                          (u'83510003', 1.492, [u'20120724', u'20120729']), #0.001 unsure
                          (u'86170003', 1.378, [u'20111016', u'20111017']), #0.013
                          (u'93440003', 1.49 , [u'20120914', u'20120916']), #0.149
                          (u'93561001', 1.45 , [u'20111129'])] #0.145

ls_corrections_diesel_e = expand_ls_price_corrections(ls_corrections_diesel,
                                                      master_price['dates'])

master_price['diesel_price'] = correct_abnormal_price_values(ls_corrections_diesel_e,
                                                             master_price['ids'],
                                                             master_price['dates'],
                                                             master_price['diesel_price'])
dict_opposit, dict_single, master_price['diesel_price'] =\
  correct_abnormal_price_variations(master_price['diesel_price'], 0.1)

ls_ls_price_durations = get_price_durations(master_price['diesel_price'])
ls_duration_corrections, master_price['diesel_price'] =\
  correct_abnormal_price_durations(master_price['diesel_price'], ls_ls_price_durations, 60)

# Stats des after modifications
ls_ls_price_durations = get_price_durations(master_price['diesel_price'])
ls_ls_price_variations = get_price_variations(ls_ls_price_durations)
ls_start_end, ls_nan, dict_dilettante =\
  get_overview_reporting_bis(master_price['diesel_price'],
                             master_price['dates'],
                             master_price['missing_dates'])

# Get rid of periods with too few observations
master_price['diesel_price'] = get_rid_missing_periods(master_price['diesel_price'], 8000)
 
enc_json(master_price, os.path.join(path_dir_built_json,
                                    'master_price_diesel_fixed.json'))

print u'\nCreation of master_price_diesel_fixed.json successful'
print type(master_price)
print u'Length:', len(master_price)

## Inspect abnormal prices (see if corrected due to abnormal variations)
#for x in ls_abnormal_price_values:
#  print 'Station id_gouv', x[1], x[0]
#  se_prices = pd.Series(master_price['diesel_price'][x[0]])
#  se_prices.plot()
#  plt.show()

## MOVE TO PRICE ANALYSIS
#dict_sales = get_sales(ls_ls_price_variations, 3)
#ls_sales = [(k, len(v)) for k, v in dict_sales.items()] 
#ls_sales = sorted(ls_sales, key=lambda x: x[1], reverse = True)
## Analysis of periods of sales: seems some are particularly concerned (uncertainty) 
