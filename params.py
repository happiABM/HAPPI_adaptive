#HAPPI
#other params

import pandas as pd
##========= electricity market===========##
eps = -0.05
p0 = 3.25 #cent/kWh.
p0 *= 10**(-2) #euro/kWh. 
##===========slice data=============##
filepath = 'C:/Users\jinxi\OneDrive - Chalmers/ABM model/paperIV_learning/model/code/HAPPI_learning/param'
data_slice = pd.read_excel(filepath + '/slice_param.xlsx',engine='openpyxl',sheet_name="slice_params",header=0,index_col=0)
sliced_el_demand = data_slice.loc['demand_level'].values * 10**3 # kW(h)
slice_hours = data_slice.loc['slice_hours'].values ##numpy.ndarray
wind_availability = data_slice.loc['wind_level'].values
solar_availability = data_slice.loc['solar_level'].values
nonVER_availability = data_slice.loc['nonVER_level'].values
# print(type(sliced_el_demand))

simulation_period = 150
extra_year = 40

##===========financial parameters=============##
fraction_f = 0.3 #0% financing fraction from own bank accout.
interests_rate = 0.04 # 4% bank interest rate for loans