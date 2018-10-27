'''
>>> DEVELOPED BY KRISTOPHER ROLLERT
>>> UPDATED: 08.07.18

'''

'''             <<<<<<<<<<<   LIBRARIES   >>>>>>>>>>>           '''
import sys
import numpy as np
from objects import *
from generate import *
from functions import *

from ortools.graph import pywrapgraph
from sklearn.neighbors import NearestNeighbors

'''         <<<<<<<<<<<           CONSTANTS       >>>>>>>>>>>        '''

EARTH_RADIUS = 6371 # in km

'''         <<<<<<<<<<<   OPTIMAL SOLUTION CODE   >>>>>>>>>>>        '''


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
    final_matches = [None] * order_len
    successful_matches = 0.0
    if min_cost_flow.SolveMaxFlowWithMinCost() == min_cost_flow.OPTIMAL:
        for arc in range(min_cost_flow.NumArcs()):
            if min_cost_flow.Tail(arc) != 0 and min_cost_flow.Head(arc) != sink_index:
                if min_cost_flow.Flow(arc) > 0:
                    successful_matches += 1.0
                    tail = min_cost_flow.Tail(arc)
                    head = min_cost_flow.Head(arc)
                    orders[tail - 1].set_shortest_path(drivers_path[tail][head])
                    final_matches[min_cost_flow.Tail(arc) - 1] = (
                        head - order_len,
                        min_cost_flow.UnitCost(arc) / 1000.0)

    # print results
    driver_distance = int(min_cost_flow.OptimalCost())
    percent_matched = 0 if order_len == 0 else (successful_matches / order_len * 100)
    # print_data(final_matches, orders, percent_matched, driver_distance)
    # print(int(successful_matches), 0, int(successful_matches), 0)
    # return (int(successful_matches), 0, int(successful_matches), 0)
    return final_matches

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            o_num = int(sys.argv[1])
            c_num = int(sys.argv[2])
            d_num = int(sys.argv[3])
            generate_new_test_data(c_num, d_num, o_num)
            optimal_solution()
        except:
            print('python alt.py <num orders> <num companies> <num drivers>')
    else:
        print(optimal_solution())
