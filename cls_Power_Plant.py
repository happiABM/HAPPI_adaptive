#HAPPI code Version_July 2021, author: Jinxi
#class Power plant
#available_technology = {'coal_fired','coal_fired_CCS','NGCC','NGCC_CCS','nuclear','wind','solar'}
import random
from collections import defaultdict
from cls_Fuel import coal,natural_gas,biogas,uranium,air,sun
from params import wind_availability,solar_availability,\
    nonVER_availability,simulation_period,extra_year,interests_rate
# import numpy as np
#from tax_profile import tax_profile

#=================================================##
#=================================================##
#super class
class PowerPlant():
    subsidy = 0

    instances = [] #track all "alive" plants.
    def append_instance(self):
        PowerPlant.instances.append(self)

    @property
    def value(self):
        return self.overnight_cost * (1-(1+interests_rate)**(-self.lifespan))/(1-(1+interests_rate)**(-self.lifetime))
    
    @classmethod
    # @property
    def annuitized_cost (cls,agent,year):
        return cls.overnight_cost * cls.CRF(interests_rate)
        #return cls.overnight_cost * cls.CRF(interests_rate) * 0.7 + cls.overnight_cost * cls.CRF(agent.hr_lst[cls][year]) * 0.3
    


    @classmethod
    @property
    def installed_capacity(cls):
        #installed_capacity = cls.quantity * cls.size
        return cls.quantity * cls.size

    
    def record_data(techLst):
        for tech in techLst:
            tech.capacity_record.append(tech.installed_capacity)
            #tech.cost_record.append(tech.overnight_cost)
            #tech.estimated_NPV_records.append(dict(tech.estimated_NPV))
            #tech.estimated_NPV = defaultdict(list)#reset the dict to empty
            #tech.hr_record.append(company.hr_tech[tech])

    @classmethod
    def record_annual_investment(cls,year):#record how many new plants are invested per year
        cls.annual_investment[year] += 1

    @classmethod
    def available_capacity(cls):
        #installed_capacity = installed_capacity(cls)
        if cls == WindPlant:
            available_capacity = WindPlant.installed_capacity* wind_availability
        elif cls == SolarPlant:
            available_capacity = SolarPlant.installed_capacity * solar_availability
        else:
            available_capacity = cls.installed_capacity * nonVER_availability
        return available_capacity

    @classmethod
    def lifespan_minus_1(cls):
        decommission_lst =[]
        for pp in list(cls.instances):
            # print('check here')
            pp.lifespan -=1 #a plant's lifespan minus by 1
            if pp.lifespan == 0:
                decommission_lst.append(pp)
        return decommission_lst

    def decommission_one_plant(decommission_lst):
        # remove a plant (at a random position in the list), and retuen "the plant".
        the_plant = decommission_lst.pop(random.randrange(len(decommission_lst)))
        plant_type = type(the_plant) #get the Class type.
        plant_type.quantity -= 1 #numbers of this type of plant minus 1.
        the_plant.owner.portfolio[plant_type] -= 1 # also delete from its owner's protfolio.
        the_plant.owner = 'avfall' # 'send' the plant to 'garbage'.
        #delete the object, even though Python cannot delet an object.
        list(PowerPlant.instances).remove(the_plant)#remove it from the whole pp_lst.
        del the_plant #delete the instance, but seems python cannot delete instance

    @classmethod
    def CRF (cls,r):
        #"r" is the discount_rate
        return r/(1 - (1 + r)**(-1 * cls.lifetime))

    @classmethod
    def get_revenue_per_plant(cls,annual_tech_revuene,tech_order,Real_lifeMode):
        for tech in tech_order:
            if tech.quantity == 0:
                tech.revuene_per_plant = 0
            else:
                tech.revuene_per_plant = annual_tech_revuene[tech_order.index(tech)] / tech.quantity
            if Real_lifeMode == True:#'real-life production',not in evaluation mode
                tech.annual_revenue_records.append (tech.revuene_per_plant)
      

    # @classmethod
    # def annuitized_cost(cls,financed_by_debt,i):
    #     #f: fraction borrowed from the bank.
    #     #: interest rate of the borrowed money.
    #     return financed_by_debt * cls.CRF(i) #annuitized cost,euro.


    # maximal_reduction = 0.5 #maximal redction of the original cost
    @classmethod
    def technology_learning(cls,year):
        #for cls in tech_lst:
        for tech in PowerPlant.__subclasses__():
            tech.total_experience_lst.append(tech.total_experience)##record the culmulative capacity.

            if (tech == NuclearPlant or tech == CoalPlant) : maximal_reduction = 0.2
            else: maximal_reduction = 0.5
            if (year > 0 and tech.total_experience_lst[year-1]>0):
                if tech.overnight_cost <= tech.investment_cost_per_kw * tech.size * maximal_reduction:
                    continue
                else:
                    tech.overnight_cost *= (tech.total_experience/tech.total_experience_lst[year-1])**tech.learning_rate
    # @classmethod
    # def calculate_performance(cls,agent,year,recall_length):
    #     safety_indicator = 0
    #     if year not in cls.performance_indicator:
    #     #print("\n",tech.__name__[0:-5])  
    #         pastRevenueRecords = cls.annual_revenue_records [year-recall_length : year]
    #         performance = [0] * recall_length
        
    #         for yr in range(recall_length):
    #             if pastRevenueRecords[yr] == 0: ##no investment at that year
    #                 continue
    #             else:   
    #                 performance[yr] = pastRevenueRecords[yr] - cls.annuitized_cost(agent=agent,year=year-recall_length+yr)

    #             if performance[yr] > 0:
    #                 safety_indicator += 1
            
    #         average_performance = sum(performance)
            
    #         cls.performance_indicator[year] = {"safety_indicator": safety_indicator,"average_performance":average_performance}
    #         cls.performance_indicator_lst[year] = average_performance
    #         #print("safety_indicator: ",safety_indicator)
    #         #print("loss_frequency : ",loss_frequency)
    #         #print("average_performance : ", average_performance/10**6)
    #         # print("old hr ",self.hr_tech[tech])
    #         # if (safety_indicator >= self.risk_averse_level and tech.performance_indicator [-1] > 0):
    #     else:
    #         safety_indicator =  cls.performance_indicator[year]["safety_indicator"]
    #         average_performance = cls.performance_indicator[year]["average_performance"]
        
    #     return safety_indicator,average_performance






