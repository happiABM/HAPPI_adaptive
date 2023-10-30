#HAPPI code Version_July 2021, author: Jinxi
#tax_profile: a growing or a constant scenario, with or without price volatility.

import random
import numpy as np
#from params import similation_period
def func_tax (similation_period,tax_scenario,initial_tax,eps1,eps2,stochasticity,start_year = 10,max_tax=100):
    tax = initial_tax #initial tax
    tax_profile =[]
    if (tax_scenario == "grow" and stochasticity == False):
        growth_rate = 2
        end_year = start_year + int(max_tax/growth_rate)
         
        for year in range(similation_period+40) :
            if year <= start_year or year > end_year:
                increaseRate = 0
            if start_year < year <= end_year:
                increaseRate = growth_rate #euro /tCO2 year
            tax += increaseRate
            tax_profile.append(tax)# Euro/tCO2 .
        # print(tax_profile)
        return tax_profile 
    
    elif tax_scenario == 'constant':
        tax_profile = [initial_tax]*(similation_period+40)
        return tax_profile

    elif tax_scenario =='no_tax':
        tax_profile = [0]* (similation_period+40)
        return tax_profile

    elif tax_scenario =='jump':
        year_interval = 10 #make a jump every 10 years
        jump_level = 20 #euro/ton CO2
        
        for year in range(0,similation_period+40,year_interval) :
            tax_profile+=([initial_tax] * year_interval) #euro 
            if initial_tax < 100:
                initial_tax += jump_level
            else:
                continue
        return tax_profile
    
    elif tax_scenario =='jump+grow':
        return tax_profile

    elif tax_scenario == 'constant + variation':
        for year in range(similation_period+40+1):
            tax_profile.append(random.randint(initial_tax/2, initial_tax*2))
        return tax_profile

    elif (tax_scenario == "grow" and stochasticity == True):
        tax_profile_mean = np.empty(similation_period)
        tax_profile = np.empty(similation_period)
        growth_rate = 2
        end_year = start_year + int(max_tax/growth_rate)
         
        for year in range(similation_period) :
            if year <= start_year or year > end_year:
                increaseRate = 0
            if start_year < year <= end_year:
                increaseRate = growth_rate #euro /tCO2 year
            tax += increaseRate
            tax_profile_mean[year] = tax# Euro/tCO2 .
        ## add stocasticity##
        tax_profile[0] = 0
        for yr in range(similation_period-1):
                tax_profile[yr+1] = max(0,tax_profile[yr] + eps1 * (tax_profile_mean[yr] - tax_profile[yr]) + eps2 * tax_profile_mean[yr] * np.random.uniform(-1, 1 + np.finfo(float).eps))
        
        return tax_profile


# scenario = 'grow'
# #scenario = 'grow'
# initial_tax = 0
# #real_tax_profile = list(map(func_tax,range (similation_period+40)))
#real_tax_profile = func_tax(similation_period=80,tax_scenario='jump',initial_tax=30)
