# This scripts initializes a Model_Manager object a Traffic_Model and Cost_Function object
# It uses as input a Demand_Assignment objects (demand per path and per time) to generate costs per path as
# a Path_Costs object
# This particular model uses a Static model and BPR Cost_Function model

import numpy as np
from copy import deepcopy

from Cost_Functions.BPR_Function import BPR_Function_class
from Traffic_Models.Static_Model import Static_Model_Class
from Solvers.Solver_Class import Solver_class
from Data_Types.Demand_Assignment_Class import Demand_Assignment_class
from Data_Types.Link_Costs_Class import Link_Costs_class
from py4j.java_gateway import JavaGateway,GatewayParameters
from Model_Manager.Link_Model_Manager import Link_Model_Manager_class


# ==========================================================================================
# This code is used on any Windows systems to self start the Entry_Point_BeATS java code
# This code launches a java server that allow to use Beasts java object
import os
import signal
import subprocess
import time
import sys
import inspect

this_folder = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

jar_file_name = os.path.join(this_folder,'py4jbeats-1.0-SNAPSHOT-jar-with-dependencies.jar')
port_number = '25335'
print("Staring up the java gateway to access the Beats object")
try:
    process = subprocess.Popen(['java', '-jar', jar_file_name, port_number],
                               stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    time.sleep(0.5)
except subprocess.CalledProcessError:
    print("caught exception")
    sys.exit()


# End of Windows specific code
# ======================================================================================

# Contains local path to input configfile, for the three_links.xml network
configfile = os.path.join(this_folder,os.path.pardir,'configfiles','seven_links.xml')

#coefficients = {0L:[1,0,0,0,1],1L:[1,0,0,0,1],2L:[1,0,0,0,1]}
coefficients = {0L:[1,0,0,0,1],1L:[1,0,0,0,1],2L:[5,0,0,0,5], 3L:[2,0,0,0,2], 4L:[2,0,0,0,2], 5L:[1,0,0,0,1], 6L:[5,0,0,0,5]}

port_number = int(port_number)
gateway = JavaGateway(gateway_parameters=GatewayParameters(port=port_number))
beats_api = gateway.entry_point.get_BeATS_API()
beats_api.load(configfile)

# This initializes an instance of static model from configfile
scenario  = Static_Model_Class(beats_api, 1, 1)

# If scenario.beast_api is none, it means the configfile provided was not valid for the particular traffic model type
if(scenario.beats_api != None):
    # Initialize the BPR cost function
    BPR_cost_function = BPR_Function_class(coefficients)
    scenario_solver = Solver_class(scenario, BPR_cost_function)
    assignment, flow_sol = scenario_solver.Solver_function()


    # Cost resulting from the path_based Frank-Wolfe
    link_states = scenario.Run_Model(assignment)
    cost_path_based = BPR_cost_function.evaluate_BPR_Potential(link_states)

    # Cost resulting from link-based Frank-Wolfe
    cost_link_based = BPR_cost_function.evaluate_BPR_Potential_FW(flow_sol)

    link_states.print_all()
    print flow_sol
    print "path-based cost: ", cost_path_based
    print "link-based cost: ", cost_link_based
