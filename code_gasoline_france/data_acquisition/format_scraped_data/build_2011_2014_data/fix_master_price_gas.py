#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *

path_dir_built_paper = os.path.join(path_data,
                                    'data_gasoline',
                                    'data_built',
                                    'data_scraped_2011_2014')
path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')

master_price = dec_json(os.path.join(path_dir_built_json,
                                     'master_price_gas_raw.json'))

# master_price_bu_sp95 = copy.deepcopy(master_price['sp95_price'])
# master_price_bu_e10 = copy.deepcopy(master_price['e10_price'])
master_price['sp95_price'] = get_num_ls_ls(master_price['sp95_price'])
master_price['e10_price'] = get_num_ls_ls(master_price['e10_price'])

master_price['sp95_price'], dict_cors_sp95, dict_ers_sp95 =\
  fill_prices_using_dates(master_price['sp95_price'],
                          master_price['sp95_date'],
                          master_price['dates'])
master_price['e10_price'], dict_cors_e10, dict_ers_e10 =\
  fill_prices_using_dates(master_price['e10_price'],
                          master_price['e10_date'],
                          master_price['dates'])

master_price['sp95_price'], dict_cors_gaps_sp95 = fill_short_gaps(master_price['sp95_price'], 5)
ls_abnormal_prices_sp95 = get_abnormal_price_values(master_price['sp95_price'], 1.0, 2.0)

master_price['e10_price'], dict_cors_gaps_sp95 = fill_short_gaps(master_price['e10_price'], 5)
ls_abnormal_prices_e10 = get_abnormal_price_values(master_price['e10_price'], 1.0, 2.0)

# for ind_indiv, price, ls_day_inds in ls_abnormal_prices_sp95:  
  # print master_price['ids'][ind_indiv], price, [master_price['dates'][x] for x in ls_day_inds]

# for ind_indiv, price, ls_day_inds in ls_abnormal_prices_e10:  
  # print master_price['ids'][ind_indiv], price, [master_price['dates'][x] for x in ls_day_inds]

ls_corrections_sp95 = [(u'20250002', 1.65 , [u'20120725', u'20120731']),
                       (u'31190001', float('nan'), [u'20111122', u'20111127']),
                       (u'36200003', float('nan'), [u'20130122', u'20130207']),
                       (u'38450001', 1.58 , [u'20120618', u'20120628']),
                       (u'43800001', 1.59 , [u'20120608', u'20120611']),
                       (u'47000001', 1.58 , [u'20120103', u'20120105']),
                       (u'51340002', float('nan'), [u'20110904', u'20111127']),
                       (u'51340002', float('nan'), [u'20111109', u'20111114']),
                       (u'51340002', float('nan'), [u'20111127']),
                       (u'56380001', 1.65 , [u'20120325']),
                       (u'58160003', 1.61 , [u'20120426', '20120502']),
                       (u'61170001', 1.63 , [u'20120427']),
                       (u'63700001', 1.6  , [u'20120513', u'20120515']),
                       (u'65190001', 1.69 , [u'20120720', u'20120724']),
                       (u'69360008', float('nan'), [u'20110904', u'20111114']), # weird: drop station?
                       (u'71500001', 1.63 , [u'20120905', u'20120912']),
                       (u'71000002', float('nan'), [u'20110904', u'20111019']), # weird: drop station?
                       (u'71700003', float('nan'), [u'20110904', u'20111114']), # weird: drop station?
                       (u'79400004', float('nan'), [u'20120615', u'20120619']), # check: expens. period?
                       (u'83390005', 1.53 , [u'20130429', u'20130506']),
                       (u'84240001', 1.54 , [u'20110928', u'20110929']),
                       (u'85350001', 2.066, [u'20120331', u'20120420']),
                       (u'85350001', 2.055, [u'20120421', u'20120512']),
                       (u'85350001', 2.043, [u'20120727', u'20120803']),
                       (u'85350001', 2.093, [u'20120727', u'20120803']),
                       (u'85350001', 2.043, [u'20120804', u'20120809']),
                       (u'85350001', 2.043, [u'20120810', u'20120812']),
                       (u'85350001', 2.121, [u'20120823', u'20120830']),
                       (u'85350001', 2.085, [u'20120831', u'20120910']),
                       (u'85350001', 2.025, [u'20120911', u'20120930']),
                       (u'85350001', 2.04 , [u'20130216', u'20130324']),
                       (u'85350001', 2.023, [u'20130325', u'20130417']),
                       (u'85350001', 2.003, [u'20130507', u'20130526'])]