#1. coal-fired plants (without CCS).
class CoalPlant (PowerPlant):
    name = "Coal"
    ##define varaibles
    color = 'sienna'
    # size = 500 #Mw
    size = 850 * 10**3 #unit:kw. 850Mw
    quantity = 0 #number of plants.
    initial_quantity = 74
    total_experience = 0
    #total_experience_lst = [] #to record culmulative capacity at each year.
    #learning_rate = -0.322
    fuel_type = coal #
    running_cost = coal.fuel_cost #+ 0 * coal.emission_intensity #0 =carbon price
    investment_cost_per_kw = 1500 # euro/kW
    lifetime = 40 #years
    efficiency = 1 #100%
    availability = nonVER_availability
    #financial variables:
    overnight_cost = investment_cost_per_kw * size
    capacity_record = []
    cost_record = []
    annual_revenue_records = []
    annual_investment = [0]*(simulation_period+extra_year)
    ##new investment assessment
    positive_cases = 0
    average_pofitability = 0
    #average_pofitability_lst = defaultdict(list)
    estimated_NPV = defaultdict(list)
    estimated_NPV_records = []
    dev_pofitability = 0
    revuene_per_plant = 0
    portfolio_pofitability = 0
    criteria = 0
    production_quantity = []
    price_produce = []
    performance_indicator = {}
    performance_indicator_lst = [None] *simulation_period 



    def __init__(self,owner,lifespan=None):
        self.owner = owner
        self.lifespan = lifespan if lifespan is not None else round(random.gauss(mu=CoalPlant.lifetime,sigma=CoalPlant.lifetime/10))
        CoalPlant.quantity +=1
        CoalPlant.total_experience += 1
        PowerPlant.append_instance(self) #record all plants



