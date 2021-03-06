
import unittest
import numpy as np

from Solvers.Frank_Wolfe_Solver_Static import Frank_Wolfe_Solver
from Solvers.Path_Based_Frank_Wolfe_Solver import Path_Based_Frank_Wolfe_Solver
#from Solvers.Decomposition_Solver import Decomposition_Solver
from Model_Manager.Link_Model_Manager import Link_Model_Manager_class
from Java_Connection import Java_Connection
from Data_Types.Demand_Assignment_Class import Demand_Assignment_class

import os
import inspect


class TestStatic(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        # make Java connection
        cls.connection = Java_Connection()

        # create a static/bpr model manager
        this_folder = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        configfile = os.path.join(this_folder, os.path.pardir, 'configfiles', 'seven_links.xml')
        bpr_coefficients = {0L: [1, 0, 0, 0, 1], 1L: [1, 0, 0, 0, 1], 2L: [5, 0, 0, 0, 5], 3L: [2, 0, 0, 0, 2],
                        4L: [2, 0, 0, 0, 2], 5L: [1, 0, 0, 0, 1], 6L: [5, 0, 0, 0, 5]}
        cls.model_manager = Link_Model_Manager_class(configfile, "static", cls.connection, None, "bpr", bpr_coefficients)

        # create a demand assignment
        api = TestStatic.model_manager.beats_api

        time_period = 1  # Only have one time period for static model
        paths_list = list(api.get_path_ids())
        commodity_list = list(api.get_commodity_ids())
        route_list = {}

        for path_id in paths_list:
            route_list[path_id] = api.get_subnetwork_with_id(path_id).get_link_ids()

        # Creating the demand assignment for initialization
        cls.demand_assignments = Demand_Assignment_class(route_list, commodity_list, time_period, dt=time_period)
        demands = {}
        demand_value = np.zeros(time_period)
        demand_value1 = np.zeros(time_period)
        demand_value[0] = 2
        demand_value1[0] = 2
        demands[(1L, 1L)] = demand_value
        demands[(2L, 1L)] = demand_value1
        demands[(3L, 1L)] = demand_value
        cls.demand_assignments.set_all_demands(demands)

    def check_manager(self):
        self.assertTrue(TestStatic.model_manager.is_valid())

    def test_model_run(self):
        traffic_model = TestStatic.model_manager.traffic_model
        link_states = traffic_model.Run_Model(TestStatic.demand_assignments)
        self.assertTrue(self.check_assignments(link_states))

    def test_link_cost(self):
        traffic_model = TestStatic.model_manager.traffic_model
        link_states = traffic_model.Run_Model(TestStatic.demand_assignments)
        link_costs = TestStatic.model_manager.cost_function.evaluate_Cost_Function(link_states)
        self.assertTrue(self.check_link_costs(link_costs))

    def test_link_based_fw(self):
        frank_sol = Frank_Wolfe_Solver(self.model_manager)


    def test_path_based_fw(self):
        num_steps = 1
        eps = 1e-2
        frank_sol = Frank_Wolfe_Solver(self.model_manager)
        assignment_seq = Path_Based_Frank_Wolfe_Solver(self.model_manager, num_steps)
        # Cost resulting from the path_based Frank-Wolfe
        link_states = self.model_manager.traffic_model.Run_Model(assignment_seq)
        cost_path_based = self.model_manager.cost_function.evaluate_BPR_Potential(link_states)

        # Cost resulting from link-based Frank-Wolfe
        cost_link_based = self.model_manager.cost_function.evaluate_BPR_Potential_FW(frank_sol)

        self.assertTrue(np.abs(cost_link_based-cost_path_based) < eps)

    '''
    def test_decomposition_solver(self):
        number_of_subproblems = 1
        start_time1 = timeit.default_timer()
        assignment_dec, error = Decomposition_Solver(self.traffic_scenario, self.Cost_Function, number_of_subproblems)
        print "Decomposition finished with error ", error
        elapsed1 = timeit.default_timer() - start_time1
        print ("Decomposition Path-based took  %s seconds" % elapsed1)
    '''
    def check_assignments(self, link_states):
        links_flows = {(0L,1L): [6], (1L,1L): [4], (2L,1L): [2], (3L,1L): [2],
                       (4L,1L): [2], (5L,1L): [2], (6L,1L): [4]}
        states = link_states.get_all_states()
        for key in states.keys():
            if states[key][0].get_flow() != links_flows[key][0]:
                return False

        return True

    def check_link_costs(self, link_costs):
        cost_links = {(0L,1L): [1297], (1L,1L): [257], (2L,1L): [85], (3L,1L): [34],
                       (4L,1L): [34], (5L,1L): [17], (6L,1L): [1285]}

        states = link_costs.get_all_costs()
        for key in states.keys():
            if states[key][0] != cost_links[key][0]:
                return False

        return True