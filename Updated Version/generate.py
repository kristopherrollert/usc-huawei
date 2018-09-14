from objects import *
import random
import string
import json

'''   <<<<<<<<<<<<<<<<<<<<<<    YELP DATA CONVERTER    >>>>>>>>>>>>>>>>>>>>>>   '''

# right now, only grabs from Las Vegas
def generate_restaurants_file_from_json(dir):
    write_file = open('data/restaurants.json', 'w')
    with open(dir, 'r') as file:
        for line in file:
            line_data = json.loads(line)
            if 'Las Vegas' in line_data['city'] and verify_restaurant(line_data):
                write_file.write(json.dumps({
                    'name' : line_data['name'],
                    'id' : line_data['business_id'],
                    'rating' : line_data['stars'],
                    'location' : [line_data['latitude'], line_data['longitude']],
                }) + "\n" )

# Returns the boolean if the data is a bar, resturant, or serves food
def verify_restaurant(data):
    return 'Food' in data['categories'] or \
        'Restaurants' in data['categories'] or \
        'Bars' in data['categories']

'''   <<<<<<<<<<<<<<<<<<<<<<    JSON TO OBJECTS   >>>>>>>>>>>>>>>>>>>>>>   '''

def generate_all():
    i = { 'restaurants' : generate_restaurants('data/restaurants.json') ,
             'companies'  : generate_companies('data/companies.json')   ,
             'drivers'    : generate_drivers('data/drivers.json')       }
    i['orders'] = generate_orders('data/orders.json', i['restaurants'][1], i['companies'][1])
    return i

def generate_orders(input_file, r_dict, c_dict):
    all_o = []
    o_dict = {}
    with open(input_file, 'r') as f:
        num = 0
        for line in f:
            data = json.loads(line)
            comp = c_dict[data['company']]
            rests = [r_dict[x] for x in data['restaurants']]
            temp = Order(data['id'], comp, rests, data['deadline'], num)
            o_dict[data['id']] = temp
            num += 1
            all_o.append(temp)
    return (all_o, o_dict)

def generate_restaurants(input_file):
    all_r = []
    r_dict = {}
    with open(input_file, 'r') as f:
        for line in f:
            data = json.loads(line)
            temp = Restaurant(data['id'], data['location'])
            temp.set_name(data['name'])
            temp.set_rating(data['rating'])
            r_dict[data['id']] = temp
            all_r.append(temp)
    return (all_r, r_dict)

def generate_companies(input_file):
    all_c = []
    c_dict = {}
    with open(input_file, 'r') as f:
        for line in f:
            data = json.loads(line)
            temp = Company(data['id'], data['location'])
            c_dict[data['id']] = temp
            all_c.append(temp)
    return (all_c, c_dict)

def generate_drivers(input_file):
    all_d = []
    d_dict = {}
    with open(input_file, 'r') as f:
        num = 0
        for line in f:
            data = json.loads(line)
            temp = Driver(data['id'], data['location'], num)
            d_dict[data['id']] = temp
            num += 1
            all_d.append(temp)
    return (all_d, d_dict)


'''   <<<<<<<<<<<<<<<<<<<<<<    TEST DATA CREATOR   >>>>>>>>>>>>>>>>>>>>>>   '''
# (y,x)
    # top left:     36.320904, -115.364003
    # top right:    36.320904, -114.890439
    # bottom left:  35.931493, -115.364003
    # bottom right: 35.931493, -114.890439

def get_random_LV_lat_long():
    y_range = int((115.364003 - 114.890439) * 1000000)
    x_range = int((36.320904 - 35.931493) * 1000000)
    y_ran = random.randint(0, x_range) / 1000000.0
    x_ran = random.randint(0, y_range) / 1000000.0
    return (35.931493 + x_ran, -115.364003 + y_ran)

def get_random_id(size):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(size))

def get_random_deadline():
    return random.randint(500, 800) / 10.0

def generate_new_test_data(c_num, d_num, o_num):
    all_r, r_dict = generate_restaurants('data/restaurants.json')
    generate_new_test_drivers(d_num)

    c_file = open('data/companies.json', 'w')
    c_ids = []
    for c in range(c_num):
        temp_id = get_random_id(16)
        c_ids.append(temp_id)
        c_file.write(json.dumps({
            "id" : temp_id,
            "location" : get_random_LV_lat_long()
        }) + "\n")

    o_file = open('data/orders.json', 'w')
    for o in range(o_num):
        r_ids = [r.id for r in random.sample(all_r, 3)]
        o_file.write(json.dumps({
            "id" : get_random_id(16),
            "company" : c_ids.pop(random.randint(0, len(c_ids) - 1)),
            "restaurants" : r_ids,
            "deadline" : get_random_deadline()
        }) + "\n")

def generate_new_test_driver():
    d_file = open('data/drivers.json', 'a')
    d_file.write(json.dumps({
        "id" : get_random_id(16),
        "location" : get_random_LV_lat_long()
    }) + "\n")

def generate_new_test_drivers(d_num):
    d_file = open('data/drivers.json', 'w')
    for d in range(d_num):
        d_file.write(json.dumps({
            "id" : get_random_id(16),
            "location" : get_random_LV_lat_long()
        }) + "\n")
