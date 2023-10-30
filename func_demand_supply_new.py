#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
demand_supply module.
-calculate the electricity price at equilibrium (when demand=supply)
- price in each time slice.
"""
# from params import eps,p0
import numpy as np
# from func_restart import restart

def func_demand_supply(q0,supply_lst,running_costs,slice_hours,eps,p0):##q0 = demand
    
    # print('supply_lst: ',supply_lst)
    # print('running_costs: ',running_costs)
    # print('slice_hours: ',slice_hours)
    
    total_avail_capacity = sum(supply_lst)
    # ~ print('\n' + 'The total_avail_capacity is: ' + str(total_avail_capacity))
    eq_production = 0
    dispatch_lst = [0] * len(supply_lst) #record dipatch amount
# =============================================================================
    for pos, pp_capacity in enumerate(supply_lst, start=0):
        eq_production += pp_capacity
        if eq_production == 0: 
            continue
        
        demand_price = p0 * q0 ** (-1 / eps) * eq_production ** (1 / eps)
        
        if demand_price <= running_costs[pos]:
            eq_price = running_costs[pos]## means price will be the running cost of first type.
            eq_production = q0 * (eq_price / p0) ** eps
            dispatch_lst[pos] = eq_production - sum(supply_lst[0:pos])
            break
            
        else: ##if demand_price > run_costs[i]
            eq_price = demand_price
            dispatch_lst[pos] = supply_lst[pos]
            if (total_avail_capacity - eq_production > 0 and demand_price > running_costs[pos+1]):
                continue
                ## first if :## if there is still remaining/unruned production/plants.second if: check if on the vertical line
            else: ## if demand_price <= run_costs[i+1] or total_avail_capacity=max
                break 
    
    
    hour_revuene =(eq_price - np.asarray(running_costs)) * supply_lst
    hour_revuene = np.where(hour_revuene < 0, 0, hour_revuene)
    slice_revuene = hour_revuene * slice_hours

    return eq_price,eq_production,slice_revuene, dispatch_lst
    
    
    
    ##calculate production for coal and gas (to record CO2 emissions)
    # if pos > 3:
    #     production_from_coal_and_gas = [supply_lst[3], eq_production - sum(supply_lst[0:3+1])]
    # elif pos ==3:    
    #     production_from_coal_and_gas = [eq_production - sum(supply_lst[0:pos]), 0]

    # else: production_from_coal_and_gas =[0,0]    

    

