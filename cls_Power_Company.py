#HAPPI, author Jinxi, July 2021.
#CLASS Power_Company


#from typing import no_type_check
import numpy as np
# import itertools
import numpy_financial as npf
# from statistics import pstdev,pvaria

from cls_Power_Plant import PowerPlant,CoalPlant,GCCPlant,\
    NuclearPlant,WindPlant,SolarPlant#,tech_lst#NGCC_ccsPlant,
from cls_Fuel import coal,natural_gas,biogas,uranium
from func_revenue import func_revenue
from params import slice_hours,simulation_period,extra_year,fraction_f,interests_rate
# from cls_Consumer import Consumer
# electricity_demand = Consumer().express_demand('electricity', scenario = "constant")

class Power_Company():
    lst = [] #store all instances.
    #bankruptLst = {}
    assessment_recods = []
    investment_assessment_lst = [] ##for plotting
    
    ##====== financial variables======##:
    initial_cash = 1000*10**6#several  million Euro
    # initial_cash = 0#several  million Euro
    minimal_hr = interests_rate
    cap_hr = 1
    # saveBuffer = 150*10**4 #money saved in the bank account before paying dividend.
    # dividend_fraction = 0.0 #50% of the "free" cash are paid out as dividend.
    a1 = np.linspace(start = 0.041, stop = 0.045, num=5, endpoint=True)
    a2 = np.linspace(start = 0.05, stop = 0.065, num=4, endpoint=True)
    a3 = np.linspace(start = 0.07, stop = cap_hr, num= int((cap_hr - 0.07) / 0.01 + 1), endpoint=True)
    hr_lst_nonLinear = np.concatenate([a1,a2,a3]).round(decimals=3)

    hr_lst_linear = np.linspace(start = minimal_hr, stop = cap_hr, num= int((cap_hr - minimal_hr)/0.01*2 + 1), endpoint=True).round(decimals=3)
        
    
    ##====== forecast variables======##:
    # carbon_price_range = [1.0, 1.5]
    # carbon_price_range = [1]
    # fuel_price_range = [0.5, 1.0, 1.5]
    # fuel_price_range = [1.0]
    #capital_cost_range = [0.75, 1.0, 1.25]
    # foresight = 10 #(default) foresight for carbon tax.

    
    def __init__(self
                ,name
                ,adaptivity
                ,adaptive_rule
                ,hr_initial = 0.06
                ,risk_averse_level = 0
                ,cash = initial_cash
                ,debt = 0
                ,status ='active'
                ,tech_preference = PowerPlant.__subclasses__()##default:all the technolgies.
                
                ):
        ##define varaibles
        self.name = name
        self.tech_preference = tech_preference
        self.portfolio = {pp: 0 for pp in PowerPlant.__subclasses__()} # initial plant portfolio
        #self.portfolio_lst = {pp : [0] for pp in PowerPlant.__subclasses__()}
        self.portfolio_lst = {pp : [0] * simulation_period for pp in PowerPlant.__subclasses__()}

        self.value_of_plant = {pp: 0 for pp in PowerPlant.__subclasses__()} #value of my plants
        self.plant_value_lst = {pp : [0] * simulation_period for pp in PowerPlant.__subclasses__()}#record for plotting.

        #hurdle rate:
        self.hr_initial = hr_initial
        self.hr_tech = {pp : self.hr_initial for pp in PowerPlant.__subclasses__()}
        self.hr_lst = {pp : [self.hr_initial] * simulation_period for pp in PowerPlant.__subclasses__()}
        self.risk_averse_level = risk_averse_level
        ##adaptive or not
        self.adaptivity = adaptivity
        self.adaptive_rule = adaptive_rule

        #financial variables:
        self.cash = cash
        self.debt = debt
        self.status = status
        self.principle_payment = np.array([0] * (simulation_period + extra_year+1), dtype=float)
        self.net_income_lst = [] #record annaul net income for (expost) ROE calculation
        self.equity_lst = [] #record annaul net income for (expost) ROE calculation
        self.debt_lst = [] #record annaul current amount of debt
        self.cash_lst = [] #record annaul current amount of cash in the bank account
        self.risk_level_lst = []
        self.revenue = {pp : [] for pp in PowerPlant.__subclasses__()}
        ##new investment assessment
        self.NPV_single_assessment = {pp : [] for pp in PowerPlant.__subclasses__()}
        ##record annaul investment
        self.annual_investment = {pp : [0] * simulation_period for pp in PowerPlant.__subclasses__()}
        ##record annaul revenue forecast
        self.forecasted_revenue = {pp : [[] for _ in range(simulation_period+1)] for pp in PowerPlant.__subclasses__()}
        self.forecasted_el_price = {yr:[] for yr in range(simulation_period + 1)}

        ##record cash flow of each technology. cash_flow = annual_revenue - annuitized_cost
        self.cash_flow = {pp : [0] * simulation_period for pp in PowerPlant.__subclasses__()}


        Power_Company.lst.append(self)#append all company instances
        


    @property
    def equity(self):
        #print('the value of my plants', self.my_plant_value()/10**7)
        return self.cash + self.my_plant_value() - self.debt

    @property
    def debt_to_equity_ratio(self):
        return self.debt/self.equity

