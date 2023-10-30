##initialize existing (coal and gas) power plants.
#from cls_Power_Company import Power_Company#,old_company
from itertools import cycle
import random
def func_initialize_plant (owner_lst,initial_tech_lst):
    for tech in initial_tech_lst:
        random.shuffle(owner_lst) ##shuffle the order.
        lifespan = list(range(tech.lifetime,0,-1))#range backwards.
        #lifespan = list(range(1,tech.lifetime+1))#range backwards.
        for company,yr,nr in zip(cycle(owner_lst),cycle(lifespan),range(tech.initial_quantity)):
            tech(owner = company,lifespan = yr) #evenly disribute lifespan.
            company.portfolio[tech] += 1 ##add the plant to the owner's portfolio.