#3. gas-fired plants (without CCS).
class GCCPlant(PowerPlant):
    name = "GCC"
    color = 'lightcoral'
    #size = 100 #MW
    size = 500 * 10**3 #kW
    quantity = 0 # the initial number of plants
    initial_quantity = 6
    total_experience = 0
    #total_experience_lst = [] #to record culmulative capacity at each year.
    # initial_experience = 2*10**3 #MW
    # previous_experience = initial_experience
    # total_experience = previous_experience
    #learning_rate = -0.322
    fuel_type = natural_gas or biogas# or biogas, need to add
    running_cost = fuel_type.fuel_cost #+ 0 * fuel_type.emission_intensity # 0 =carbon price
    investment_cost_per_kw = 900 # euro/kW
    lifetime = 30 #years
    efficiency = 1 #100%
    overnight_cost = investment_cost_per_kw * size
    capacity_record = []
    cost_record = []
    annual_revenue_records = []
    annual_investment = [0]*(simulation_period+extra_year)
    availability = nonVER_availability
    positive_cases = 0
    average_pofitability = 0
    #average_pofitability_lst = defaultdict(list)
    estimated_NPV = defaultdict(list)
    estimated_NPV_records = []
    dev_pofitability = 0
    revuene_per_plant = 0
    portfolio_pofitability = 0
    criteria = 0
    
    production_quantity = []
    biogas_production = [] ##annual production by biogas
    natural_gas_production = [] ##annual production by biogas
    price_produce = []
    performance_indicator = {}
    performance_indicator_lst = [None] *simulation_period 
    


    def __init__(self,owner,lifespan=None):
        self.owner = owner
        self.lifespan = lifespan if lifespan is not None else round(random.gauss(mu=GCCPlant.lifetime,sigma=GCCPlant.lifetime/10))
        GCCPlant.quantity+=1
        GCCPlant.total_experience += 1
        PowerPlant.append_instance(self)

#4. gas-fired plants with CCS.
# class NGCC_ccsPlant(PowerPlant):
#     size = 500* 10**3 #MW
#     quantity = 0 # the initial number of plants
#     initial_experience = 2*10**3
#     previous_experience = initial_experience
#     total_experience = previous_experience
#     learning_rate_en = -0.322
#     learning_rate_ex = 0.0
#     fuel_type = natural_gasCCS
#     lifetime = 30 #years
#     investment_cost_per_kw = 1400 # euro/kW
#     efficiency = 0.85 #85%
#     overnight_cost = investment_cost_per_kw * size * 1000 #size: Mw to Kw
#     capacity_record = []
#     cost_record = []
#     annual_revenue_records = []
#     annual_investment = [0]*(simulation_period+extra_year)
#     availability = nonVER_availability

#     def __init__(self,owner,lifespan=lifetime,value=overnight_cost):
#         self.owner = owner
#         self.lifespan = lifespan
#         NGCC_ccsPlant.total_experience += NGCC_ccsPlant.size
#         NGCC_ccsPlant.quantity+=1
#         PowerPlant.append_instance(self)

#5.nuclear plants.
class NuclearPlant(PowerPlant):
    name = "Nuclear"
    color = 'darkgrey' #for plotting purpose
    #size = 1000 #MW
    size = 1500* 10**3 #kW
    quantity = 0
    initial_quantity = 0
    total_experience = 0
    #total_experience_lst = [] #to record culmulative capacity at each year.
    #learning_rate = -0.322
    fuel_type = uranium
    running_cost = uranium.fuel_cost
    investment_cost_per_kw = 6000 #* 2# euro/kW
    lifetime = 40 #years
    efficiency = 1 #100%
    overnight_cost = investment_cost_per_kw * size
    capacity_record = []
    cost_record = []
    annual_revenue_records = []
    annual_investment = [0]*(simulation_period+extra_year)
    availability = nonVER_availability
    positive_cases = 0
    average_pofitability = 0
    #average_pofitability_lst = defaultdict(list)
    estimated_NPV = defaultdict(list)
    estimated_NPV_records = []
    dev_pofitability = 0
    revuene_per_plant = 0
    portfolio_pofitability = 0
    criteria = 0
    production_quantity = []
    price_produce = []
    performance_indicator = {}
    performance_indicator_lst = [None] *simulation_period 


    def __init__(self,owner,lifespan=None,):
        self.owner = owner
        self.lifespan = lifespan if lifespan is not None else round(random.gauss(mu=NuclearPlant.lifetime,sigma=NuclearPlant.lifetime/10))
        NuclearPlant.quantity+=1
        NuclearPlant.total_experience += 1
        PowerPlant.append_instance(self)

