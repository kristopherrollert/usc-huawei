import math
import itertools
from objects import *
'''             <<<<<<<<<<<   GENERAL FUNCIIONS   >>>>>>>>>>>           '''
def create_2d_array(len1, len2, val=None):
    a = []
    for i in range(len1):
        a.append([val] * len2)
    return a


def get_distance_from_dict(computed_distances, place1, place2):
    try:
        return computed_distances[place1.get_name() + '->' + place2.get_name()]
    except KeyError:
        distance = dist(place1, place2)
        computed_distances[place1.get_name() + '->' + place2.get_name()] = distance
        computed_distances[place2.get_name() + '->' + place1.get_name()] = distance
        return distance

# returns all shortest paths going through all restaurants and companies, but ensures
# that all restaurants are delivered before their companies and company1 is delivered
# before company 2
def all_paths_double(rests1, c1, dl1, rests2, c2, dl2):
    all_rests = rests1 + rests2
    info = []
    computed_distances = {}
    for index in range(len(all_rests)):
        new_o1_to_do, new_o2_to_do = get_updated_to_dos(index, rests1, rests2)
        temp_info = all_paths_double_rec([all_rests[index]], new_o1_to_do, c1, dl1, new_o2_to_do, c2, dl2, [0], computed_distances)
        minfo = None
        for path in temp_info:
            if path is None: continue
            if not minfo or minfo['distances'][-1] > path['distances'][-1]: minfo = path
        if minfo: info += [minfo]
    return info

def all_paths_double_rec(done, o1_to_do, c1, dl1, o2_to_do, end, dl2, distances, computed_distances):
    if not o1_to_do and c1:
        return all_paths_double_rec(done, [c1], None, dl1, o2_to_do, end, dl2, distances, computed_distances)
    elif dl2 < 0: return [None]
    elif dl1 < 0 and o1_to_do: return [None]
    elif not o1_to_do and not o2_to_do:
        distances += [distances[-1] + dist(done[-1], end)]
        done +=  [end]
        return [{"distances" : distances, "order" : done}]
    else:
        data = []
        previous_point = done[-1]
        previous_distance = distances[-1]
        all_to_do = o1_to_do + o2_to_do
        for index in range(len(all_to_do)):
            new_done = done + [all_to_do[index]]
            new_dist = get_distance_from_dict(computed_distances, previous_point, all_to_do[index])
            new_o1_to_do, new_o2_to_do = get_updated_to_dos(index, o1_to_do, o2_to_do)
            new_dl1, new_dl2 = (dl1 - new_dist, dl2 - new_dist)
            new_distances = distances + [previous_distance + new_dist]
            data += all_paths_double_rec(new_done, new_o1_to_do, c1, new_dl1, new_o2_to_do, end, new_dl2, new_distances, computed_distances)
        return data

# returns all shortest resturant paths. Every path has the total distance and
# the order of the elements
def all_paths_single(restaurants, company, deadline):
    info = []
    for index in range(len(restaurants)):
        new_to_do = restaurants[:index] + restaurants[index + 1:]
        temp_info = all_paths_single_rec([restaurants[index]], new_to_do, company, deadline, [0])
        minfo = None
        for path in temp_info:
            if path is None: continue
            if not minfo or minfo['distances'][-1] > path['distances'][-1]: minfo = path
        if minfo: info += [minfo]
    return info

def all_paths_single_rec(done, to_do, company, deadline, distances):
    if deadline < 0: return [None]
    elif not to_do and company:
        return all_paths_single_rec(done, [company], None, deadline, distances)
    elif not to_do: return [{'distances' : distances, 'order': done}]
    else:
        data = []
        previous_point = done[-1]
        previous_distance = distances[-1]
        for index in range(len(to_do)):
            new_done = done + [to_do[index]]
            new_dist = dist(previous_point, to_do[index])
            new_to_do = to_do[:index] + to_do[index + 1:]
            new_dl = deadline - new_dist
            new_distances = distances + [previous_distance + new_dist]
            data += all_paths_single_rec(new_done, new_to_do, company, new_dl, new_distances)
        return data