ls_corrections_e10 =  [(u'1390004' , 1.65 , [u'20130121', u'20130122']),
                       (u'6300005' , 1.54 , [u'20121003']),
                       (u'6260001' , 1.62 , [u'20130410']),
                       (u'7160002' , float('nan'), [u'20110904', u'20111130']),
                       (u'37800002', 1.53 , [u'20121030']),
                       (u'44600001', 0.999, [u'20110904', u'20111114']),
                       (u'44600001', 0.999, [u'20110927', u'20110929']),
                       (u'51100031', 1.54 , [u'20120811', u'20120811']),
                       (u'57210001', 1.66 , [u'20120524', u'20120605']),
                       (u'62220001', 1.56 , [u'20120703']),
                       (u'75015007', float('nan'), [u'20110904', u'20111129'])]

# TODO (?): change correction function
ls_corrections_sp95_e = expand_ls_price_corrections(ls_corrections_sp95, master_price['dates'])
ls_corrections_e10_e = expand_ls_price_corrections(ls_corrections_e10, master_price['dates'])

master_price['sp95_price'] =  correct_abnormal_price_values(ls_corrections_sp95_e,
                                                            master_price['ids'],
                                                            master_price['dates'],
                                                            master_price['sp95_price'])
                                                                
master_price['e10_price'] =   correct_abnormal_price_values(ls_corrections_e10_e,
                                                            master_price['ids'],
                                                            master_price['dates'],
                                                            master_price['e10_price'])
                                                                
dict_suspects_sp95, dict_suspects_single_sp95, master_price['sp95_price'] =\
  correct_abnormal_price_variations(master_price['sp95_price'], 0.1)

dict_suspects_e10, dict_suspects_single_e10, master_price['e10_price'] =\
  correct_abnormal_price_variations(master_price['e10_price'], 0.1)

ls_ls_price_durations_sp95 = get_price_durations(master_price['sp95_price'])
ls_duration_corrections_sp95, master_price['sp95_price'] =\
  correct_abnormal_price_durations(master_price['sp95_price'], ls_ls_price_durations_sp95, 30)

ls_ls_price_durations_e10 = get_price_durations(master_price['e10_price'])
ls_duration_corrections_sp95, master_price['e10_price'] =\
  correct_abnormal_price_durations(master_price['e10_price'], ls_ls_price_durations_sp95, 30)

# Stats des after modifications

ls_ls_price_durations_sp95 = get_price_durations(master_price['sp95_price'])
ls_ls_price_variations_sp95 = get_price_variations(ls_ls_price_durations_sp95)
ls_start_end_sp95, ls_nan_sp95, dict_dilettante_sp95 =\
                  get_overview_reporting_bis(master_price['sp95_price'],
                                             master_price['dates'],
                                             master_price['missing_dates'])

ls_ls_price_durations_e10 = get_price_durations(master_price['e10_price'])
ls_ls_price_variations_e10 = get_price_variations(ls_ls_price_durations_e10)
ls_start_end_e10, ls_nan_e10, dict_dilettante_e10 =\
                  get_overview_reporting_bis(master_price['e10_price'],
                                             master_price['dates'],
                                             master_price['missing_dates'])

master_price['e10_price'] = get_rid_missing_periods(master_price['e10_price'], 2700)
master_price['sp95_price'] = get_rid_missing_periods(master_price['sp95_price'], 5500)

# read http://www.leparisien.fr/economie/pourquoi-le-sans-plomb-98-coute-t-il-plus-cher-que-le-sp95-01-05-2012-1979493.php

enc_json(master_price, os.path.join(path_dir_built_json,
                                    'master_price_gas_fixed.json'))

print u'\nCreation of master_price_gas_fixed.json successful'
print type(master_price)
print u'Length:', len(master_price)
