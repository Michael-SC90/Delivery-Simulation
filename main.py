# Michael Craig, 000955248
from app.csv_reader import load_package_csv, load_city_csv
from app.trip_calc import shortest_distance
from app.classes.hub import Hub, to_sec, update_status
from app.classes.truck import Truck
from app.classes.package import clock_time
import logging
import os


for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s] %(module)-10s %(levelname)-8s %(message)s',
                    datefmt='%m-%d-%Y %I:%M:%S %p',
                    filename='DeliveryScheduler.log',
                    filemode='w')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)-12: %(levelname)-82 %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)
hub_logger = logging.getLogger('app.classes.hub')


# Render GUI
def generate_ui():
    logging.info('=======Route Calculation=======')
    logging.info('1. Display all packages\' status')
    logging.info('q. Quit')
    logging.info('===============================')
    logging.info("Please select an option to continue...\n")
    selection = input()
    return selection


# Runs simulation of hub activity, including shipping and receiving, truck scheduling,
# processing changes to package data, and measuring truck statistics.
# # O(N^2 * M^2), where N = number of packages; M = number of graph vertices.
def simulate_deliveries(pkg_lst, graph, seconds_count):
    hub = Hub(graph)
    hub_vertex = graph.get_vertex('HUB')
    hub.produce_packages(pkg_lst.get_all())  # O(N)

    start_time = 28800
    sim_time = start_time
    num_trucks = 2
    trucks = ready_trucks(hub_vertex, num_trucks, start_time)
    hub.process_package_states(trucks, start_time)

    # Set state for receiving late packages
    first_update = 32700
    entered_a = False
    # Set state for correcting invalid package data
    second_update = 37200
    entered_b = False

    while sim_time < seconds_count:  # O(N^2 * M^2)
        logging.info('Checking for updates...')
        if sim_time >= first_update and not entered_a:
            hub.receive_packages(first_update)  # O(N)
            entered_a = True
        if sim_time >= second_update and not entered_b:
            hub.correct_package()  # O(1)
            entered_b = True

        if min(trucks, key=lambda trk: trk.end_time()).location == hub_vertex:  # O(N)
            while len(hub.packages) > 0:  # O(N^2 * M(M-N))
                next_truck = determine_truck(trucks)  # O(N)
                start_time = next_start_time(next_truck, sim_time)  # O(1)
                if len(next_truck.reserve) > 0:
                    for package in next_truck.reserve:  # O(N)
                        if package not in next_truck.packages:
                            next_truck.add_package(package)
                    for package in next_truck.packages:  # O(N)
                        if package in next_truck.reserve:
                            next_truck.reserve.remove(package)
                    next_truck.schedule_deliveries(graph, hub_vertex, hub_vertex, start_time)  # O(N^2 * M^2)
                next_package = hub.determine_package(next_truck)  # O(N)

                package_count = hub.total_pkg_count(next_package)  # O(1)
                if next_truck.package_count + package_count <= next_truck.capacity:
                    hub.process_package(next_truck, next_package)  # O(N*M*P)
                    load_log = 'Delivery loaded: packageID={}, truckID={}, start_time={}'
                    logging.info(load_log.format(next_package.id, next_truck.id, clock_time(start_time)))
                    start_time = next_start_time(next_truck, sim_time)
                    next_truck.schedule_deliveries(graph, hub_vertex, hub_vertex, start_time)  # O(N^2 * M^2)
                else:
                    hub.packages.append(next_package)
                    cur_count = next_truck.package_count
                    load_log = 'Truck full: truck_id={} [package_count={}]'
                    logging.info(load_log.format(next_truck.id, cur_count))
                    break

        for truck in trucks:  # O(N^2 * M)
            truck.deliver_packages(sim_time)  # O(N) ; O(1) since truck never exceeds 16?
            dist_to_hub = shortest_distance(graph, truck.location, hub_vertex)  # O(N^2)
            next_delivery = shortest_distance(graph, truck.location, truck.next_location())  # O(N^2)
            hub_dist_from = shortest_distance(graph, truck.next_location(), hub_vertex)  # O(N^2)
            optimization_log = 'Optimization check: distance_to [hub={}, next_delivery={}, hub_from_delivery={}]'
            logging.info(optimization_log.format(dist_to_hub, next_delivery, hub_dist_from))
            worst_case_distance = next_delivery + hub_dist_from
            if dist_to_hub < worst_case_distance:
                if len(hub.packages) > 0:
                    deadline = min(hub.packages, key=lambda pkg: pkg.deadline).deadline  # O(N)
                    logging.debug('Earliest deadline at hub: deadline={}'.format(clock_time(deadline)))
                    if deadline < truck.end_time() + truck.travel_time(worst_case_distance):
                        recall_log = 'Recalling truck: truck_id={}, package_count={}, location={}'
                        logging.info(recall_log.format(truck.id, truck.package_count, truck.location.label))
                        recall_truck(hub, truck, sim_time)  # O(N)
            truck.deliver_packages(sim_time)  # O(N)
            separator = '=-' * 50 + '=\n'
            logging.info(separator)
        sim_time += 900

    active_time = 0
    for truck in trucks:  # O(N^2)
        truck.deliver_packages(sim_time)  # O(N)
        active_time += truck.end_time() - start_time
    total_mileage = active_time * .005  # miles per second
    logging.info('PACKAGE STATUS AT: {}'.format(clock_time(seconds_count)))
    logging.debug('sim_time={} [{}], total_mileage={}'.format(sim_time, clock_time(sim_time), total_mileage))
    for truck in trucks:
        logging.info(truck)
    logging.info("TOTAL MILEAGE: %d\n" % total_mileage)
    return


