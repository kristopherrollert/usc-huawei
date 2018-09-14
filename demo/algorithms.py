import sys
import numpy as np
from enum import Enum
import multiprocessing as mp

from ortools.graph import pywrapgraph
from sklearn.neighbors import NearestNeighbors

sys.path.insert(0, '../Updated Version')
from objects import *
from generate import *
from functions import *

# Constants
EARTH_RADIUS = 6371 # in kmpip
SOURCE = 0
SINK = 0
driver_offset = 0
order_offset = 0

def alt_multi():
    graph = pywrapgraph.SimpleMinCostFlow()
    all_items = generate_all()
    drivers, driver_dict = all_items["drivers"]
    companies, company_dict = all_items["companies"]
    restaurants, restaurant_dict = all_items["restaurants"]
    orders, order_dict = all_items['orders']

    singleton_edges = [None] * len(drivers)
    single_matches = 0
    double_matches = 0

    deliverable = create_2d_array(len(orders), len(drivers), val=False)
    driver_single_path = {}
    paths = {}
    node_index_to_text = {}

    # Setting constants
    SINK = len(drivers) * 3 + 1
    node_index_to_text[SINK] = 'SINK'
    node_index_to_text[0] = 'SOURCE'
    driver_offset = SINK + 1
    order_offset = driver_offset + (len(orders)*2)

    # 0 = Source, 1 = Sink
    # Set up Drivers
    # -> get driver locaitons in radians
    # -> sets up edges from source to main driver nodes
    driver_locations = []
    for index, driver in enumerate(drivers):

        main_index         = driver_main_node(index)
        single_order_index = driver_single_order_node(index)
        double_order_index = driver_double_order_node(index)

        node_index_to_text[main_index] = 'D*' + str(index + 1)
        node_index_to_text[single_order_index] = 'D' + str(index + 1) + '(1)'
        node_index_to_text[double_order_index] = 'D' + str(index + 1) + '(2)'

        graph.AddArcWithCapacityAndUnitCost(SOURCE, main_index, 2, 0)
        graph.AddArcWithCapacityAndUnitCost(main_index, single_order_index, 1, 100)
        graph.AddArcWithCapacityAndUnitCost(main_index, double_order_index, 2, 10000)

        driver_locations.append(driver.location_in_rad())

    # Set up Orders
    # -> set up edges for main order nodes
    # -> set up edge for secondary order nodes
    company_locations = []
    for index, order in enumerate(orders):
        node_index_to_text[order_main_node(index, driver_offset)] = 'C*' + str(index + 1)
        node_index_to_text[order_single_node(index, driver_offset)] = 'C' + str(index + 1)
        company_locations.append(order.company.location_in_rad())
        main_index = order_main_node(index, driver_offset)
        single_order_index = order_single_node(index, driver_offset)
        graph.AddArcWithCapacityAndUnitCost(single_order_index, main_index, 1, 0)
        graph.AddArcWithCapacityAndUnitCost(main_index, SINK, 1, 0)

    neigh_single = NearestNeighbors(metric="haversine", algorithm="ball_tree")
    neigh_single.fit(driver_locations)

    # Set up edges for single orders
    for o_index, order in enumerate(orders):
        driver_info = [None] * len(drivers)
        shortest_paths = all_paths_single(order.restaurants, order.company, order.deadline)
        for sp_info in shortest_paths:
            order_range = order.deadline - sp_info['distances'][-1]
            if order_range < 0.0: continue
            order_range_rad = deg2rad(order_range * 0.008)
            start_location = sp_info['order'][0].location_in_rad()
            rng = neigh_single.radius_neighbors([start_location], radius=order_range_rad)
            for d_index, distance in zip(rng[1][0], rng[0][0]):
                deliverable[o_index][d_index] = True
                curr_distance = int((distance * EARTH_RADIUS + sp_info['distances'][-1]) * 1000)
                if driver_info[d_index] is None or driver_info[d_index][0] > curr_distance:
                    driver_info[d_index] = (curr_distance, d_index, sp_info, o_index)

        o_graph_index = order_single_node(o_index, driver_offset)
        paths[o_graph_index] = {}

        for d_info in driver_info:
            if d_info is None: continue
            if singleton_edges[d_info[1]] is None:
                singleton_edges[d_info[1]] = [(d_info[3], d_info[0], d_info[2])]
            else:
                singleton_edges[d_info[1]].append((d_info[3], d_info[0], d_info[2]))

            d_graph_index = int(driver_single_order_node(d_info[1]))
            paths[o_graph_index][d_graph_index] = d_info[2]
            graph.AddArcWithCapacityAndUnitCost(d_graph_index, o_graph_index, 1, d_info[0])


    # Setting up edges for double orders
    neigh_company = NearestNeighbors(metric="haversine", algorithm="ball_tree")
    neigh_company.fit(company_locations)
    already_created_extra_order_edges = {}
    combo_orders = create_2d_array(len(orders), len(orders))
    combo_order_index = 0
    driver_double_path = {}

    for o1_index, o1 in enumerate(orders):
        result_queue = mp.Queue()
        processes = []
        order_range_rad = deg2rad(o1.deadline * 0.008)
        rng_company = neigh_company.radius_neighbors([company_locations[o1_index]], radius=order_range_rad, return_distance=False)
        for o2_index in rng_company[0]:
            if o1_index == o2_index: continue
            o2_index = int(o2_index)
            o2 = orders[o2_index]
            processes.append(mp.Process(target=double_comp, args=(o1_index, o2_index, o1, o2, drivers, deliverable, result_queue)))

        for p in processes: p.start()

        while 1:
            running = any(p.is_alive() for p in processes)
            while not result_queue.empty():
                data = result_queue.get()
                o1, o2 = data['orders']
                all_data = data['routes']
                o1_index, o2_index = data['o_indices']
                possible_drivers = data['possible_drivers']
                possible_driver_locations = data['pd_locations']
                curr_combo_order_index = None
                s, e = (o1_index, o2_index) if o1_index < o2_index else (o2_index, o1_index)
                if combo_orders[s][e] is None:
                    node_index_to_text[order_double_node(combo_order_index, order_offset)] = 'C' + str(s + 1) + ',' + str(e + 1)
                    combo_orders[s][e] = combo_order_index
                    curr_combo_order_index = combo_order_index
                    already_created_extra_order_edges[curr_combo_order_index] = False
                    combo_order_index += 1
                else:
                    curr_combo_order_index = combo_orders[s][e]

                neigh_drivers = NearestNeighbors(metric="haversine", algorithm="ball_tree")
                end_node = order_double_node(curr_combo_order_index, order_offset)

                if not end_node in paths.keys():
                    paths[end_node] = {}

                if len(possible_driver_locations) != 0:
                    neigh_drivers.fit(possible_driver_locations)
                    driver_path_info = [None] * len(drivers)
                    for path in all_data:
                        o1_fin = path['distances'][path['order'].index(o1.company)]
                        o2_fin = path['distances'][path['order'].index(o2.company)]
                        driver_range = min(o1.deadline - o1_fin, o2.deadline - o2_fin)
                        if driver_range < 0.0: continue
                        driver_range_rad = deg2rad(driver_range * 0.008)
                        rng_drivers = neigh_drivers.radius_neighbors([path['order'][0].location_in_rad()], radius=driver_range_rad)
                        for d_index, d_distance in zip(rng_drivers[1][0], rng_drivers[0][0]):
                            total_cost = int(((d_distance * EARTH_RADIUS + path['distances'][-1]) * 1000) / 2)
                            if driver_path_info[d_index] is None or driver_path_info[d_index][0] > total_cost:
                                driver_path_info[d_index] = (total_cost, path)

                    for data_index in range(len(driver_path_info)):
                        if driver_path_info[data_index] is None: continue
                        distance, path = driver_path_info[data_index]
                        id = str(o1_index + 1) + ',' + str(o2_index + 1)
                        start_node = driver_double_order_node(data_index)
                        paths[end_node][start_node] = path

                        if not already_created_extra_order_edges[curr_combo_order_index]:
                            already_created_extra_order_edges[curr_combo_order_index] = True
                            generate_extra_order_edges(graph, curr_combo_order_index, o1_index, o2_index, driver_offset, order_offset, node_index_to_text)
                        graph.AddArcWithCapacityAndUnitCost(start_node, end_node, 2, distance)

            if not running:
                break

    node_supplies = min(len(drivers) * 2, len(orders))
    graph.SetNodeSupply(0, node_supplies)
    graph.SetNodeSupply(SINK, -node_supplies)


    arcs_to_head = {}
    arcs_from_tail = {}
    flow_in = {}
    main_driver_arcs = []

    if graph.SolveMaxFlowWithMinCost() == graph.OPTIMAL:
        for arc in range(graph.NumArcs()):
            head = node_index_to_text[graph.Head(arc)]
            tail = node_index_to_text[graph.Tail(arc)]
            temp_arc = Arc(tail, head, graph.Flow(arc), graph.Capacity(arc), graph.UnitCost(arc))

            if graph.UnitCost(arc) > 0:
                try: temp_arc.set_path(paths[graph.Head(arc)][graph.Tail(arc)])
                except KeyError: pass

            if head in arcs_to_head: arcs_to_head[head].append(temp_arc)
            else: arcs_to_head[head] = [temp_arc]

            if tail in arcs_from_tail: arcs_from_tail[tail].append(temp_arc)
            else: arcs_from_tail[tail] = [temp_arc]

            if head in flow_in: flow_in[head] += graph.Flow(arc)
            else: flow_in[head] = graph.Flow(arc)

            if graph.Tail(arc) == SOURCE:
                main_driver_arcs.append(temp_arc)

    # Post graph computations
    driver_assignment = [None] * (len(drivers) + 1)
    order_assignment = [None] * (len(orders) + 1)
    num_matches = 0.0
    total_distance = 0
    for main_driver_arc in main_driver_arcs:
        if main_driver_arc.flow == 0:
            continue

        seconday_driver_arcs = arcs_from_tail[main_driver_arc.head]
        single_order_driver_arc, double_order_driver_arc = None, None
        for arc in seconday_driver_arcs:
            if arc.flow == 0: continue
            if arc.max_flow == 1: single_order_driver_arc = arc
            else: double_order_driver_arc = arc

        if double_order_driver_arc:
            found_assignment = False
            possible_arcs = list(filter(lambda x: x.flow != 0, arcs_from_tail[double_order_driver_arc.head]))
            possible_singleton = None
            for possible_arc in possible_arcs:
                o1_index, o2_index = map(lambda x: int(x), possible_arc.head[1:].split(','))
                if order_assignment[o1_index] is None and order_assignment[o2_index] is None:
                    driver_index = int(main_driver_arc.head[2:])
                    order_assignment[o1_index] = main_driver_arc.head
                    order_assignment[o2_index] = main_driver_arc.head
                    id = str(o1_index) + ',' + str(o2_index)
                    driver_assignment[driver_index] = [possible_arc.head, (possible_arc.cost * 2) / 1000.0, possible_arc.get_path()]
                    found_assignment = True
                    total_distance += 2 * possible_arc.cost
                    double_matches += 1
                    num_matches += 2.0
                    break
                elif order_assignment[o1_index] is None:
                    possible_singleton = o1_index
                elif order_assignment[o2_index] is None:
                    possible_singleton = o2_index

            if found_assignment: continue
            elif possible_singleton:
                driver_index = int(main_driver_arc.head[2:])
                order_assignment[possible_singleton] = main_driver_arc.head
                singleton_id = 'C' + str(possible_singleton)
                driver_single_order_id = 'D' + str(driver_index) + '(1)'
                for arc in arcs_from_tail[driver_single_order_id]:
                    if arc.head == singleton_id:
                        total_distance += arc.cost
                        driver_assignment[driver_index] = [singleton_id, arc.cost/ 1000.0, arc.get_path()]
                        single_matches += 1
                        num_matches += 1.0
                        break


        if single_order_driver_arc:
            arc = list(filter(lambda x: x.flow != 0, arcs_from_tail[single_order_driver_arc.head]))[0]
            o_index = int(arc.head[1:])
            if order_assignment[o_index] is None:
                driver_index = int(main_driver_arc.head[2:])
                order_assignment[o_index] = main_driver_arc.head
                driver_assignment[driver_index] = [arc.head, arc.cost / 1000.0, arc.get_path()]
                total_distance += arc.cost
                single_matches += 1
                num_matches += 1.0

    bonus_graph = pywrapgraph.SimpleMinCostFlow()
    bonus_source = 0
    bonus_sink = len(drivers) + len(orders) + 1
    second_num_matches = 0
    bonus_paths = {}

    unmatched_orders = 0
    for o_num, info in enumerate(order_assignment[1:]):
        if info is None:
            unmatched_orders += 1
            bonus_paths[o_num + len(drivers) + 1] = {}
            bonus_graph.AddArcWithCapacityAndUnitCost(o_num + len(drivers) + 1, bonus_sink, 1, 0)

    unmatched_drivers = 0
    for d_num, info in enumerate(driver_assignment[1:]):
        if info is None:
            if singleton_edges[d_num] is None: continue
            bonus_graph.AddArcWithCapacityAndUnitCost(bonus_source, d_num + 1, 1, 0)
            unmatched_drivers += 1
            for edge_data in singleton_edges[d_num]:
                start_node, distance, path = edge_data
                if order_assignment[start_node + 1] is None:
                    bonus_paths[start_node + len(drivers) + 1][d_num + 1] = path
                    bonus_graph.AddArcWithCapacityAndUnitCost(d_num + 1, start_node + len(drivers) + 1, 1, distance)

    bonus_supplies = min(unmatched_orders, unmatched_drivers)
    if bonus_supplies > 0:
        bonus_graph.SetNodeSupply(0, bonus_supplies)
        bonus_graph.SetNodeSupply(bonus_sink, -bonus_supplies)
        if bonus_graph.SolveMaxFlowWithMinCost() == bonus_graph.OPTIMAL:
            for arc in range(bonus_graph.NumArcs()):
                if bonus_graph.Flow(arc) > 0:
                    head = bonus_graph.Head(arc)
                    tail = bonus_graph.Tail(arc)
                    if head == bonus_sink or tail == bonus_source: continue
                    path = bonus_paths[head][tail]
                    driver_assignment[tail] = ['C' + str(head - len(drivers)), bonus_graph.UnitCost(arc) / 1000.0, path]
                    second_num_matches += 1
                    total_distance += bonus_graph.UnitCost(arc)

    percent_matched = 0 if len(orders) == 0 else ((num_matches + second_num_matches) / len(orders) * 100)
    return {
    'total_distance' : total_distance,
    'percent_matched': percent_matched,
    'matches': driver_assignment}

