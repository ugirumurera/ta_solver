# This is a path_based implementation of Frank-Wolfe
# OD stands for origin destination pair

# October 19, 2017: We are adding a new cost_function, coefficients parameters at the end of Path_Based_Frank_Wolfe_Solver function, to solve convex
# optimization problems that arise when solving the Dynamic Traffic Assignment Problem as a general Variational Inequality problem.
# This "cost_function" will replace all the instances when the model_manager's evaluate method is called.
# Coefficients are parameters for the cost_function

from __future__ import division

from Data_Types.Demand_Assignment_Class import Demand_Assignment_class

from copy import copy
import numpy as np
import timeit
from All_or_Nothing_Function import all_or_nothing
from Method_Successive_Averages_Solver import Method_of_Successive_Averages_Solver

# od is used in decomposition mode, where od is the subset of origin-destination pairs to consider for one
# decomposition subproblem
#Added od_out_indices to be used in the parallel version on the algorithm
# od_out_indices are the indices in the assignment vector that is not modified by the current subproblem
# Timer is used to calculate the time spent in path costs evaluation
def Path_Based_Frank_Wolfe_Solver(model_manager, T, sampling_dt,  od = None, od_out_indices = None, assignment = None,
                                  past=10, max_iter=1000, eps=1e-4, q=50, display=1, stop=1e-2, timer = None):
    # In this case, x_k is a demand assignment object that maps demand to paths
    # Constructing the x_0, the initial demand assignment, where all the demand for an OD is assigned to one path
    # We first create a list of paths from the traffic_scenario

    num_steps = int(T / sampling_dt)

    sim_time = 0    # simulation time
    comm_time = 0   # communication time

    # If no subset of od provided, get od from the model manager
    if od is None:
        od = list(model_manager.get_OD_Matrix(num_steps, sampling_dt))


    init_vector = None
    x_assignment_vector = None

    if assignment is not None:
        init_vector = np.asarray(assignment.vector_assignment())

    if assignment is None or np.count_nonzero(init_vector) == 0:
        assignment, x_assignment_vector, temp_sim_time, temp_comm_time = Method_of_Successive_Averages_Solver(model_manager, T, sampling_dt, od, od_out_indices,
                                                                      assignment, max_iter = 100, display = display)
        sim_time = sim_time + temp_sim_time
        comm_time = comm_time + temp_comm_time

    #If assignment is None, then return from the solver
    if assignment is None:
        print "Demand dt is less than sampling dt, or demand not specified properly"
        return None, None

    #assignment, start_cost = all_or_nothing(model_manager, assignment, od, None, T)
    path_list = assignment.get_path_list()
    past_assignment = np.zeros((len(path_list.keys())*num_steps, past), dtype="float64")


    for i in range(max_iter):
        # All_or_nothing assignment
        #start_time1 = timeit.default_timer()
        y_assignment, current_path_costs, temp_sim_time = all_or_nothing(model_manager, assignment, od, None, T)
        sim_time = sim_time + temp_sim_time
        #elapsed1 = timeit.default_timer() - start_time1
        #print ("All_or_nothing took  %s seconds" % elapsed1)

        if x_assignment_vector is None: x_assignment_vector = np.asarray(assignment.vector_assignment())

        # When in parallel strategy, the y_assignment_vector has to be combined from all subproblems
        # If we are doing the parallel strategy, then od_out_indices is not None
        if od_out_indices is not None :
            from mpi4py import MPI
            comm = MPI.COMM_WORLD
            y_temp_vector = np.asarray(y_assignment.vector_assignment())
            y_assignment_vector = np.zeros(len(y_temp_vector))

            # First zero out the values corresponding to other subproblems
            y_temp_vector[od_out_indices] = 0

            # Combine assignment from all subproblems into ass_vector
            start_time1 = timeit.default_timer()

            comm.Allreduce(y_temp_vector, y_assignment_vector, op=MPI.SUM)

            elapsed1 = timeit.default_timer() - start_time1
            comm_time = comm_time + elapsed1

            if display == 1: print ("Communication took  %s seconds" % elapsed1)

        else:
            y_assignment_vector = np.asarray(y_assignment.vector_assignment())

        # Calculating the error
        current_cost_vector = np.asarray(current_path_costs.vector_path_costs())

        error = np.abs(np.dot(current_cost_vector, y_assignment_vector - x_assignment_vector) /
                       np.dot(y_assignment_vector, current_cost_vector))

        #error = distance_to_Nash(assignment,current_path_costs,od)

        if error < stop :
            if display == 1: print "FW Stop with error: ", error
            return assignment, x_assignment_vector, sim_time, comm_time

        if display == 1: print "FW iteration: ", i, ", error: ", error

        past_assignment[:,i%past] = y_assignment_vector
        d_assignment = y_assignment_vector-x_assignment_vector

        if i > q:
            # step 3 of Fukushima
            v = np.sum(past_assignment,axis=1) / min(past,i+1) - x_assignment_vector
            norm_v = np.linalg.norm(v,1)
            if norm_v < eps:
                if display >= 1: print 'FW stop with norm_v: {}'.format(norm_v)
                return assignment, x_assignment_vector, sim_time, comm_time
            norm_w = np.linalg.norm(d_assignment,1)
            if norm_w < eps:
                if display >= 1: print 'FW stop with norm_w: {}'.format(norm_w)
                return assignment, x_assignment_vector, sim_time, comm_time
            # step 4 of Fukushima
            gamma_1 = current_cost_vector.dot(v) / norm_v
            gamma_2 = current_cost_vector.dot(d_assignment) / norm_w
            if gamma_2 > -eps:
                if display >= 1: print 'FW stop with gamma_2: {}'.format(gamma_2)
                return assignment, x_assignment_vector, sim_time, comm_time
            d = v if gamma_1 < gamma_2 else d_assignment

        else:
            d = d_assignment

        # step 5 of Fukushima
        start_time1 = timeit.default_timer()
        s = line_search(model_manager, assignment, x_assignment_vector, y_assignment, y_assignment_vector,
                        d, 1e-8, timer = timer)
        #s = line_search_original(model_manager, assignment, x_assignment_vector, d)
        elapsed1 = timeit.default_timer() - start_time1
        #if display == 1: print ("Line_Search took  %s seconds" % elapsed1)

        if s < eps:
            if display >= 1: print 'FW stop with step_size: {}'.format(s)
            return assignment, x_assignment_vector, sim_time, comm_time

        x_assignment_vector = x_assignment_vector + s*d
        assignment.set_demand_with_vector(x_assignment_vector)

    return assignment, x_assignment_vector, sim_time, comm_time

