#Static Traffic Model, assuming the demand is fixed

from Abstract_Traffic_Model import Abstract_Traffic_Model_class
from Data_Types.State_Trajectory_Class import State_Trajectory_class
from Traffic_States.Static_Traffic_State import Static_Traffic_State_class


class Static_Model_Class(Abstract_Traffic_Model_class):
    #Configfile is needed to initialize the model's scenario via beats_api
    def __init__(self, beats_api, num_steps, dt):
        Abstract_Traffic_Model_class.__init__(self, beats_api)
        self.model_type = 's'     #Indicates that this is a static model
        self.num_time_steps = num_steps    # Keeps track of the number of time_steps associated with the model
        self.dt = dt

        if not self.Validate_Configfile():
            self.beats_api = None
            return

    def get_num_steps(self):
        return self.num_time_steps

    def get_dt(self):
        return self.dt

    def Validate_Configfile(self):
        # If the configfile indicates varying demand, return with an error
        # We first want to check the configfile to make sure it is in correct format
        demand_array = self.beats_api.get_demands()
        valid = True
        i = 0 # index in the demand_arrary matrix
        while i < demand_array.__len__() and valid:
            if demand_array[i].getProfile().num_values() > 1:
                return False
            i = i + 1
        return True

    # Overides the Run_Model function in the abstract class
    # Returns an array of link states where each entry indicates the flow per link, per commodity and per time step
    def Run_Model(self, demand_assignments, initial_state = None, dt = None, T = None):
        # Initialize the State_Trajectory object
        link_states = State_Trajectory_class( list(self.beats_api.get_link_ids()),
                                                 list(self.beats_api.get_commodity_ids()), 1, 1)
        for key in demand_assignments.get_all_demands().keys():
            route = demand_assignments.get_path_list()[key[0]]
            for link_id in route:
                if (link_id,key[1]) not in link_states.get_all_states().keys():
                    state = Static_Traffic_State_class()
                    link_states.set_state_on_link_comm_time(link_id, key[1], 0, state)

                demand_value = demand_assignments.get_demand_at_path_comm_time(key[0], key[1], 0)
                link_states.get_state_on_link_comm_time(link_id, key[1], 0).add_flow(demand_value)

        return link_states

    def get_total_demand(self):
        demands = self.beats_api.get_demands()
        total_demand = 0

        for demand in demands:
            total_demand = total_demand + demand.getProfile().get_value(0)*3600

        return total_demand