####===================produce_electricity===========####
    @classmethod
    def bid_el_price (cls
                    ,carbon_price
                    ,coal_Fuelcost = coal.fuel_cost
                    ,natural_gas_Fuelcost = natural_gas.fuel_cost
                    ,biogas_Fuelcost = biogas.fuel_cost
                    ,uranium_Fuelcost = uranium.fuel_cost
                    ):#bid at the marginal costs/running cost of the technology

        CoalPlant.running_cost = coal_Fuelcost + carbon_price * coal.emission_intensity
        GCCPlant.running_cost = min (natural_gas_Fuelcost + carbon_price * natural_gas.emission_intensity, biogas_Fuelcost)
        NuclearPlant.running_cost = uranium_Fuelcost

        tech_order = sorted(PowerPlant.__subclasses__(), key=lambda x: x.running_cost)
        
        cost_order = [tech.running_cost for tech in tech_order]
        #print(tech_order,cost_order)

        return tech_order,cost_order


##==============update financial status==================##
    @classmethod
    def offer_capacity(cls,tech_order):
        supply_tech = [tech.available_capacity() for tech in tech_order]
        return supply_tech


    def calculate_revenue(self):
        portfolio_revenue = 0
        for tech, nr in self.portfolio.items():
            revenue_tech = nr * tech.revuene_per_plant
            self.revenue[tech].append(revenue_tech)
            portfolio_revenue += revenue_tech
            
            #print('portfolio_revenue',self.portfolio[tech])
        return portfolio_revenue

        # pp_quantity_own = [self.portfolio[pp] for pp in tech_order]
        # revenue = sum(x*y for x,y in zip(pp_quantity_own,revuene_per_plant))


    def calculate_cash_flow(self,year,tech_lst):
        for tech in tech_lst:
            if tech.quantity > 0:
                self.cash_flow[tech][year] = tech.revuene_per_plant - tech.annuitized_cost(self,year)
            else:
                continue

            #return


    def adapt_hurdle_rate(self, year,recall_length):#,uniformStep,risk_measurement,information="public"
        hr_lst = self.hr_lst_linear
            
        for tech in self.tech_preference:
            if tech.quantity > 0:
                cash_flows = self.cash_flow[tech][year-recall_length:year] #list of cash flows during the past 5 years.
                
                average_performance = sum(cash_flows)

                safety_indicator = len([num for num in cash_flows if num > 0])

                if (safety_indicator >= self.risk_averse_level and average_performance >= 0):
                    # print("decrease")
                    #print("self.hr_tech",self.hr_tech[tech])
                    new_index = int(max(np.where(hr_lst == self.hr_tech[tech])[0][0] - 1, 0))
                    self.hr_tech[tech] = min(self.cap_hr, hr_lst[(new_index)])
                # elif (safety_indicator < self.risk_averse_level and tech.performance_indicator [-1] < 0):
                elif (safety_indicator <= self.risk_averse_level and average_performance < 0):
                    # print("increase")
                    new_index = int(min (np.where(hr_lst == self.hr_tech[tech])[0][0] + 1, int(hr_lst.size-1)))
                    self.hr_tech[tech] = min(self.cap_hr, hr_lst[(new_index)])
            else: #tech.quantity = 0
                continue

    # def adapt_hurdle_rate(self, year,recall_length,uniformStep,risk_measurement,information="public"):
    #     if uniformStep == False:
    #         hr_lst = self.hr_lst_nonLinear
    #     elif uniformStep == True:
    #         hr_lst = self.hr_lst_linear
        
    #     for tech in self.tech_preference:
    #         if tech.quantity > 0:
    #             safety_indicator,average_performance = tech.calculate_performance(self,year,recall_length)

    #             if (safety_indicator >= self.risk_averse_level and average_performance >= 0):
    #                 # print("decrease")
    #                 #print("self.hr_tech",self.hr_tech[tech])
    #                 new_index = int(max(np.where(hr_lst == self.hr_tech[tech])[0][0] - 1, 0))
    #                 self.hr_tech[tech] = min(self.cap_hr, hr_lst[(new_index)])
    #             # elif (safety_indicator < self.risk_averse_level and tech.performance_indicator [-1] < 0):
    #             elif (safety_indicator <= self.risk_averse_level and average_performance < 0):
    #                 # print("increase")
    #                 new_index = int(min (np.where(hr_lst == self.hr_tech[tech])[0][0] + 1, int(hr_lst.size-1)))
    #                 self.hr_tech[tech] = min(self.cap_hr, hr_lst[(new_index)])
    #         else: #tech.quantity = 0
    #             continue
                # print("new hr ",self.hr_tech[tech])
        #return


    # elif risk_measurement == "forecasted_revenue":
    #                         real_revenue = tech.annual_revenue_records[year - recall_length:year][i]
    #                         forcested_revenue = self.forecasted_revenue[tech][year-recall_length : year][i]
    #                         difference = real_revenue - forcested_revenue
    #                         if abs(difference) / real_revenue > 0.05: #the difference is less than 5%.
    #                             tech.performance_indicator[i] = difference

    def check_affordability(self,invesment_cadidate,year):
        remaining = (self.cash 
                    - invesment_cadidate.overnight_cost * fraction_f
                    - self.debt * interests_rate
                    - self.principle_payment[year+1]
                    )

        if remaining > 0:
            return invesment_cadidate
        else:
            return None
    
    


    def update_cash(self,amount):
        self.cash += amount
        
    def update_debt(self,amount):
        self.debt += amount
    
    def pay_back_debt(self,year):
        interest_cost = self.debt * interests_rate
        #if self.name == 'hr0.045hf0': print('interest cost = ', round(interest_cost/10**7,2))

        if self.cash < interest_cost:
            self.status == 'inactive' #no further investment allowed
            self.cash = 0
            self.principle_payment[year+1] += self.principle_payment[year]
             #pay interest costs.
        else:
            self.cash -= interest_cost ##pay back interest costs
            #print('interest cost paid:',round(interest_cost/10**6,2))
            if self.cash - self.principle_payment[year] < 0:
                self.status == 'inactive'
                self.debt -= self.cash
                self.principle_payment[year+1] += (self.principle_payment[year]- self.cash)
                self.cash = 0
            
            else:
                #self.status == 'active'
                self.cash -= self.principle_payment[year]
                self.debt -= self.principle_payment[year]
                #print('principle cost paid:',round(self.principle_payment[year]/10**6,2))

            #return interest_cost + self.principle_payment[year]
        
            #if self.name == 'hr0.045hf0': 
                #print('principle next year before hand', round(self.principle_payment[year+1]/10**6,2))
            #if self.name == 'hr0.045hf0':
                #print('principle unpaid', round((self.principle_payment[year]- self.cash)/10**7,2))
                #print('principle next year after unpaid', round(self.principle_payment[year+1]/10**7,2))
       


    def record_financial_variable(self,revenue,year):
        self.net_income_lst.append(revenue - self.debt * interests_rate - self.principle_payment[year])
        self.equity_lst.append(self.equity)
        self.debt_lst.append(self.debt)
        self.cash_lst.append(self.cash)

        # print('equity',round(self.equity/10**6,2))
        # print('debt',round(self.debt/10**6,2))
        # print('cash',round(self.cash/10**6,2))
    def record_individual_data(self,tech_lst,year):
        for tech in tech_lst:
            self.portfolio_lst[tech][year] = self.portfolio[tech]
            self.hr_lst[tech][year] = self.hr_tech[tech]
            self.plant_value_lst[tech][year] = self.value_of_plant[tech]


    def update_repayment_schedule_and_financial_status(self,year,new_plant):
        financed_by_own_capital = new_plant.overnight_cost * fraction_f
        financed_by_debt = new_plant.overnight_cost  *  (1-fraction_f)
        self.update_cash(-1 * financed_by_own_capital)#pay downpayment immediately,therefore mutiply*-1.
        self.update_debt(financed_by_debt) #update debt.
        
        # print('')
        # print('financed_by_debt: ',round(financed_by_debt/10**6,2))                            
        # print('financed_by_own_capital: ',round(financed_by_own_capital/10**6,2))                            
        # print('total debt: ',round(self.debt/10**6,2))                            
        # print('cash: ',round(self.cash/10**6,2))                            
        ##update the principle_payment payment
        outstanding_loan = financed_by_debt #outstanding_loan of this plant.
        amortization = financed_by_debt * new_plant.CRF(interests_rate)
        # print('amortization',round(amortization/10**6,2))
        counting = 0
        
        for yr in range (year+1,year+new_plant.lifetime+1):
            principle_amount = amortization - outstanding_loan * interests_rate
            self.principle_payment[yr] += principle_amount #annuitized cost meanus interest payment
            outstanding_loan -= principle_amount
        
        #     print('interests payment: ', outstanding_loan * interests_rate/10**6)    
        # print("interests_rate ",interests_rate)
        # print('principle_payment: ', self.principle_payment/10**6)    
       
                

    def my_plant_value(self):
        plant_value = 0
        self.value_of_plant = {pp: 0 for pp in PowerPlant.__subclasses__()} 
        for pp in list(PowerPlant.instances):
            if pp.owner == self:
                # print("the class of the plant is ",pp.__class__)
                plant_value += pp.value
                self.value_of_plant[pp.__class__] += pp.value
        return plant_value

    
    # def pay_dividend(self):
    #     if self.cash - self.saveBuffer > 0 :
    #         self.cash -= self.dividend_fraction *  (self.cash - self.saveBuffer)

    def calculate_forecasted_performance(self,year):
        for tech in self.tech_preference:
            #print("revenues",self.forecasted_revenue[tech][year])
            #print("len",len(self.forecasted_revenue[tech][year]))
            if len(self.forecasted_revenue[tech][year]) != 0:
                ##take the average because a technology is evaluated mutiple times a year.
                self.forecasted_revenue[tech][year] = sum(self.forecasted_revenue[tech][year]) / len(self.forecasted_revenue[tech][year])
            else:
                # print("len",len(self.forecasted_revenue[tech][year]))
                # print(self.forecasted_revenue[tech][year])
                # print("opps")
                continue


