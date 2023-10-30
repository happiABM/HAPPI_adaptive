# import os
import sys
import itertools
import importlib
from time import sleep
from params import simulation_period
from func_main import func_main

adaptive_rules = ["annuitized_cost"]##"forecasted_revenue", "annuitized_cost"
forecast_method = "past_experience" #"past_experience" or "extrapolate"

adaptivityLst = [True]#True,False
stochasticityLst = [True]
heter_risk_level = True

all_cases = []
for a in adaptivityLst:
    if a == True and heter_risk_level == False:
        risk_levels = [0,1,3,5]
    else:
        risk_levels = [0]
    all_cases.extend(list(itertools.product(*[adaptive_rules,[a],risk_levels,stochasticityLst])))


for case_setting in all_cases:
    adaptive_rule,adaptivity,risk_level,stochasticity = case_setting
    # case_name = "adaptive_" + str(adaptivity) + "_risk_heter_yr150"
    #case_name = "adaptive_" + str(adaptivity) + "_risk_"+ str(risk_level) + "_yr150"
    
    # case_name = "adaptive_non_stochasticity"
    case_name = "coal_price_non_stochastic"

    # simulation_period = 100
    
    if __name__ == "__main__":
        if stochasticity == True:
            n = 500
        else:
            n = 10
        for i in range(n):
            print(case_setting)
            print("run",i)
            

            # try:
            func_main(case_name,adaptive_rule,adaptivity,risk_level,stochasticity,forecast_method,simulation_period)
            importlib.reload(sys.modules['cls_Consumer'])
            importlib.reload(sys.modules['cls_Power_Plant'])
            importlib.reload(sys.modules['cls_Power_Company'])
            importlib.reload(sys.modules['cls_system'])
            importlib.reload(sys.modules['cls_Fuel'])
                # sleep(1)
                
            # except:
                # print("error")
                # sleep(1)
                # importlib.reload(sys.modules['cls_Consumer'])
                # importlib.reload(sys.modules['cls_Power_Plant'])
                # importlib.reload(sys.modules['cls_Power_Company'])
                # importlib.reload(sys.modules['cls_system'])
                # importlib.reload(sys.modules['cls_Fuel'])
                # continue
            
            

 