def line_search(model_manager, x_assignment, x_vector, y_assignment, y_vector, d_vector, eps, timer = None):
    # alfa = 0 corresponds to when assignment is equal to original assignment x_assignment
    sampling_dt = x_assignment.get_dt()
    T = sampling_dt * x_assignment.get_num_time_step()

    g0 = g_function(model_manager, x_assignment, T, d_vector, timer = timer)

    # alfa = 1 corresponds to when assignment is equal to all_or_nothing assignment y_assignment
    g1 = g_function(model_manager, y_assignment, T, d_vector,timer = timer)

    if (g0 > 0 and g1 > 0) or (g0 < 0 and g1 < 0):
        if np.abs(g0) <= np.abs(g1):
            return 0
        else:
            return 1

    l, r = 0, 1

    # Initializing the demand assignment
    commodity_list = x_assignment.get_commodity_list()
    num_steps = x_assignment.get_num_time_step()
    path_list = x_assignment.get_path_list()

    while r-l > eps:
        m = (l+r)/2
        m_vector = x_vector + m * d_vector
        m_assignment = Demand_Assignment_class(path_list, commodity_list, num_steps, sampling_dt)
        m_assignment.set_all_demands(x_assignment.get_all_demands())
        m_assignment.set_demand_with_vector(m_vector)
        g_m = g_function(model_manager, m_assignment, T, d_vector,timer = timer)

        if (g_m < 0 and np.abs(g_m) > eps and g1 > 0) or (g_m > 0 and np.abs(g_m) > eps and g1 < 0):
            l = copy(m)
            g0 = copy(g_m)
        elif (g_m < 0 and np.abs(g_m) > eps and g0 > 0) or (g_m > 0 and np.abs(g_m) > eps and g0 < 0):
            r = copy(m)
            g1 = copy(g_m)
        else: return m

    return l


def g_function(model_manager, assignment, T, d_vector, timer = None):
    #y_vector = assignment.vector_assignment()

    start_time1 = timeit.default_timer()
    path_costs = model_manager.evaluate(assignment, T, initial_state=None)
    elapsed1 = timeit.default_timer() - start_time1
    if timer is not None:
        timer[0] = timer[0] + elapsed1
        print ("Timer is now  %s seconds" % timer[0])

    if timer is not None: timer[0]= timer[0]+ elapsed1

    F_value = path_costs.vector_path_costs()
    #print F_value
    return np.dot(F_value, d_vector)



