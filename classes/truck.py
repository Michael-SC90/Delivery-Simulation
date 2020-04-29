# Michael Craig, 000955248
from .travel_schedule import TravelSchedule
from .package import clock_time
from .delivery import Delivery
from app.trip_calc import dsp, shortest_tour, shortest_distance
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# Separates packages from initial list to reduce size of scheduling parameters
# from 40 to truck capacity (16) or less.
class Truck:
    def __init__(self, t_id, hub_vertex):
        self.id = t_id
        self.SPEED = 18
        self.total_mileage = 0
        self.trip_odometer = 0
        self.capacity = 16
        self.location = hub_vertex
        self.package_count = 0
        self.packages = []
        self.reserve = []
        self.delivered = []
        self.deliveries = {}
        self.itinerary = TravelSchedule(hub_vertex)

    # Adds single package to truck; includes delivery address if not already in table.
    # O(1)
    def add_package(self, pkg):
        self.packages.append(pkg)
        self.package_count += 1
        address = pkg.address
        if address in self.deliveries:
            return
        else:
            new_delivery = Delivery(address)
            self.deliveries[address] = new_delivery
            return

    # Determines schedule based on current packages assigned to truck;
    # Does not accumulate mileage, nor does it deliver packages, it just
    # produces a schedule that includes locations to visit and arrival times.
    # O(N^2 * M^2), where N = number of vertices in graph; M = number of packages on truck (M <= 16)
    def schedule_deliveries(self, graph, initial_vertex, end_vertex, start_time):
        new_itinerary = TravelSchedule(initial_vertex)
        new_itinerary.schedule_start(start_time)  # O(1)
        self.itinerary = new_itinerary
        cur_vertex = initial_vertex
        unscheduled = []
        for package in self.packages:  # O(N)
            package.arrival_time = 86399
            unscheduled.append(package)
        tour = []
        while unscheduled:  # O(N^2 * M^2)
            unscheduled.sort(key=lambda pkg: (pkg.deadline, shortest_distance(graph, cur_vertex, pkg.address)),
                             reverse=True)  # O(N^2 * M)
            cur_package = unscheduled.pop()
            next_vertex = cur_package.address
            if next_vertex not in tour:
                dsp(graph, cur_vertex)  # O(N^2)
                tour_leg = shortest_tour(cur_vertex, next_vertex)  # O(N)
                tour += tour_leg
                arrival_time = self.schedule_route(tour_leg)  # O(N)
                cur_delivery = self.deliveries[next_vertex]
                self.schedule_delivery(cur_delivery, arrival_time)  # O(1)
                cur_package.arrival_time = arrival_time
                cur_vertex = next_vertex
            else:
                cur_package.arrival_time = self.deliveries[next_vertex].end_time
        home_leg = route_to_hub(graph, cur_vertex, end_vertex)  # O(N^2)
        self.schedule_route(home_leg)  # O(N)
        return

    # Saves time of arrival for each particular location visited in a trip from
    # one location to another; saves to truck's current travel schedule.
    # O(N), where N = number of locations in tour
    def schedule_route(self, tour_leg):
        for location in tour_leg:
            leg_time = self.travel_time(location.distance)
            location.arrival_time = leg_time + self.itinerary.end_time
            self.itinerary.schedule_location(location)
            if location in self.deliveries:
                self.deliveries[location].end_time = min(location.arrival_time, self.deliveries[location].end_time)
        return self.itinerary.end_time

    # Provides estimation for time to perform delivery.
    # O(1)
    def travel_time(self, distance):
        return distance / self.SPEED * 3600  # Miles/(MPH)*(Seconds/Hour) = Seconds

    # Schedule delivery for truck.
    # O(1)
    def schedule_delivery(self, delivery, end_time):
        self.itinerary.schedule_delivery(delivery, end_time)
        return

    # Determines locations truck will visit over a period of time and
    # adjusts package statuses and own package count as deliveries occur.
    # O(N), where N = number of packages on truck (N <= 16)
    def deliver_packages(self, sec_count):
        start = self.itinerary.start_time
        delivery_batch = []
        time_active = sec_count - start
        delivery_log = 'Simulating deliveries: truckID={}, start_time={}, active_time={}'
        logging.debug(delivery_log.format(self.id, clock_time(sec_count), time_active))
        self.update_stats(time_active)
        for package in self.packages:
            if package.arrival_time <= sec_count:
                package.status = "Delivered"
                self.package_count -= 1
                delivery_batch.append(package)
                log_str = 'Package delivered: package_id={}, address={}, arrival_time={} [{}]'
                logging.info(log_str.format(package.id,
                                            package.address.label,
                                            package.arrival_time,
                                            clock_time(package.arrival_time)))
        for package in delivery_batch:
            self.packages.remove(package)
            self.deliveries.pop(package.address, None)
        self.delivered += delivery_batch
        return

    # Returns location of truck at time of day (in seconds) and updates mileage.
    # O(N), where N = total number of locations scheduled
    def update_stats(self, time_active):
        speed = self.SPEED / 3600  # miles per second
        distance_lst = sorted(self.itinerary.locations.keys(), reverse=True)
        cur_dist = 0
        distance_travelled = int(time_active * speed)
        last_dist = cur_dist
        while cur_dist < distance_travelled:
            if distance_lst:
                last_dist = cur_dist
                cur_dist = distance_lst.pop()
                travel_log = 'Travelling to location: truckID={}, cur_location={}, cur_distance={}'
                logging.debug(travel_log.format(self.id, self.itinerary.locations[cur_dist].label, cur_dist))
            else:
                break
        if cur_dist > distance_travelled:
            self.itinerary.next_location = self.itinerary.locations[cur_dist]
            cur_dist = last_dist
        self.trip_odometer = cur_dist
        mileage_log = 'Updating mileage: truckID={}, new_dist={}, mileage={}'
        logging.info(mileage_log.format(self.id, cur_dist, self.trip_odometer))
        self.location = self.itinerary.locations[cur_dist]
        return

    # Getter for start time of truck's current itinerary.
    # O(1)
    def start_time(self):
        return self.itinerary.start_time

    # Getter for end time of truck's current itinerary.
    # O(1)
    def end_time(self):
        return self.itinerary.end_time

    # Getter for next delivery location in truck's current itinerary.
    # O(1)
    def next_location(self):
        return self.itinerary.next_location

    # Getter for last location visited by truck.
    # O(1)
    def last_location(self):
        return self.itinerary.last_location

    # String override for viewing details of truck.
    def __str__(self):
        data = "\n" + "=-" * 68 + "=\n"
        loc = 'Location'
        data += "|\tTruck ID\t|\t{:<62}\t|\tPackage Count\t|\tTour Start\t|\tTour end\t|\tTour Mileage\n".format(loc)
        row_format = "|\t{:<8}\t|\t{:<62}\t|\t{:<14}\t|\t{:<10}\t|\t{:<10}\t|\t{:<10}\n"
        start = clock_time(self.itinerary.start_time)
        end = clock_time(self.itinerary.end_time)
        data += row_format.format(self.id, self.location.label, self.package_count, start, end, self.trip_odometer)
        data += "|----Package List:" + "-" * 119 + "\n"
        data += "|\tID\t|\t{:<70}\t|\tWeight\t|\tStatus\t\t|\tScheduled arrival\n".format('Address')
        packages = self.delivered + self.packages
        packages.sort(key=lambda pkg: pkg.arrival_time)
        for package in packages:
            data += str(package)
            data += "=-" * 68 + "=\n"
        return str(data)


# Provides route to hub from current location.
# O(N^2) with dsp
def route_to_hub(graph, cur_vertex, hub_vertex):
    dsp(graph, cur_vertex)
    home_leg = shortest_tour(cur_vertex, hub_vertex)
    return home_leg
