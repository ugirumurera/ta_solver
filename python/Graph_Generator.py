from igraph import *
from xml.etree.ElementTree import Element
import xml.etree.ElementTree as etree
import csv
import itertools
import random
from xml.dom import minidom
import StringIO
import random
import inspect
import timeit
import numpy as np
import random
from igraph import plot


def csv2string(data):
    si = StringIO.StringIO()
    cw = csv.writer(si)
    cw.writerow(data)
    return si.getvalue().strip('\r\n')

#Function used to determine all paths between ods
# def find_all_paths(graph, start, end):
#     def find_all_paths_aux(adjlist, start, end, path):
#         path = path + [start]
#         if start == end:
#             return [path]
#         paths = []
#         for node in adjlist[start] - set(path):
#             paths.extend(find_all_paths_aux(adjlist, node, end, path))
#         return paths
#
#     adjlist = [set(graph.nimport matplotlib.pyplot as plteighbors(node)) for node in xrange(graph.vcount())]
#     return find_all_paths_aux(adjlist, start, end, [])

# Function that determines all paths between ods that have lengh les or equal to given maxlengh
def find_all_paths_len(graph, start, end, mode = 'OUT', maxlen = None):
    def find_all_paths_aux(adjlist, start, end, path, maxlen = None):
        path = path + [start]
        if start == end:
            return [path]
        paths = []
        if maxlen is None or len(path) <= maxlen:
            for node in adjlist[start] - set(path):
                paths.extend(find_all_paths_aux(adjlist, node, end, path, maxlen))
        return paths
    adjlist = [set(graph.neighbors(node, mode = mode)) \
        for node in xrange(graph.vcount())]
    all_paths = []
    start = start if type(start) is list else [start]
    end = end if type(end) is list else [end]
    for s in start:
        for e in end:
            all_paths.extend(find_all_paths_aux(adjlist, s, e, [], maxlen))
    return all_paths

#Change path representation from node list to link ids list
def translate_paths(g, paths):
    new_paths = []
    for p in paths:
        trans_path = []
        for i in range(len(p)-1):
            source_list = [p[i]]
            end_list = [p[i+1]]
            link_id = g.es.select(_between = (source_list,end_list))
            for e in link_id:
                if e.source == p[i] and e.target == p[i+1]:
                    trans_path.append(e.index)

        new_paths.append(trans_path)
    return new_paths

def generate_graph_and_paths(graph_size, scaling, num_nodes, num_ods, max_length, paths_per_od):

    graph = Graph.Lattice([graph_size, graph_size], circular=False, directed = True)

    # Generate od pairs
    # For Beats purposes, the origins to be of outdegree 1 and the sinks have to be of outdegree 1
    graph.vs["indegree"] = graph.indegree()
    graph.vs["outdegree"] = graph.outdegree()

    origins = np.zeros(num_ods, dtype=int)
    destinations = np.zeros(num_ods, dtype=int)

    odpairs = random.sample(list(itertools.permutations(range(graph.vcount()), 2)), num_ods)

    #Adding source node and outgoing link to od
    seen_o = {}   # Keeps track of seen origins so we do not put mutiple source link on the same node
    seen_d = {}   # Keeps track of seen destination to avoid multiple sink links
    j = len(graph.vs)   # Starting index of new nodes
    k = 0
    #for i in range(len(origins)):
    for o in odpairs:
        # add a new node and edge to graph for origin
        if o[0] not in seen_o.keys():
            graph.add_vertices(1)
            graph.add_edge(j, o[0])
            seen_o[o[0]] = int(j)
            j += 1

        origins[k] = seen_o[o[0]]

        if o[1] not in seen_d.keys():
            # add a new node and edge to the graph for destination
            graph.add_vertices(1)
            graph.add_edge(o[1], j)
            seen_d[o[1]] = j
            j += 1

        destinations[k] = seen_d[o[1]]

        k += 1

    print "Finished Adding All ods, now getting node coordinates with layout"
    #random.shuffle(pairs)   # shuffles the od pairs to allow for variability
    #ods = zip(origins,destinations)

    # Get node ids and positions
    layout = graph.layout("kk")     # This fixes the coordinates of the nodes
    layout.scale(scaling)

    coordinates = layout.coords    # Coordinates of the nodes
    graph.vs["Coordinates"] = coordinates
    graph.vs["indices"] = graph.vs.indices
    #graph.vs["label"] = graph.vs["indices"]
    print(graph.ecount()) #printing the number of edges
    plot(graph, layout=layout)


    print "Moving to getting paths for all ods"
    # Generate the paths between the od pairs
    all_paths = {}
    for j in range(len(odpairs)):
        #Find all paths between origin and destination that have at most max_length edges
        #start_time1 = timeit.default_timer()
        # Each iteration the weight of the shortest path is multiplied by power to allow to
        # find a new shortest path
        # Add edge weights to graph, we start will all edges with weight 1
        graph.es["weight"] = np.ones(graph.ecount())
        factor = 10
        paths = []

        print "Finding paths for od ", origins[j], " and dest ", destinations[j]

        for i in range(paths_per_od):
            #Returns a list of edges going from origin[j] to destination[j]
            path = graph.get_shortest_paths(origins[j], destinations[j], weights="weight", mode=OUT, output="epath")

            added = False
            k = 0
            while(~added and k < len(path)):
                if path[k] not in paths:
                    paths.append(path[k])
                    added = True
                    #change weight of edges in path in order to find new shortest path
                    size_of_path = len(path[0])
                    new_weights = np.multiply(factor**(i+1),np.ones(size_of_path))
                    graph.es[path[0]]["weight"] = new_weights
                k +=1

        all_paths[(origins[j],destinations[j])] = paths

    return graph, all_paths