####===================investment evaluation and decision processes===========####    
    @classmethod
    def forecast_carbon_price(cls,year,observed_CO2price,recall_years,method):
        if method == "past_experience":
            if len(observed_CO2price) < recall_years:
                past_average = sum(observed_CO2price) / len(observed_CO2price)
            else: 
                past_average = sum (observed_CO2price[-recall_years:]) / recall_years #data of the last 5 years
            # possible_carbon_price = [past_average * n for n in cls.carbon_price_range]
            #print("past_average carbon price",past_average)
            return past_average
        
        elif method == "extrapolate":
            # print(observed_CO2price)
            if year <= recall_years:
                possible_carbon_price = observed_CO2price[-1]

            else:
                x = np.linspace(1, recall_years, num=recall_years, endpoint=True)
                y = observed_CO2price[year-recall_years:year]
                f = np.polyfit(x, y, deg=1)#linear extrpolation
                possible_carbon_price = f[0] * (recall_years+1) + f[1]
            return max(0,possible_carbon_price)

        

    @classmethod
    def forecast_fuel_price (cls,year,observed_fuel_price,recall_years,method):
        if method == "past_experience":
            if len(observed_fuel_price) < 5:
                past_average = sum(observed_fuel_price) / len(observed_fuel_price)
            else: 
                past_average = sum (observed_fuel_price[-recall_years:]) / recall_years #data of the last 5 years
            # possible_fuel_price = [past_average * n for n in cls.fuel_price_range]
            return past_average
        # print(observed_fuel_price)
        
        elif method == "extrapolate":
            if year <= recall_years:
                possible_fuel_price = observed_fuel_price[-1]
            else:
                x = np.linspace(1, recall_years, num=recall_years, endpoint=True)
                y = observed_fuel_price[year-recall_years:year]
                f = np.polyfit(x, y, deg=1)#linear extrpolation
                possible_fuel_price = f[0] * (recall_years+1) + f[1]
            return max(0.001,possible_fuel_price)

    
    @classmethod
    def forecast_el_demand (cls,year,observed_el_demand,recall_years,method):
        if method == "past_experience":
            if len(observed_el_demand) < 5:
                past_average = np.sum(observed_el_demand,axis=0) / len(observed_el_demand)
            else:
                past_average = np.sum (observed_el_demand[-recall_years:],axis=0) / recall_years #data of the last 5 years
            #print("average ele demand",past_average)
            return past_average


        elif method == "extrapolate":
            raise ValueError ("you haven't defined this function")
  



    @classmethod
    def calculate_past_trend (cls,data):
        #print(data)
        a,b = np.polyfit(list(range(1,len(data)+1)),data, deg=1) # linear fit.
        #print('data',data)
        #print('a,b',a,b)
        return a,b #a=the slope of the line/change_rate, b=residuals


    def estimate_profits(self
                        ,year
                        ,possible_carbon_price
                        ,possible_coal_price
                        ,possible_gas_price
                        ,possible_biogas_price
                        ,possible_uranium_price
                        ,electricity_demand
                        ,financial_module
                        ,capacityIncreaseConstraint = True
                        ):

        investment_cadidate = []
        #print("estimate_profits")
        ##===company runs a 'internal' profit estimation simulation===##
        tech_order,cost_order = Power_Company.bid_el_price ( carbon_price = possible_carbon_price
                                                            ,coal_Fuelcost = possible_coal_price
                                                            ,natural_gas_Fuelcost = possible_gas_price
                                                            ,biogas_Fuelcost = possible_biogas_price
                                                            ,uranium_Fuelcost = possible_uranium_price
                                                            )

        for tech in self.tech_preference:# tech_lst_list = company.tech_preference
            if  capacityIncreaseConstraint == True:
                if tech.installed_capacity / max(tech.size, tech.capacity_record[-1]) >= 2 :#capacity has doubled
                    continue
            
            self.NPV_single_assessment[tech] = [] 

            tech.quantity += 1
            supply_lst = (list(zip(*Power_Company.offer_capacity(tech_order))))
            #print(supply_lst)
            slice_revuene,el_price,el_production = zip(*map(func_revenue 
                            ,electricity_demand
                            ,supply_lst
                            ,[cost_order]*len(slice_hours)
                            ,slice_hours
                            ))
            #print(el_price)
            expected_el_price = (sum(np.array(el_price)*np.array(el_production)*np.array(slice_hours))
                                /sum(np.array(el_production)*np.array(slice_hours))) #total_price/total_production
            #print("total production", sum(np.array(el_price)*np.array(el_production)*np.array(slice_hours)/10**9))
            self.forecasted_el_price[year+1].append(expected_el_price)
            
            annual_tech_revuene = np.sum(slice_revuene,axis=0)
            
            PowerPlant.get_revenue_per_plant(annual_tech_revuene, tech_order, Real_lifeMode=False)
    
            # print("self",self.name)
            # print("forecasted_revenue",self.forecasted_revenue[tech][year+1])
            self.forecasted_revenue[tech][year+1].append(tech.revuene_per_plant) #should it mutiplied by (1 - self.hr_tech[tech])??


            revenue_stream_single_assessment = [tech.revuene_per_plant] * tech.lifetime
            
            NPV_single_investment = npf.npv(rate = self.hr_tech[tech], values= [0] +  revenue_stream_single_assessment) - tech.overnight_cost
            self.NPV_single_assessment[tech].append(NPV_single_investment)
            
            tech.average_pofitability = NPV_single_investment / tech.overnight_cost #* tech.CRF (self.hr_tech[tech])
            if tech.average_pofitability > 0:
                investment_cadidate.append(tech)
                
            #print("expected_el_price ",expected_el_price)
            #print(self.NPV_single_assessment[tech])
            tech.quantity -= 1
            continue #go to the next technology
            
                    

        ##================make decision==================##
        if len(investment_cadidate) == 0:
            return None
        else:# len(investment_cadidate)> 0:
            investment_cadidate.sort(key=lambda tech: tech.average_pofitability, reverse=True)
            #print("investment_cadidate ",investment_cadidate)

            if financial_module == "on" :
                decision = self.check_affordability(investment_cadidate[0],year)
            else:
                decision = investment_cadidate[0]
            return decision


   

##end_of_the_code==##