class WindPlant(PowerPlant):
    name = "Wind"
    color = 'deepskyblue' #for plotting purpose
    #size = 500 #MW
    size = 100* 10**3 #MW
    quantity = 0
    initial_quantity = 0
    total_experience = 0
    #total_experience_lst = [] #to record culmulative capacity at each year.
    # initial_experience = 54938#MW, Germany 2020
    # previous_experience = initial_experience
    # total_experience = previous_experience
    #learning_rate = -0.322
    technology = 'wind'
    fuel_type = air
    running_cost = 0
    investment_cost_per_kw = 1500 # euro/kW
    lifetime = 25 #years
    efficiency = 1 #100%
    overnight_cost = investment_cost_per_kw * size
    capacity_record = []
    cost_record = []
    annual_revenue_records = []
    annual_investment = [0]*(simulation_period+extra_year)
    availability = wind_availability
    positive_cases = 0
    average_pofitability = 0
    #average_pofitability_lst = defaultdict(list)
    estimated_NPV = defaultdict(list)
    estimated_NPV_records = []
    dev_pofitability = 0
    revuene_per_plant = 0
    portfolio_pofitability = 0
    criteria = 0
    production_quantity = []
    price_produce = []
    performance_indicator = {}
    performance_indicator_lst = [None] *simulation_period 


    def __init__(self,owner,lifespan=None):
        self.owner = owner
        self.lifespan = lifespan if lifespan is not None else round(random.gauss(mu=WindPlant.lifetime,sigma=WindPlant.lifetime/10))
        WindPlant.quantity+=1
        WindPlant.total_experience += 1
        PowerPlant.append_instance(self)

class SolarPlant(PowerPlant):
    name = "Solar"
    color = 'gold'
    #size = 500 #MW
    size = 100 * 10**3 #MW
    quantity = 0
    initial_quantity = 0
    total_experience = 0
    #total_experience_lst = [] #to record culmulative capacity at each year.
    # initial_experience = 49096#MW, Germany 2019.
    # previous_experience = initial_experience
    # total_experience = previous_experience
    #learning_rate = -0.322
    technology = 'solar'
    fuel_type = sun
    running_cost = 0
    #investment_cost_per_kw = 800 # euro/kW
    investment_cost_per_kw = 700 # euro/kW
    lifetime = 25 #years
    efficiency = 1 #100%
    overnight_cost = investment_cost_per_kw * size
    capacity_record = []
    cost_record = []
    annual_revenue_records = []
    annual_investment = [0]*(simulation_period+extra_year)
    availability = solar_availability
    positive_cases = 0
    average_pofitability = 0
    #average_pofitability_lst = defaultdict(list)
    estimated_NPV = defaultdict(list)
    estimated_NPV_records = []
    dev_pofitability = 0
    revuene_per_plant = 0
    portfolio_pofitability = 0
    criteria = 0
    production_quantity = []
    price_produce = []
    performance_indicator = {}
    performance_indicator_lst = [None] *simulation_period 



    def __init__(self,owner,lifespan=None):
        self.owner = owner
        self.lifespan = lifespan if lifespan is not None else round(random.gauss(mu=SolarPlant.lifetime,sigma=SolarPlant.lifetime/10))
        SolarPlant.quantity+=1
        SolarPlant.total_experience += 1
        PowerPlant.append_instance(self)

#2. coal-fired plants with CCS.
# class Coal_ccsPlant (CoalPlant):

# print(CoalPlant.running_cost(tax=2))

# c1=CoalPlant(owner='test')
# print(CoalPlant.quantity)
# print(list(c1.instances))