# write the scenario to csv files
def write_to_csv(graph, all_paths):

    # Print vertices and their coordinates
    f = open('node_info.csv', 'wb')
    writer = csv.writer(f)
    node_info_title = ["Node id", "x coord", "y coord"]
    writer.writerow(node_info_title)
    for v in graph.vs:
        row = [v.index,v["Coordinates"][0],v["Coordinates"][1]]
        writer.writerow(row)

    # Get edge list
    f = open('edge_info.csv', 'wb')
    writer = csv.writer(f)
    edge_info_title = ["Link id", "source node", "end node"]
    writer.writerow(edge_info_title)
    for e in graph.es:
        row = [e.index,e.source, e.target]
        writer.writerow(row)

    # Write paths
    f = open('paths_info.csv', 'wb')
    writer = csv.writer(f)
    for o, path in all_paths.iteritems():
        writer.writerows(path)

# create scenario xml
def create_xml(graph,all_paths):

    xscenario = Element('scenario')
    xscenario.set('xmlns', "opentrafficmodels")

    # # Adding model
    # xmodels = Element('models')
    # xmodel = Element('model')
    # xmodel.set('type', "ctm")
    # xmodel.set('name', "myctm")
    # xmodel.set('is_default', "true")
    #
    # xmodel_param = Element('model_params')
    # xmodel_param.set('sim_dt', "2")
    # xmodel_param.set('max_cell_length', "100")
    # # Addition model and model_params to models element
    # xmodel.append(xmodel_param)
    # xmodels.append(xmodel)

    # xscenario.append(xmodels)


    # network ---------------------
    xnetwork = Element('network')
    xscenario.append(xnetwork)

    # nodes ........................
    xnodes = Element('nodes')
    xnetwork.append(xnodes)
    for v in graph.vs:
        xnode = Element('node')
        xnodes.append(xnode)
        xnode.set('id', str(v.index))
        xnode.set('x', str(v["Coordinates"][0]))
        xnode.set('y', str(v["Coordinates"][1]))

    # links .........................
    xlinks = Element('links')
    xnetwork.append(xlinks)
    link_ids = []
    for e in graph.es:
        xlink = Element('link')
        link_ids.append(e.index)
        xlinks.append(xlink)
        xlink.set('id', str(e.index))
        xlink.set('length', str(200))   # length in meters --- FIX THIS
        xlink.set('full_lanes', str(1)) # number of lanes --- FIX THIS
        xlink.set('start_node_id', str(e.source))
        xlink.set('end_node_id', str(e.target))
        xlink.set('roadparam', "0" )

    # road params .......................
    xroadparams = Element('roadparams')
    xnetwork.append(xroadparams)
    xroadparam = Element('roadparam')
    xroadparams.append(xroadparam)
    xroadparam.set('id', "0")
    xroadparam.set('name', "Standard link")
    xroadparam.set('capacity', "2000" )     # veh/hr/lane
    xroadparam.set('speed', "60" )          # km/hr
    xroadparam.set('jam_density', "100" )   # veh/km/lane

    # road connections .......................

    # add only the road connections needed for the paths
    # create a map from node id to road connections in that node
    road_connection_map = {}
    for od, paths in all_paths.iteritems():
        for path in paths:
            for i in range(len(path)-1):
                up_link = graph.es[path[i]]
                dn_link = graph.es[path[i+1]]

                if up_link.target != dn_link.source:
                    print 'ERROR!!!!!', up_link.target, dn_link.source

                node_id = up_link.target
                if node_id in road_connection_map:

                    # ignore if it is already present
                    if 0==len([item for item in road_connection_map[node_id] if (item[0] == path[i] and item[1] == path[i+1])]):
                        road_connection_map[node_id].append((path[i], path[i+1]))
                else:
                    road_connection_map[node_id] = [(path[i], path[i+1])]

    # road connections to xml
    xroadconnections = Element('roadconnections')
    xnetwork.append(xroadconnections)
    c = -1
    for node_id, tuple_list in road_connection_map.iteritems():
        for in_out_link in tuple_list:
            c += 1
            xrc = Element('roadconnection')
            xroadconnections.append(xrc)
            xrc.set('id',str(c))
            xrc.set('in_link',str(in_out_link[0]))
            xrc.set('out_link',str(in_out_link[1]))
            xrc.set('in_link_lanes',"1#1")
            xrc.set('out_link_lanes',"1#1")

    # # MN model --------------------
    # xmodel = Element('model')
    # xscenario.append(xmodel)
    # xmn = Element('mn')
    # xmodel.append(xmn)
    # xmn.set('max_cell_length', '100')  # m
    # xmn.text = csv2string(link_ids)

    # CTM model
    xmodels = Element('models')
    xscenario.append(xmodels)
    xmodel = Element('model')
    xmodels.append(xmodel)
    xmodel.set('type', 'ctm')  # m
    xmodel.set('name', 'myctm')
    xmodel.set('is_default', 'true')
    xmodel_param = Element('model_params')
    xmodel.append(xmodel_param)
    xmodel_param.set('sim_dt', '2')
    xmodel_param.set('max_cell_length', '100')


    # paths ---------------------
    xsubnetworks = Element('subnetworks')
    xscenario.append(xsubnetworks)
    c = -1
    path_ids = []
    for od, paths in all_paths.iteritems():
        for path in paths:
            c += 1
            path_ids.append(c+1)
            xsubnetwork = Element('subnetwork')
            xsubnetworks.append(xsubnetwork)
            xsubnetwork.set('id',str(path_ids[c]))
            xsubnetwork.text = csv2string(path)

    # demands ---------------------
    xdemands = Element('demands')
    xscenario.append(xdemands)
    for path_id in path_ids:
        xdemand = Element('demand')
        xdemands.append(xdemand)
        xdemand.set('commodity_id',"0")
        xdemand.set('subnetwork',str(path_id))
        xdemand.set('start_time',"0")
        xdemand.set('dt',"600")
        xdemand.text = "100"

    # commodities ---------------------
    xcommodities = Element('commodities')
    xscenario.append(xcommodities)
    xcommodity = Element('commodity')
    xcommodities.append(xcommodity)
    xcommodity.set('id','0')
    xcommodity.set('pathfull','true')
    xcommodity.set('name','car')
    xcommodity.set('subnetworks',csv2string(path_ids))

    return xscenario