def get_shortest_path_all_restaurants(to_do):
    data = []
    for index in range(len(to_do)):
        rest = to_do[index]
        new_to_do = to_do[:index] + to_do[index + 1:]
        data += get_sp_all_rests_rec([rest], new_to_do, [0])
    return data

def get_sp_all_rests_rec(done, to_do, distances):
    # print(distances)
    if not to_do:
        return [{"distances" : distances, "order" : done}]
    else:
        new_data = []
        previous_point = done[-1]
        previous_distance = distances[-1]
        for index in range(len(to_do)):
            new_done = done + [to_do[index]]
            new_dist = distances + [previous_distance + dist(previous_point, to_do[index])]
            new_to_do = to_do[:index] + to_do[index + 1:]
            temp_info = get_sp_all_rests_rec(new_done, new_to_do, new_dist)
            new_data += temp_info
        return new_data

# problem in traveling salesman
def get_all_shortest_combo_paths(o1_to_do, o2_to_do, comp1, comp2):
    all_rests = o1_to_do + o2_to_do
    info = [{"distance" : 0, "order" : []}] * len(all_rests)
    for index in range(len(all_rests)):
        new_o1_to_do, new_o2_to_do = get_updated_to_dos(index, o1_to_do, o2_to_do)
        info[index] = get_shortest_combo_paths([all_rests[index]], new_o1_to_do, new_o2_to_do, comp1, comp2, 0, 0, 0)
    return info

# if o1_to_do is empty and company is not None, then move company to o1_to_do
# WHEN AN ELEMENT IS ADDED TO DONE, MAKE SURE IT IS AT THE END
def get_shortest_combo_paths(done, o1_to_do, o2_to_do, comp1, comp2, total_dist, c1_dist, c2_dist):
    if   not o1_to_do and comp1:
        return get_shortest_combo_paths(done, [comp1], o2_to_do, None, comp2, total_dist, c1_dist, c2_dist)
    elif not o2_to_do and comp2l:
        return get_shortest_combo_paths(done, o1_to_do, [comp2], comp1, None, total_dist, c1_dist, c2_dist)
    elif not o1_to_do and not o2_to_do:
        return {'order' : done, 'company1_distance' :  c1_dist, 'company2_distance' : c2_dist, 'total_distance': total_dist}
    else: # minfo = min_info
        all_to_do = o1_to_do + o2_to_do
        previous_point = done[-1]
        minfo = None
        for index in range(len(all_to_do)):
            new_done = done + [all_to_do[index]]
            new_dist = total_dist + dist(all_to_do[index], previous_point)
            if type(all_to_do[index]) is Company:
                if not comp1: c1_dist = new_dist
                else: c2_dist = new_dist
            new_o1_to_do, new_o2_to_do = get_updated_to_dos(index, o1_to_do, o2_to_do)
            temp_info = get_shortest_combo_paths(new_done, new_o1_to_do, new_o2_to_do, comp1, comp2, new_dist, c1_dist, c2_dist)
            if not minfo or temp_info['total_distance'] < minfo['total_distance']: minfo = temp_info
        return minfo


def get_updated_to_dos(index, o1_to_do, o2_to_do):
    if index < len(o1_to_do):
        o1_to_do = o1_to_do[:index] + o1_to_do[index + 1:]
    else:
        alt_index = index - len(o1_to_do)
        o2_to_do = o2_to_do[:alt_index] + o2_to_do[alt_index + 1:]
    return o1_to_do, o2_to_do

# returns all shortest resturant paths. Every path has the total distance and
# the order of the elements
def get_shortest_restaurant_paths(restaurants, company):
    info = [{"distance" : 0, "order" : []}] * len(restaurants)
    for index in range(len(restaurants)):
        new_to_do = restaurants[:index] + restaurants[index + 1:]
        info[index] = get_shortest_path([restaurants[index]], new_to_do, company, 0)
    return info

# returns the shortest resturant path. The path has the total distance and
# the order of the elements
def get_shortest_restaurant_path(restaurants, company):
    minfo = None
    for index in range(len(restaurants)):
        new_to_do = restaurants[:index] + restaurants[index + 1:]
        temp_info = get_shortest_path([restaurants[index]], new_to_do, company, 0)
        if not minfo or temp_info["distance"] < minfo["distance"]: minfo = temp_info
    return minfo

