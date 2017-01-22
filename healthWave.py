from collections import Counter
from datetime import datetime, date, time
import math
import numpy as np
import re
from random import randint

def generate_data_people(x, num_weeks):
    schol = School()
    for y in range(x):
        a = generate_data_person(y, num_weeks)
        print (a.list_profiles)[0].mac_address
        schol.list_profiles.append(a.list_profiles[0])
    return schol

def generate_data_person(x, num_weeks):
    school = School()
    home = 'router' + str(randint(1,3))
    name = 'MAC ' + str(x + 1)
    num_classes = randint(1, 3)
    class_time1 = 5 + randint(6, 10)
    class_time2 = 5 + randint(1, (class_time1 - 5)) if num_classes > 1 else 100
    class_time3 = class_time1 + randint(1, (19 - class_time1)) if num_classes > 2 else 100
    for week_num in range(num_weeks):
        month = 1 + week_num / 4
        num_pts  = randint(1,3)
        for day_num in range(7):
            is_infected = randint(0,1) == True
            day1 = (week_num % 4) * 7 + day_num + 1
            for hour in range(24):
                if not(is_infected) and (abs(hour - class_time1) < 1 or abs(hour - class_time2) < 1 or abs(hour - class_time3) < 1):
                    router = 'router6'
                else:
                    router = home
                school.add_ping(router, name, datetime(2016, month, day1, hour, 15, 0, 0))
                school.add_ping(router, name, datetime(2016, month, day1, hour, 45, 0, 0))
    school.mac_address_exists(name).home = home
    return school

class School:

    def __init__(self):
        self.list_profiles = []
        self.list_routers  = []

    def add_ping(self, router, mac_address, time):
        if self.mac_address_exists(mac_address) is None:
            prof = Profile(mac_address)
            prof.add_time(router, time)
            self.list_profiles.append(prof)
        else:
            elem = self.mac_address_exists(mac_address)
            (self.list_profiles[self.list_profiles.index(elem)]).add_time(router, time)

    def mac_address_exists(self, curr_mac_address):
        for x in self.list_profiles:
            if x.mac_address == curr_mac_address:
                return x
            return None

    def get_infected_at_router(self, router):
        count = 0
        for x in self.list_profiles:
            if x.home == router and x.infected:
                count = count + 1
        return count

    def get_total_infected(self):
        count = 0
        for x in self.list_profiles:
            if x.infected:
                count = count + 1
        return count

    def print_list_profiles(self):
        for x in self.list_profiles:
            print(x.time)

class Profile:

    def __init__(self, mac_address):
        self.mac_address = mac_address
        self.time = []
# a  profile becomes enabled when it has enough data to be able to determine if a time is unusual
        self.is_enabled = False
        self.home = ""
        self.infected = False
        self.norm = []

    def add_time(self, router_name, time):
        self.time.append((router_name, time))
        if not(self.is_enabled):
            if len(self.time) > 50:
                self.activate()
        if (self.time[-1][1] - self.time[0][1]).days > 60:
            self.time.pop(0)

    def setHome(self, home):
        self.home = home

    def activate(self):
       self.is_enabled = True

def init_norm(time_pairs):
#returns norm as a vector of confidence values with 3 sig figs (0.000) for each hour
    hourly_IDs = {}
    keys = []
    norm = []
    for i in range (24):
        keys.append("h"+str(i))
    for router_ID, time in time_pairs:
        if type(time) is not datetime:
            raise TypeError('time must be a datetime, not a %s' % type(arg))
        isMAC = re.match("[0-9a-f]{2}([-:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", router_ID)
#        if not isMAC:
#            raise TypeError('%s is not a valid MAC address' % router_ID)
        #organizes router_ID into 1-hour intervals by creating dict with "key" (only organized by ToD, not DoW)
        key = "h" + str(time.hour)
        hourly_IDs.setdefault(key, []).append(router_ID)
    for k in keys:
        hrly_ping_num = len(hourly_IDs[k])
        rID_freq = Counter(hourly_IDs[k])
        mode = rID_freq.most_common(1)[0]
        confidence = math.ceil((float(mode[1])/hrly_ping_num)*1000)/1000
        norm.append((mode[0], confidence))
    return norm

def chk_Abnormal(time_pairs, norm):
    test = init_norm(time_pairs)
    #print "test:{0} \n\n norm:{1}\n\n".format(test,norm)
    test_conf = []
    for i,j in test:
        test_conf.append(j)
    conf = []
    for i,j in norm:
        conf.append(j)
    #compare norms
    conf_vec = np.asarray(conf)
    test_vec = np.asarray(test_conf)
    joined = np.array([conf_vec, test_vec])
    std_devs = np.std(joined, axis=0)
    #print std_devs
    ab_devs = filter(lambda x: x>.15, std_devs)
    if len(ab_devs)>2:
        return True
    else:
        return False


def adjust_norm(time_pairs, old_norm):
    #assume router usage at certain times is consistent, and confidence is the only changing variable
    #assume time_pairs comes from a >>dataset than norm
    delta = init_norm(time_pairs)
    #unpack norms
    rID=[]
    d_conf = []
    nu_norm=[]
    for i,j in delta:
        d_conf.append(j)
    conf = []
    for i,j in old_norm:
        conf.append(j)
        rID.append(i)
    #compare norms
    conf_vec = np.asarray(conf)
    delta_vec = np.asarray(d_conf)
    nu_conf = list(.4*delta_vec+.6*conf_vec)
    for i in range(len(nu_conf)):
        nu_norm.append((rID[i],nu_conf[i]))
    return nu_norm


uchiraq = generate_data_people(100, 20)
#split sample into arbitrary segments to enable testing and initializing
timespan = len(uchiraq.list_profiles[0].time)
print uchiraq.list_profiles
init_time = (timespan / 5) * 4
test_time = timespan - init_time
#    [(router1, [1 inf, 2 inf,3,4,5,6]), (router2, [1,4,6,7,9,10])]
dictionary = {'router1':[],'router2':[], 'router3': []}
for i in uchiraq.list_profiles:
    i.norm = init_norm(uchiraq.list_profiles[0].time[:init_time])
for i in range(test_time/48):  #loop through each days
    print ("alarum")
    dictionary['router1'].append(0)
    dictionary['router2'].append(0)
    dictionary['router3'].append(0)
    for x in uchiraq.list_profiles:
        if not chk_Abnormal(x.time[init_time:(init_time+49+(i*48))], x.norm):
            print("not abnormal (phewf!)")
            x.norm = adjust_norm(uchiraq.list_profiles[0].time[init_time:(init_time+49+(i*48))], x.norm)
        else:
            dictionary[x.home][-1] = dictionary[x.home][-1] + 1
            print("Abnormal!")
print(dictionary)