def main():

    # user definitions
    graph_size = 50 # grid size, leads to a grid of graph_size*graph_size nodes
    scaling = 100 # number used to scale the resulting grid graph
    max_length =25  # Maximum number of nodes in paths returned
    paths_per_od = 5    # Number of paths saved per OD

    num_nodes = graph_size*graph_size   # Number of nodes in the graph
    num_ods = int(num_nodes)   # Number of od, have to be less that 1/2 number of nodes

    graph, all_paths = generate_graph_and_paths(graph_size, scaling, num_nodes, num_ods, max_length, paths_per_od)

    print "Now writing to xml file"
    # write_to_csv(graph,all_paths)

    signalized_nodes = graph.vs.select(indegree_ge=4).indices

    xscenario = create_xml(graph,all_paths)

    # BELOW IS CODE GABRIEL WAS PUTTING TOGETHER TO CREATE SIGNALS
    #
    # all_nodes = xscenario.find('network').find('nodes')
    # road_connections = xscenario.find('network').find('roadconnections')
    #
    # rc_in = [int(child.get('in_link')) for child in road_connections._children]
    # rc_out = [int(child.get('out_link')) for child in road_connections._children]
    #
    # # node_in = map from node id to all in links
    # # node_out = map from node_id to all out links
    #
    # # create the actuators
    # xactuators = Element('actuators')
    # xscenario.append(xactuators)
    # for node_id in signalized_nodes:
    #
    #     xactuator = Element('actuator')
    #     xactuators.append(xactuator)
    #     xactuator.set('id',node_id)
    #     xactuator.set('type','signal')
    #
    #     xsignal = Element('signal')
    #     xactuator.append(xsignal)
    #
    #     # find this node in the graph
    #     # in_links_1 = graph.es.select(_source=node_id)
    #     in_links = graph.incident(node_id, mode="out")
    #
    #     # traverse its incoming links
    #     phase_id = 0
    #     for in_link in in_links:
    #
    #         rcs = []
    #         # for each link, find the associated road connections
    #         #     rcs.add(rc_out.get(in_link))
    #
    #         # attach a phase to the road connections
    #         phase_id += 1
    #
    #         xphase = Element('phase')
    #         xsignal.append(xphase)
    #         xphase.set('id',phase_id)
    #         xphase.set('roadconnection_ids',rcs)
    #         xphase.set('yellow_time',3)
    #         xphase.set('red_clear_time',2)
    #         xphase.set('min_green_time',5)
    #
    #     # create a controller
    #     xcontroller = Element('controller')
    #     xcontrollers.append(xcontroller)
    #     xcontroller.set('id',xxx)
    #     xcontroller.set('type','sig_pretimed')
    #
    #     xtarget = Element('target_actuators')
    #     xcontroller.append(xtarget)
    #     xtarget.set('ids',xxx)
    #
    #     xschedule = Element('schedule')
    #     xcontroller.append(xschedule)
    #
    #     xscheduleitem = Element('schedule_item')
    #     xschedule.append(xscheduleitem)
    #     xscheduleitem.set('start_time','20')
    #     xscheduleitem.set('cycle','120')
    #     xscheduleitem.set('offset','20')
    #
    #     xstages = Element('stages')
    #     xscheduleitem.append(xstages)
    #
    #     for xxx in xxx:
    #         xstage = Element('stage')
    #         xstages.append(xstage)
    #         xstage.set('order','1')
    #         xstage.set('phases','1,5')
    #         xstage.set('duration','30')


    # write to file ---------------------
    this_folder = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    name = 'scenario_'+str(graph_size * graph_size) + '_nodes.xml'
    print("Saving to xml: ", name)
    configfile = os.path.join(this_folder, os.path.pardir, 'configfiles', name)
    with open(configfile, 'w') as f:
        f.write(minidom.parseString(etree.tostring(xscenario)).toprettyxml(indent="\t"))

    # Plot the resulting graph
    # graph.vs["ID"] = graph.vs.indices
    # graph.vs["label"] = graph.vs["ID"]      # We label the nodes by the ID
    # plot(graph, layout = layout)            # Plotting the graph

if __name__ == "__main__": main()