# Produces truck objects for use in simulation.
# O(N), where N = number of trucks
def ready_trucks(cur_vertex, num_trucks, start_time):
    trucks = []
    for x in range(num_trucks):
        new_truck = Truck(x + 1, cur_vertex)
        new_truck.itinerary.schedule_start(start_time)
        trucks.append(new_truck)
    return trucks


# Returns truck with most room (capacity - count).
# O(N), where N = number of trucks (min function iteration)
def determine_truck(trucks):
    next_truck = min(trucks, key=lambda truck: truck.end_time())
    logging.info('Truck selected: truckID={}, package_count={}'.format(next_truck.id, next_truck.package_count))
    return next_truck


# Returns time value (in seconds) for when to schedule the start of a truck's tour.
# O(1)
def next_start_time(truck, cur_time):
    cur_start = truck.start_time()
    cur_end = truck.end_time()
    schedule_start_log = 'Scheduling start time: truckID={}, prompt={}, start={}, end={}'
    logging.info(schedule_start_log.format(truck.id, clock_time(cur_time), clock_time(cur_start), clock_time(cur_end)))
    if cur_end > cur_time:
        new_start_time = cur_start
    else:
        new_start_time = cur_end
    return new_start_time


# Removes packages without special requirements from a truck's delivery schedule so that
# the truck can return to the hub sooner when deadline criteria is in jeopardy.
# Hub deliveries is a dictionary, so checking for address key is O(1).
# O(N), where N = remaining packages on truck (N <= 16)
def recall_truck(hub, truck, cur_time):
    g = hub.city_graph
    hub_vertex = g.get_vertex('HUB')
    returning_packages = []
    for package in truck.packages:
        package.arrival_time = 86399
        if package in hub.bundles:
            if package not in truck.reserve:
                truck.reserve.append(package)
                update_status(package, 'On truck')
        elif package in hub.statuses['Preassigned']:
            if package not in truck.reserve:
                truck.reserve.append(package)
                update_status(package, 'On truck')
        else:
            if package.status != "Delivered":
                if package not in hub.packages:
                    returning_packages.append(package)
                    update_status(package, 'At hub')
                    hub.packages.append(package)
    for package in returning_packages:
        truck.packages.remove(package)
        truck.package_count -= 1
    for package in truck.reserve:
        if package in truck.packages:
            truck.package_count -= 1
            truck.packages.remove(package)
    truck.schedule_deliveries(g, truck.location, hub_vertex, cur_time)
    return


# Clears screen.
# O(1)
def clear():
    os.system('cls')


# Main Program
if __name__ == "__main__":
    clear()
    package_table = load_package_csv('WGUPS Package File.csv')  # O(N)
    city_graph = load_city_csv('WGUPS Distance Table.csv')  # O(N*M)
    while True:
        choice = generate_ui()
        if choice == "1":
            logging.debug(choice)
            logging.info('Please enter time to view package status:\n')
            prompt = input()
            prompt_in_seconds = to_sec(prompt)
            logging.debug('User input received: {} [{}]'.format(prompt, prompt_in_seconds))
            simulate_deliveries(package_table, city_graph, prompt_in_seconds)
        elif choice == "q":
            break
