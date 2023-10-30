#CLASS consumer
from params import sliced_el_demand
import numpy as np

class Consumer ():
    @classmethod
    def express_demand(cls,product,stochasticity,total_years=1,mean=1,eps1=1,eps2=0):
        if product == 'electricity' or product == 'el':
            if stochasticity == True:
                demand_scale = np.empty(total_years)
                # print(demand_scale)
                demand_scale [0] = mean
                
                for yr in range(total_years-1):
                    demand_scale[yr+1] = demand_scale[yr] + eps1 * (mean - demand_scale[yr]) + eps2 * mean * np.random.uniform(-1,1)
                return [scale * sliced_el_demand for scale in demand_scale]
            
            else:

                return [sliced_el_demand] * total_years
        
        else:##e.g.product == demand heat
            raise ValueError ('We are sorry to inform you that HAPPI cannot provide ' + product + ' at the moment.')


# electricity_demand_profile = Consumer.express_demand(product = "electricity"
#                                                     ,total_years = 100
#                                                     ,mean = 1
#                                                     ,eps1 = 0.5
#                                                     ,eps2 = 0.1
#                                                     ,stochasticity = True  #constant
#                                                     )
