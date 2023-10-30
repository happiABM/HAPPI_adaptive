#build a Class for the system
#record data on the system level

import numpy as np
from cls_Power_Plant import PowerPlant,CoalPlant,GCCPlant
# from func_demand_supply import func_demand_supply
from func_demand_supply_new import func_demand_supply
from cls_Fuel import natural_gas,biogas
from params import slice_hours,eps,p0
from collections import Counter

#from itertools import combinations

class El_System():
    def __init__(self
                ,capacity_mix=None
                ,electricity_price=None
                ,carbon_price_record=None
                ,demand_record = None
                ,CO2_emission = None
                ):
        self.capacity_mix = {pp: 0 for pp in PowerPlant.__subclasses__()} # capacity mix of the generation plants
        self.average_electricity_price = []
        self.slice_electricity_price = []
        self.demand_record = []
        self.CO2_emission = []
        self.produce_lst = []



    @classmethod
    def evaluate_tech_profitability(cls,tech,scenario):
        pass
    #return profitability_distribution

    @classmethod
    def clear_the_market(cls,supply_lst,cost_order,slice_hours,electricity_demand):
        return zip(*map(func_demand_supply
                        ,electricity_demand
                        ,supply_lst
                        ,[cost_order]*len(electricity_demand)
                        ,slice_hours
                        ,[eps]*len(electricity_demand)
                        ,[p0]*len(electricity_demand)
                        ))
        #return el_price,el_production,slice_revuene,prod_fossil1,prod_fossil2
    

    def record_el_price(self,el_price,el_production,slice_hours):
        el_price = np.array(el_price)
        self.average_electricity_price.append(sum(el_price*np.array(el_production)*np.array(slice_hours))/sum(np.array(el_production)*np.array(slice_hours))) #total_price/total_production
        self.slice_electricity_price.append(el_price)
        

    

    def record_CO2_emission(self,year,carbon_price):
        # print("natual gas cost",natural_gas.fuel_cost + carbon_price*natural_gas.emission_intensity)
        # print("bio gas cost",biogas.fuel_cost)

        if natural_gas.fuel_cost + carbon_price*natural_gas.emission_intensity >= biogas.fuel_cost:
            GCCPlant.fuel_type = biogas
        else:
            GCCPlant.fuel_type = natural_gas
        
        emission_from_coal = CoalPlant.production_quantity[year]  * CoalPlant.fuel_type.emission_intensity
        emission_from_gas = GCCPlant.production_quantity[year] * GCCPlant.fuel_type.emission_intensity
        
        #print('fossil1.fuel_type',fossil1.fuel_type.emission_intensity)
        
        self.CO2_emission.append(emission_from_coal + emission_from_gas) #tCO2



    def record_production (self, el_price,tech_order,produce_data,slice_hours):
        produce_data = zip(*produce_data)
        el_price = list(np.around(np.array(el_price),2))
        # el_price = list(np.array(el_price))
        for tech, produce in zip(tech_order,produce_data):
            tech_produce = np.array(produce) * np.array(slice_hours)
            tech.production_quantity.append(tech_produce.sum())
            #print(tech,tech.production_quantity)
            # price_produce = zip(el_price, tech_produce)
            c = Counter()
            for price, produce in zip(el_price, tech_produce):
                c[price] += produce
            tech.price_produce.append(Counter(c).most_common())##.most_common(): save the data as a tuple
            #print(tech.price_produce)
        
    def record_biogas_production(self,year):
        #print(GCCPlant.production_quantity[year])
        if GCCPlant.fuel_type == biogas:
            GCCPlant.biogas_production.append(GCCPlant.production_quantity[year])
            GCCPlant.natural_gas_production.append(0)
        else:
            GCCPlant.natural_gas_production.append(GCCPlant.production_quantity[year])
            GCCPlant.biogas_production.append(0)