#HAPPI_learning code Version_2022, author: Jinxi
# ###=========import python module==============###
import pathlib
import random
import csv
import numpy as np
from datetime import datetime
import json
# ###=======import self-defined Class================###

##==============
from tax_profile import func_tax
from func_initialize_plants import func_initialize_plant
# ###========import self-defined variables===============###
# from Initialization import Happi,real_carbon_price_profile,real_coal_price_profile,\
#     real_gas_price_profile,electricity_demand_profile,case_name,real_uranium_price_profile,adaptive_rule
from params import slice_hours#,simulation_period#,sliced_el_demand
###=======================###=======================###
##==============start the simulation===============###
# 0) set-up some variables.   
 ##folder for saving data (for plotting).
financial_module = "on"
# technology_learning = "off"

 #years (for update hurdle rate)

def func_main(case_name,adaptive_rule,adaptivity,risk_averse_level,stochasticity,forecast_method,simulation_period,recall_length = 5):
    from cls_Power_Plant import PowerPlant,CoalPlant,GCCPlant#,NuclearPlant
    tech_lst = PowerPlant.__subclasses__()
    from cls_Power_Company import Power_Company
    from cls_system import El_System
    from cls_Fuel import coal,natural_gas,uranium,biogas
    from cls_Consumer import Consumer

    
    A0 = Power_Company(name='A0', adaptivity =  adaptivity , adaptive_rule = adaptive_rule, risk_averse_level = 0)
    A1 = Power_Company(name='A1', adaptivity =  adaptivity , adaptive_rule = adaptive_rule, risk_averse_level = 1)
    A2 = Power_Company(name='A2', adaptivity =  adaptivity , adaptive_rule = adaptive_rule, risk_averse_level = 3)
    A3 = Power_Company(name='A3', adaptivity =  adaptivity , adaptive_rule = adaptive_rule, risk_averse_level = 5)
    # A4 = Power_Company(name='A4', adaptivity =  adaptivity , adaptive_rule = adaptive_rule, risk_averse_level = risk_averse_level)
    # A5 = Power_Company(name='A5', adaptivity =  adaptivity , adaptive_rule = adaptive_rule, risk_averse_level = risk_averse_level)
    # A6 = Power_Company(name='A6', adaptivity =  adaptivity , adaptive_rule = adaptive_rule, risk_averse_level = risk_averse_level)
    # A7 = Power_Company(name='A7', adaptivity =  adaptivity , adaptive_rule = adaptive_rule, risk_averse_level = risk_averse_level)
    # A8 = Power_Company(name='A8', adaptivity =  adaptivity , adaptive_rule = adaptive_rule, risk_averse_level = risk_averse_level)
    # A9 = Power_Company(name='A9', adaptivity =  adaptivity , adaptive_rule = adaptive_rule, risk_averse_level = risk_averse_level)
    A10 = Power_Company(name='A10', adaptivity = False, adaptive_rule = adaptive_rule, hr_initial = 1)


        ##===========initializa Power Company and assign initial plants to agents==========##
    CoalPlant.initial_quantity = 74
    GCCPlant.initial_quantity = 6
    func_initialize_plant(owner_lst=[A10],initial_tech_lst=[CoalPlant,GCCPlant])
    PowerPlant.record_data(tech_lst)

    Power_Company.lst.pop(-1)#remove the "A10" from the list for future investments.
    #company_lst = sorted(Power_Company.lst, key=lambda x: x.name)##sort list by company's name
    

    ##===========initializa the electricity system==========##
    Happi = El_System()
    Happi.capacity_mix = {pp: pp.quantity * pp.size for pp in PowerPlant.__subclasses__()}
        
    
    real_coal_price_profile = coal.func_fuel_price(total_years = simulation_period
                                            ,mean = coal.fuel_cost ##the mean of the random numbers
                                            ,eps1 = 0.15
                                            ,eps2 = 0.3
                                            ,stochasticity = False #stochastic,constant
                                            )

    real_gas_price_profile = natural_gas.func_fuel_price(total_years = simulation_period
                                                        ,mean = natural_gas.fuel_cost ##the mean of the random numbers
                                                        ,eps1 = 0.15
                                                        ,eps2 = 0.3
                                                        ,stochasticity = stochasticity  #True, False
                                                        )

    real_biogas_price_profile = biogas.func_fuel_price(total_years = simulation_period
                                                        ,mean = biogas.fuel_cost ##the mean of the random numbers
                                                        ,eps1 = 0.15
                                                        ,eps2 = 0.3
                                                        ,stochasticity = stochasticity  #stochastic, constant
                                                        )
    #print(real_biogas_price_profile)
    real_uranium_price_profile = uranium.func_fuel_price(total_years = simulation_period
                                                        ,mean = uranium.fuel_cost ##the mean of the random numbers
                                                        ,eps1 = 0.15
                                                        ,eps2 = 0.3
                                                        ,stochasticity = stochasticity  #stochastic,constant
                                                        )

    #(2) stochastic electricity demand
    ## consumer needs electricity.#consumer is characterise by price elasticity
    electricity_demand_profile = Consumer.express_demand(product = "electricity"
                                                        ,total_years = simulation_period
                                                        ,mean = 1
                                                        ,eps1 = 0.5
                                                        ,eps2 = 0.1
                                                        ,stochasticity = stochasticity  #constant
                                                        )

    #(3) (stochastic) carbon price scenario==##
    tax_scenario ="grow" #'grow','no_tax','constant'
    real_carbon_price_profile = func_tax(simulation_period
                                        ,tax_scenario
                                        ,initial_tax = 0
                                        ,start_year= 10
                                        ,max_tax= 100
                                        ,eps1 = 0.5
                                        ,eps2 = 0.3
                                        ,stochasticity = stochasticity
                                        )

    
    sub_name = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")##use the current time as the file name (to export data).
    for year in range (0,simulation_period):#simulation_period
        if year % 50 == 0:
            print('\n','year: ', year)
        # 1) The power companies bid electricity production.
        carbon_price = real_carbon_price_profile [year]
        coal.fuel_cost = real_coal_price_profile [year]
        natural_gas.fuel_cost = real_gas_price_profile [year]
        biogas.fuel_cost = real_biogas_price_profile [year]
        uranium.fuel_cost = real_uranium_price_profile [year]

        tech_order,cost_order = Power_Company.bid_el_price (carbon_price = carbon_price)
        # supply_lst = Power_Company.offer_capacity(tech_order)
        supply_lst = [tech.available_capacity() for tech in tech_order]
        supply_lst = (list(zip(*supply_lst))) #supply profile for each 64 slices.
        # print(supply_lst)
        ##==the market clears demand and supply, return electricity price and production of each slice
        el_price,el_production,slice_revuene,dispatch_lst = Happi.clear_the_market ( supply_lst
                                                                                    ,cost_order
                                                                                    ,slice_hours
                                                                                    ,electricity_demand = electricity_demand_profile [year]
                                                                                    )
        # print(len(el_price))
        Happi.record_el_price(el_price,el_production,slice_hours)
        Happi.record_production (el_price,tech_order,dispatch_lst,slice_hours)
        Happi.record_CO2_emission(year,carbon_price)
        Happi.record_biogas_production(year)
        #print(f'Happi.electricity_price {Happi.electricity_price[year]:.4f}')

        ##===========================companies update financial status===========######
        annual_tech_revuene = np.sum(slice_revuene,axis=0) #net revenue per technology
        #print('annual_tech_revuene',annual_tech_revuene)
        PowerPlant.get_revenue_per_plant(annual_tech_revuene,tech_order,Real_lifeMode = True)


        for company in Power_Company.lst: #each company updates cash on its bank account
            portfolio_revenue = company.calculate_revenue()#calculate the total portfolio revenue and per technology.
            #print('name: ',company.name)
            #print('revenue: ',round(portfolio_revenue/10**6,2))
            # print('cash1: ',round(company.cash/10**6,2)) 
            company.update_cash(portfolio_revenue)
            # print('cash2: ',round(company.cash/10**6,2)) 
            company.pay_back_debt(year)
            company.record_financial_variable(portfolio_revenue,year) #record net income,debt,cash,equity.
            company.calculate_forecasted_performance(year)

            company.calculate_cash_flow(year,tech_lst) ## calculate revenue for each technology

            if financial_module == "on":
                if company.status == 'active' and company.equity < 0:#check_bankruptcy
                    company.status = year #no further investment will be allowed.
                    Power_Company(name = company.name + "_new"
                                  ,adaptivity =  company.adaptivity
                                  ,adaptive_rule = company.adaptive_rule
                                  ,risk_averse_level = company.risk_averse_level)
                    #Power_Company.bankruptLst[company.name] = year
    
                    print('you are bankrupt '+ company.name)
                    

            #if company.status == 'active':
                #company.pay_dividend() #company pays out dividend to shareholders
            
            ##=============update hurdle rate=========###
            if ( year >= recall_length + 1 and company.adaptivity == True):
                company.adapt_hurdle_rate(year
                                        ,recall_length
                                        #,information = "public"
                                        #,risk_measurement = adaptive_rule #"forecasted_revenue", "annuitized_cost"
                                        #,uniformStep = True
                                        )##information="private"
            continue
        
        ##=============================================================######
        ##===========================check system status===========######
        ## lifespan of plants minus 1, and return the plants has 0 lifespan.
        decommission_lst = PowerPlant.lifespan_minus_1()
        #print(' decommission_lst ',decommission_lst)
        ## how variable(carbon price) has chaneged in the past years
        
        possible_carbon_prices = Power_Company.forecast_carbon_price(year = year
                                                                    ,observed_CO2price = real_carbon_price_profile[:year+1]
                                                                    ,recall_years = recall_length
                                                                    ,method = forecast_method
                                                                    )##method="past_experience" or "extrapolate"

        possible_coal_prices = Power_Company.forecast_fuel_price(year = year
                                                                ,observed_fuel_price = real_coal_price_profile[:year+1]
                                                                ,recall_years = recall_length
                                                                ,method = forecast_method
                                                                )
        
        possible_gas_prices = Power_Company.forecast_fuel_price(year = year
                                                                ,observed_fuel_price = real_gas_price_profile[:year+1]
                                                                ,recall_years = recall_length
                                                                ,method = forecast_method
                                                                )

        possible_biogas_prices = Power_Company.forecast_fuel_price(year = year
                                                                ,observed_fuel_price = real_biogas_price_profile[:year+1]
                                                                ,recall_years = recall_length
                                                                ,method = forecast_method
                                                                )
        
        possible_uranium_price = Power_Company.forecast_fuel_price(year = year
                                                                ,observed_fuel_price = real_uranium_price_profile[:year+1]
                                                                ,recall_years = recall_length
                                                                ,method = forecast_method
                                                                )
       
        possible_el_demad = Power_Company.forecast_el_demand(year = year
                                                            ,observed_el_demand = electricity_demand_profile[:year+1]
                                                            ,recall_years = recall_length
                                                            ,method = "past_experience"
                                                            )
        
        
        #print(possible_carbon_prices)

        while True: #as long as the decommission_lst is not empty.
            #print('check1')
            if decommission_lst:#if the decomission is not empty.
                PowerPlant.decommission_one_plant(decommission_lst)
                #print('\n','decommission')
                ##===========================new investment decisions===========######
            random.shuffle(Power_Company.lst) #randomize the order of companies for investment.
            while True:
                count_NO = 0 #counting the number of "No investment"
                for company in Power_Company.lst:
                    #if (company.status != 'active' or company.debt_to_equity_ratio > 0.5):
                    if company.status != 'active' :
                        count_NO += 1
                        continue
                    #print('name: ',company.name)
                    else:
                        invesment_decision = company.estimate_profits(year = year
                                                                    ,possible_carbon_price = possible_carbon_prices
                                                                    ,possible_coal_price = possible_coal_prices
                                                                    ,possible_gas_price = possible_gas_prices
                                                                    ,possible_biogas_price = possible_biogas_prices
                                                                    ,possible_uranium_price = possible_uranium_price
                                                                    ,electricity_demand = possible_el_demad
                                                                    ,financial_module = financial_module
                                                                    ,capacityIncreaseConstraint = True
                                                                    )
            
                        if invesment_decision != None:
                            new_plant = invesment_decision(owner=company)#The power companies 'construct' the newly invested plant and update the capacity mix
                            new_plant.record_annual_investment(year)#record how many new plants are invested per year
                            #print('\n',"the newly invested plant is a", type(new_plant).__name__)
                            company.portfolio[type(new_plant)] += 1 #add the new_plant to the corresponding compamy's portfolio.
                            company.annual_investment[type(new_plant)][year] += 1 ##record annual investments for poltting.
                            company.update_repayment_schedule_and_financial_status(year,new_plant) ##update installment and principle_payment.
                            # print('owner',company.name)
                            continue

                        else:# invesment_decision == None:
                            #print('investment decision: None')
                            count_NO += 1
                            continue

                if count_NO == len(Power_Company.lst): #no companies wants to make more investment.
                    break
                else: continue
                
            if (not decommission_lst and count_NO == len(Power_Company.lst)):
                break
            else:
                continue
        # if year == 45:
        #     new_plant = NuclearPlant(owner=company)#The power companies 'construct' the newly invested plant and update the capacity mix
        #     new_plant.record_annual_investment(year)#record how many new plants are invested per year
        #     #print('\n',"the newly invested plant is a", type(new_plant).__name__)
        #     company.portfolio[type(new_plant)] += 1 #add the new_plant to the corresponding compamy's portfolio.
        #     company.annual_investment[type(new_plant)][year] += 1 ##record annual investments for poltting.
        #     company.update_repayment_schedule_and_financial_status(year,new_plant) 

        PowerPlant.record_data(tech_lst) #record capacity mix and overnight cost.
        # if technology_learning == "on":
        #     PowerPlant.technology_learning(year) ##update the overnight cost of each technology.

        for company in Power_Company.lst:
            company.record_individual_data(tech_lst,year) #record own portfolio and hr (for later plotting)
        
        continue # year +=1 #go to next year
    ####================#######end######==================######
    print("END of the simulation","\n")
    # print(int(pp.quantity) for pp in tech_lst) #print out the final capacity mix.

    ####======================================##########======================================######
    #===========export and save final results==========#
    # Answer = input('Do you want to continue with saving data to CSV? Type yes or no: ')
    # if Answer == ('yes') or Answer == ('y'):
    #     print ('saving the data')
    savepath = "C:/Users/jinxi/OneDrive - Chalmers/ABM model/paperIV_learning/model/model_output/" + case_name + "/"
    pathlib.Path(savepath).mkdir(parents=True, exist_ok=True) 

    # #==== system variables====##
    save_variables = ["system_installed_capacity"
                    ,"electricity_production"
                    ,"biogas_production"
                    ,"average_electricity_price"
                    ,"slice_electricity_price"
                    ,"real_carbon_price"
                    ,"real_coal_price_profile"
                    ,"real_gas_price_profile"
                    ,"real_biogas_price_profile"
                    ,"real_uranium_price_profile"
                    ,"electricity_demand_profile"
                    ,"CO2_emission"
                    ,"tech_revenue"
                    ,"tech_performance"
                    #,"hurdle_rates"
                    ,"total_experience"
                    # ,"price_produce"
                    ]

    for variable in save_variables:
        savepath_sub1 = savepath + variable
        pathlib.Path(savepath_sub1).mkdir(parents=True, exist_ok=True)
        with open(savepath_sub1 +"/"+ sub_name +'.csv','w', newline='') as f:
            writer = csv.writer(f)

            if variable == "system_installed_capacity":##save system capacity#
                for tech in tech_lst:
                    writer.writerow([tech.__name__[0:-5]]+tech.capacity_record)

            elif variable == "electricity_production":
                for tech in tech_lst:
                    writer.writerow([tech.__name__[0:-5]]+tech.production_quantity)
            
            elif variable == "biogas_production":
                writer.writerow(GCCPlant.biogas_production)

            elif variable == "average_electricity_price":
                writer.writerow(Happi.average_electricity_price)

            elif variable == "slice_electricity_price":
                for yr, value in enumerate(Happi.slice_electricity_price):
                    writer.writerow([yr] + value.tolist())

            elif variable == "real_carbon_price":
                writer.writerow(real_carbon_price_profile)
            
            elif variable == "real_coal_price_profile":
                writer.writerow(real_coal_price_profile)

            elif variable == "real_gas_price_profile":
                writer.writerow(real_gas_price_profile)

            elif variable == "real_biogas_price_profile":
                writer.writerow(real_biogas_price_profile)
            
            elif variable == "real_uranium_price_profile":
                writer.writerow(real_uranium_price_profile)
            
            elif variable == "electricity_demand_profile":
                for el_demand in electricity_demand_profile:
                    writer.writerow(el_demand[:4])

            elif variable == "CO2_emission":
                writer.writerow(Happi.CO2_emission)
            
            elif variable == "tech_revenue":
                for tech in tech_lst:
                    writer.writerow([tech.__name__[0:-5]]+tech.annual_revenue_records)
            
            elif variable == "tech_performance":
                for tech in tech_lst:
                    writer.writerow([tech.__name__[0:-5]]+tech.performance_indicator_lst)

            elif variable == "total_experience":
                for tech in tech_lst:
                    writer.writerow([tech.__name__[0:-5]] + [tech.total_experience])
        
                


    # #====save Power_Company's data====#####
    company_level_variables = [
                            "company_portfolio"
                            ,"annual_investment"
                            ,"company_hr"
                            ,"debt"
                            ,"cash"
                            ,"net_income"
                            ,"equity"
                            ,"company_revenue"
                            ,"plant_value_lst"
                            ,"forecasted_revenue"
                            ,"forecasted_el_price"
                            ,"cash_flow"
                            ]

    for variable in company_level_variables:
        for company in Power_Company.lst:
            savepath_sub2 = savepath +"/"+ variable + "/" + company.name
            pathlib.Path(savepath_sub2).mkdir(parents=True, exist_ok=True) 
            with open(savepath_sub2 + "/" + sub_name + '.csv','w', newline='') as f:
                writer = csv.writer(f)
                if variable == "company_portfolio":
                    for tech in tech_lst:
                        writer.writerow([tech.__name__[0:-5]] + company.portfolio_lst[tech])
                
                elif variable == "annual_investment":
                    for tech in tech_lst:
                        writer.writerow([tech.__name__[0:-5]] + company.annual_investment[tech])
                
                elif variable == "company_hr":
                    for tech in tech_lst:
                        writer.writerow([tech.__name__[0:-5]] + company.hr_lst[tech])

                elif variable == "debt":
                    writer.writerow(company.debt_lst)
                
                elif variable == "cash":
                    writer.writerow(company.cash_lst)

                elif variable == "net_income":
                    writer.writerow(company.net_income_lst)

                elif variable == "equity":
                    writer.writerow(company.equity_lst)

                elif variable == "company_revenue":
                    for tech in tech_lst:
                        writer.writerow([tech.__name__[0:-5]] + company.revenue[tech])

                elif variable == "plant_value_lst":
                    for tech in tech_lst:
                        writer.writerow([tech.__name__[0:-5]] + company.plant_value_lst[tech])
                
                elif variable == "forecasted_revenue":
                    for tech in tech_lst:
                        writer.writerow([tech.__name__[0:-5]] + company.forecasted_revenue[tech])
                
                elif variable == "forecasted_el_price":
                    for key in company.forecasted_el_price.keys():
                        if len(company.forecasted_el_price[key]) != 0:
                            average_value = sum(company.forecasted_el_price[key]) / len(company.forecasted_el_price[key])
                        elif key == 0:
                            average_value = Happi.average_electricity_price[key]
                        else:
                            average_value = "nan"
                        f.write("%s,%s\n"%(key,average_value))

                elif variable == "cash_flow":
                    for tech in tech_lst:
                        writer.writerow([tech.__name__[0:-5]] + company.cash_flow[tech])
                
                


    bankruptcy_data = {company.name : company.status for company in Power_Company.lst}
    bankruptcy_file = savepath + "bankruptcy.json"

    if not pathlib.Path(savepath + "bankruptcy.json").exists(): 
        writing_mode = "w" #write
    else:
        writing_mode = "a" #append
    with open(bankruptcy_file, mode=writing_mode) as f:
        json_string = json.dumps({sub_name: bankruptcy_data})
        f.write(json_string + '\n')



    if not pathlib.Path(savepath + "company_attribute.json").exists():
        company_attribute = {company.name : {"adaptivity":company.adaptivity,"risk_level": company.risk_averse_level} for company in Power_Company.lst}
        writing_mode = "w" #write
        with open(savepath + "company_attribute.json", mode=writing_mode) as f:
            json_string = json.dumps(company_attribute)
            f.write(json_string)


    if not pathlib.Path(savepath + "price_produce.json").exists():
        price_produce = {tech.name: tech.price_produce for tech in tech_lst}
        with open(savepath + "price_produce.json", "w") as f:
            json.dump(price_produce, f)