# returns the distance and order of the shortest path from the start through
# all of the to_do locations and the end.
def get_shortest_path(done, to_do, end, distance):
    if not to_do:
        return {"distance" : distance + dist(done[-1], end), "order" : done}
    else: # minfo = min_info
        minfo = None
        previous_point = done[-1]
        for index in range(len(to_do)):
            new_done = done + [to_do[index]]
            new_dist = distance + dist(previous_point, to_do[index])
            new_to_do = to_do[:index] + to_do[index + 1:]
            temp_info = get_shortest_path(new_done, new_to_do, end, new_dist)
            if not minfo or temp_info["distance"] < minfo["distance"]: minfo = temp_info
        return minfo

# prints info about order matches to drivers
def print_data(final_matches, orders, percent_matched, total_distance):
    print("* Percent of Companies Matched = %.2f%%" % percent_matched)
    print("* Total distance for all drivers to first resturant = %.4f\n" % (total_distance))

    for final_inc in range(len(final_matches)):
        order_match = final_matches[final_inc]
        order = orders[final_inc]
        if (order_match is None):
            print("Order #%d has no match\n" %(final_inc + 1))
        else:
            print("Order #%d is matched to Driver #%d" % (final_inc + 1, order_match[0] ))
            print("-> Restaurant order : ", end="")
            for item in order.get_shortest_path()["order"]: print(item.name, end=", ")
            print("\n-> Distance to first restaurant = %.4f" % order_match[1])
            print("-> Distance between pickups & dropoff = %.4f" % order.get_shortest_path()["distance"])
            total_distance = order_match[1] + order.get_shortest_path()["distance"]
            print("-> Total Distance = %.4f" % total_distance)
            print("-> Order Deadline = %.4f\n" % order.deadline)


# converts degrees to radians
def deg2rad(deg):
    return deg * (math.pi/180)

# converts radians back to degrees
def rad2deg(rad):
    return rad * (180/math.pi)

# Formula for distance between objects using lat/long
def dist(start, end):
    lat1, lon1 = start.location
    lat2, lon2 = end.location
    dLat = deg2rad(lat2-lat1)
    dLon = deg2rad(lon2-lon1)
    a = math.sin(dLat/2) ** 2 + math.cos(deg2rad(lat1)) * math.cos(deg2rad(lat2)) * math.sin(dLon/2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(a))

def dist_rad(start, end):
    lat1, lon1 = start.location
    lat2, lon2 = end.location
    dLat = deg2rad(lat2-lat1)
    dLon = deg2rad(lon2-lon1)
    a = math.sin(dLat/2) ** 2 + math.cos(deg2rad(lat1)) * math.cos(deg2rad(lat2)) * math.sin(dLon/2) ** 2
    return 2 * math.asin(math.sqrt(a))

# Functions for mapping lat/long to X/Y
def lat_long_to_X_Y(loc):
    x = ((1000/360.0) * (180 + loc[1]))
    y = ((1000/180.0) * (90 - loc[0]))
    return [x,y]

# Eucliadian Distance function
def dist_X_Y(loc1,loc2):
    return ((loc1[0] - loc2[0]) ** 2 + (loc1[1] - loc2[1]) ** 2) ** .5

def generate_extra_order_edges(graph, combo_index, o1_index, o2_index, driver_offset, order_offset, to_text):
    graph.AddArcWithCapacityAndUnitCost(order_double_node(combo_index, order_offset), order_main_node(o1_index, driver_offset), 1, 0)
    graph.AddArcWithCapacityAndUnitCost(order_double_node(combo_index, order_offset), order_main_node(o2_index, driver_offset), 1, 0)

def driver_main_node(i): return 3 * i + 1
def driver_single_order_node(i): return 3 * i + 2
def driver_double_order_node(i): return 3 * i + 3

def order_main_node(i, do): return do + (i * 2)
def order_single_node(i, do): return 1 + do + (i * 2)
def order_double_node(n, oo): return oo + n

def print_path(path):
    for location, d in zip(path['order'], path['distances']):
        print('at', location.get_name(), 'with distance', d)
    print()