def double_comp(o1_index, o2_index, o1, o2, drivers, deliverable, queue):
    possible_drivers, possible_driver_locations = [], []
    for d_index, driver in enumerate(drivers):
        if deliverable[o1_index][d_index] and deliverable[o2_index][d_index]:
            possible_drivers.append(driver)
            possible_driver_locations.append(driver.location_in_rad())

    if len(possible_drivers) != 0:
        all_data = all_paths_double(o1.restaurants, o1.company, o1.deadline, o2.restaurants, o2.company, o2.deadline)
        queue.put({
            'routes' : all_data,
            'possible_drivers' : possible_drivers,
            'pd_locations' : possible_driver_locations,
            'orders' : (o1, o2),
            'o_indices' : (o1_index, o2_index)
            })

def optimal_solution():
    min_cost_flow = pywrapgraph.SimpleMinCostFlow()
    all_items = generate_all()
    drivers, driver_dict = all_items["drivers"]
    companies, company_dict = all_items["companies"]
    restaurants, restaurant_dict = all_items["restaurants"]
    orders, order_dict = all_items['orders']
    drivers_path = {}
    order_len = len(orders)

    # generate arcs from source node (0) to company users (company_inc)
    # sets the cost to 0 and the capacity to 1
    user_increment = 1
    for x in range(order_len):
        min_cost_flow.AddArcWithCapacityAndUnitCost(0, user_increment, 1, 0)
        user_increment += 1

    # generate arcs from male users (male_inc) to
    # sets the cost to 0 and the capacity to 1
    # the loops also generates array for driver locations for later
    driver_locations = []
    sink_index = len(companies) + len(drivers) + 1
    for driver in drivers:
        driver_locations.append(driver.location_in_rad())
        min_cost_flow.AddArcWithCapacityAndUnitCost(user_increment, sink_index, 1, 0)
        user_increment += 1

    # goes through every company and generates the shortest path between that companies'
    # resturants. Get the shortest path starting at each restaurant, we use a near
    # neighbor search to determine which drivers are in range. After finding all drivers
    # in range, it only adds an edge for the shortest total distance for each driver.
    neigh = NearestNeighbors(metric="haversine", algorithm="ball_tree")
    neigh.fit(driver_locations)

    for order in orders:
        driver_info = [None] * len(drivers)
        order_index = orders.index(order) + 1
        drivers_path[order_index] = {}
        shortest_paths_info = get_shortest_restaurant_paths(order.restaurants, order.company)

        for sp_info in shortest_paths_info:
            order_range = order.deadline - sp_info['distance']
            if order_range < 0.0: continue
            order_range_rad = deg2rad(order_range * 0.008)
            start_location = sp_info['order'][0].location_in_rad()
            rng = neigh.radius_neighbors([start_location], radius=order_range_rad)
            indices = np.asarray(rng[1][0])
            distances = np.asarray(rng[0][0])

            for index in range(len(indices)):
                real_index = indices[index]
                driver_index = index + order_len + 1
                distance = int((distances[index] * EARTH_RADIUS + sp_info['distance'])* 1000)
                if driver_info[real_index] is None or driver_info[real_index][0] > distance:
                    driver_info[real_index] = (distance, driver_index, sp_info)

        for d_info in driver_info:
            if d_info is None: continue
            drivers_path[order_index][d_info[1]] = d_info[2]
            min_cost_flow.AddArcWithCapacityAndUnitCost(order_index, d_info[1], 1, d_info[0])

    # get the length of the limiting value, men or women. Set that to the supplies
    node_supplies = min(len(drivers), order_len)
    supplies = [node_supplies] + ([0] * (order_len + len(drivers))) + [(-1) * node_supplies]
    for i in range(len(supplies)):
        min_cost_flow.SetNodeSupply(i, supplies[i])

    # calculate the max flow with min cost and save information about matches
    driver_assignment = [None] * (len(drivers) + 1)
    successful_matches = 0.0
    if min_cost_flow.SolveMaxFlowWithMinCost() == min_cost_flow.OPTIMAL:
        for arc in range(min_cost_flow.NumArcs()):
            if min_cost_flow.Tail(arc) != 0 and min_cost_flow.Head(arc) != sink_index:
                if min_cost_flow.Flow(arc) > 0:
                    successful_matches += 1.0
                    tail = min_cost_flow.Tail(arc)
                    head = min_cost_flow.Head(arc)
                    cost = min_cost_flow.UnitCost(arc) / 1000.0
                    name = 'C' + str(tail)
                    driver_assignment[head - order_len] = [name, cost, drivers_path[tail][head]]

    driver_distance = int(min_cost_flow.OptimalCost())
    percent_matched = 0 if order_len == 0 else (successful_matches / order_len * 100)
    return {
        'total_distance' : driver_distance,
        'percent_matched' : percent_matched,
        'matches': driver_assignment
    }
