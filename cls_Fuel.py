#HAPPI code Version_July 2021, author: Jinxi
##class Fuels
# import random
import numpy as np


class Fuel():
    
    def __init__(self,fuel_type,cost_fuel,emission_intensity):
        self.fuel_type = fuel_type
        self.fuel_cost = cost_fuel #euro/kWh el
        self.emission_intensity = emission_intensity*10**(-6) # tCO2/kWh electricity

#H2 = Fuel('H2',2,0)

    def func_fuel_price(self,total_years,mean,eps1, eps2,stochasticity):
        price_profile = np.empty(total_years)
        price_profile [0] = mean ##average_price
        if stochasticity == True:
            for yr in range(total_years-1):
                price_profile[yr+1] = max (0.001, price_profile[yr] + eps1 * (mean - price_profile[yr]) + eps2 * mean * np.random.uniform(-1,1 + np.finfo(float).eps))
        else:
            price_profile [:] = mean

        return price_profile


coal = Fuel('coal',2.0*10**(-2),1000)# gCO2/kWh electricity
#coalCCS = Fuel('coalCCS',2.0,500)# 
natural_gas= Fuel('natural_gas',4.6*10**(-2),432)
#natural_gasCCS = Fuel('natural_gasCCS',natural_gas.fuel_cost*0.467/0.4+0.457,51)
biogas = Fuel('biogas',8.0*10**(-2),0)
uranium = Fuel('uranium',1.0*10**(-2),0)
air = Fuel('air',0,0)
sun = Fuel('sun',0,0)