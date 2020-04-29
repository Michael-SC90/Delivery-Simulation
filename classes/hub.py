# Michael Craig, 000955248
from .package import Package
from app.trip_calc import shortest_distance
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# Primary data structure; houses all package information, including
# tables for storing delivery addresses, specific statuses, as well
# as the graph for determining available travel routes.
class Hub:
    def __init__(self, graph):
        self.city_graph = graph
        self.bundles = {}
        self.deliveries = {}
        self.packages = []
        self.pkg_id_table = {}
        self.late_arrivals = {}
        self.statuses = {"Delivered": [],
                         "On truck": [],
                         "At hub": [],
                         "Bundling": [],
                         "Bundled": [],
                         "Preassigned": [],
                         "Delayed": [],
                         "Correction needed": []}

    # Produces list of all packages from hash table for simulation to track progress.
    # O(N)
    def produce_packages(self, tup_lst):
        for tup in tup_lst:
            p_id, address, deadline, city, state, p_zip, weight, note = tup
            address = self.city_graph.get_vertex(address)
            if address not in self.deliveries:
                self.deliveries[address] = []
            new_package = Package(p_id, address, deadline, city, state, p_zip, weight, note)
            self.deliveries[address].append(new_package)
            process_note(new_package)
            if new_package.status in self.statuses:
                self.statuses[new_package.status].append(new_package)
            else:
                self.statuses[new_package.status] = [new_package]
            self.packages.append(new_package)
            self.pkg_id_table[p_id] = new_package
        return

    # Filters main package list into individual tables to track statuses.
    # O(N*M)
    def process_package_states(self, trucks, start_time):
        delayed_lst = self.statuses["Delayed"]
        if len(delayed_lst) > 0:
            self.identify_delayed(delayed_lst)
        assigned_lst = self.statuses["Preassigned"]
        if len(assigned_lst) > 0:
            self.identify_assignments(trucks, assigned_lst, start_time)
        bundle_lst = self.statuses["Bundling"]
        if len(bundle_lst) > 0:
            self.identify_bundles(bundle_lst)
        correction_lst = self.statuses["Correction needed"]
        if len(correction_lst) > 0:
            self.identify_corrections(correction_lst)
        return

    # Loads late packages to late arrivals and status tables.
    # O(N)
    def identify_delayed(self, package_lst):
        delayed_deliveries = []
        for pkg in package_lst:
            arrival_time, address = self.prepare_late_arrival(pkg)
            delayed_deliveries.append((arrival_time, address))
        for delivery in delayed_deliveries:
            self.delay_delivery(*delivery)
        return

    # Loads packages requiring to be on certain trucks to status table and designated truck.
    # O(N)
    def identify_assignments(self, trucks, package_lst, start_time):
        assigned_deliveries = {}
        for pkg in package_lst:
            address = pkg.address
            truck_assignment = int(pkg.note.split("Can only be on truck ")[1])
            assigned_deliveries[address] = truck_assignment
            logging.debug('Package pre-assigned: packageID={}, truckID={}'.format(pkg.id, truck_assignment))
        hub_vertex = self.city_graph.get_vertex('HUB')
        for address in assigned_deliveries:
            truck_id = assigned_deliveries[address]
            truck = trucks[truck_id - 1]
            self.load_delivery(truck, address)
            truck.schedule_deliveries(self.city_graph, hub_vertex, hub_vertex, start_time)
        return

    # Loads packages with bundling requirements to status and bundles tables.
    # O(N*M)
    def identify_bundles(self, package_lst):
        comparison_lst = []
        for pkg in package_lst:
            comparison_lst.append(pkg)
            bundle_lst = pkg.note.split("Must be delivered with ")[1].split(", ")
            new_list = []
            for other_pkg in bundle_lst:
                other_pkg = self.pkg_id_table[int(other_pkg)]
                update_status(other_pkg, "Bundled")
                new_list.append(other_pkg)
            self.bundles[pkg] = new_list
        prev_pkg = comparison_lst[0]
        logging.debug('Loaded bundles: {}'.format(self.bundles))
        logging.debug('Comparing bundles...')
        for pkg in comparison_lst:
            logging.debug('Current bundle: {} (size={})'.format(self.bundles[pkg], len(self.bundles[pkg])))
            if pkg is not prev_pkg:
                self.compare_bundles(prev_pkg, pkg)
            logging.info('Skipping bundle: no merge candidates')
            if pkg in self.bundles:
                prev_pkg = pkg
        logging.debug('Appending deliveries to bundles...')
        for bundle in self.bundles:
            address_lst = []
            for other_pkg in self.bundles[bundle]:
                if other_pkg.address not in address_lst:
                    address_lst.append(other_pkg.address)
            for address in address_lst:
                for some_pkg in self.deliveries[address]:
                    if some_pkg not in self.bundles[bundle]:
                        self.bundles[bundle].append(some_pkg)
                        logging.info('Appending to bundle: package_id={}, address={}'.format(some_pkg.id,
                                                                                             address.label))
                        update_status(some_pkg, "Bundled")
        logging.debug('Loaded bundles: {}'.format(self.bundles))
        return

    # Loads packages with incorrect information to status table
    # O(N)
    def identify_corrections(self, package_lst):
        for pkg in package_lst:
            address = pkg.address
            delivery_table = self.deliveries
            delivery_table[address].remove(pkg)
            self.packages.remove(pkg)

    # Determines next package based on closest distance to a truck's last scheduled location
    # if that truck already has packages, otherwise it selects the package with the earliest deadline.
    # O(N^2 * M), where N = number of vertices; M = number of packages
    def determine_package(self, truck):
        g = self.city_graph
        if truck.package_count == 0:
            self.packages.sort(key=lambda pkg: pkg.deadline, reverse=True)
            next_package = self.packages.pop()
        else:
            self.packages.sort(key=lambda pkg: (pkg.deadline, shortest_distance(g,
                                                                                truck.last_location(),
                                                                                pkg.address)),
                               reverse=True)
            next_package = self.packages.pop()
        return next_package

    # Schedule the package and any packages with similar address to truck.
    # O(N*M*P), where N < M <= P
    def process_package(self, truck, package):
        process_log = 'Processing: truck_id={}, package_id={}, package_status={}'
        logging.debug(process_log.format(truck.id, package.id, package.status))
        if "Bundled" in package.status:
            for other_pkg in self.bundles:
                if package in self.bundles[other_pkg]:
                    self.load_bundle(truck, other_pkg)
                    break
        elif "Bundling" in package.status:
            self.load_bundle(truck, package)
        else:
            address = package.address
            self.load_delivery(truck, address)
        return

    # Combines dictionary list values if intersection exists.
    # O(N)
    def compare_bundles(self, pkg_a, pkg_b):
        if common_bundle(self.bundles[pkg_a], self.bundles[pkg_b]):
            logging.info('Merging bundles: pkg_a_ID={}, pkg_b_ID={}'.format(pkg_a.id, pkg_b.id))
            pkg_lst = self.bundles.pop(pkg_b)
            self.bundles[pkg_a].append(pkg_b)
            for pkg in pkg_lst:
                self.bundles[pkg_a].append(pkg)
            self.bundles[pkg_a] = list(set(self.bundles[pkg_a]))
            update_status(pkg_b, "Bundled")
        return

    # Readies late arrival table to delay a delivery to an address
    # if all packages for that address are not ready.
    # O(1)
    def prepare_late_arrival(self, pkg):
        late_table = self.late_arrivals
        note = pkg.note
        arrival_time = note.split("Delayed on flight---will not arrive to depot until ")[1].split(" ")[0]
        arrival_time = to_sec(arrival_time)
        address = pkg.address
        if arrival_time in late_table:
            if address in late_table[arrival_time]:
                late_table[arrival_time][address].append(pkg)
            else:
                late_table[arrival_time][address] = [pkg]
        else:
            late_table[arrival_time] = {address: [pkg]}
        return arrival_time, address

    # Relocates packages from deliveries table to delayed table.
    # O(N)
    def delay_delivery(self, arrival_time, address):
        packages = self.deliveries[address]
        late_arrivals = self.late_arrivals[arrival_time][address]
        for package in packages:
            if package not in late_arrivals:
                late_arrivals.append(package)
            self.packages.remove(package)
            update_status(package, "Delayed")
        return

    # Determines package count for any number of packages associated with a single package,
    # whether they share a common address, or have bundling requirements.
    # O(1)
    def total_pkg_count(self, pkg):
        total_count_log = 'Counting: package_id={}, address={}'
        logging.debug(total_count_log.format(pkg.id, pkg.address.label))
        bundle_size = 0
        address = pkg.address
        if len(self.bundles) > 0:
            if pkg.status == "Bundling":
                if pkg in self.bundles:
                    bundle_size = len(self.bundles[pkg])
        delivery_size = len(self.deliveries[address]) + bundle_size
        return delivery_size

    # Moves package from hub list to truck list.
    # O(1)
    def load_package(self, truck, package):
        if package in self.packages:
            self.packages.remove(package)
        update_status(package, "On truck")
        truck.add_package(package)
        logging.info('Package loaded: packageID={}, truckID={} [package_count={}]'.format(package.id,
                                                                                          truck.id,
                                                                                          truck.package_count))
        logging.debug('{}'.format(package))
        return

    # Loads a truck with all packages associated with a single delivery address
    # O(N)
    def load_delivery(self, truck, address):
        logging.info('Loading delivery: truckID={}, address={}'.format(truck.id, address.label))
        if address in self.deliveries:
            packages = self.deliveries[address]
            for package in packages:
                if package.status != "Delivered":
                    if package.status != "On truck":
                        self.load_package(truck, package)
        else:
            logging.error('Delivery load failed: truckID={}, address={}'.format(truck.id, address.label))
        return

    # Loads a truck with all packages with particular bundling requirements.
    # O(N*M)
    def load_bundle(self, truck, package):
        logging.info('Loading bundle: truckID={}, bundle_key={} (packageID)'.format(truck.id, package.id))
        packages = self.bundles[package]
        packages.append(package)
        addresses = []
        for pkg in packages:
            self.bundles[pkg] = packages
            logging.info('Un-bundling: packageID={}, address={}, status={}'.format(pkg.id, pkg.address, pkg.status))
            if pkg.address not in addresses:
                addresses.append(pkg.address)
        for address in addresses:
            self.load_delivery(truck, address)
        return

    # Updates package objects determined to be delayed arrivals and appends them
    # to list of packages for trucks to pull from.
    # O(N)
    def receive_packages(self, arrival_time):
        logging.info('Receiving additional packages...')
        delayed_lst = self.statuses["Delayed"]
        received_lst = []
        for package in delayed_lst:
            received_lst.append(package)
            address = package.address
            logging.debug('packageID={}, address={}'.format(package.id, address.label))
            if address in self.deliveries:
                if package not in self.deliveries[address]:
                    logging.debug('Appending to existing delivery...')
                    self.deliveries[address].append(package)
            else:
                logging.debug('Creating new delivery...')
                self.deliveries[address] = [package]
            if address in self.late_arrivals[arrival_time]:
                delivery = list(set(self.deliveries[address]).union(self.late_arrivals[arrival_time][address]))
                self.deliveries[address] = delivery
        for package in received_lst:
            self.packages.append(package)
            update_status(package, "At hub")
        return

    # Corrects package at specified time; doesn't update if package already delivered or on truck
    # O(1)
    def correct_package(self):
        logging.info('Correcting packages...')
        pkg = self.pkg_id_table[9]
        address = '410 S State St'
        address = self.city_graph.get_vertex(address)
        pkg.address = address
        city_zip = '84111'
        pkg.zip = city_zip
        update_status(pkg, "At hub")
        if address in self.deliveries:
            self.deliveries[address].append(pkg)
        else:
            self.deliveries[address] = [pkg]
        logging.info('Correction made: package_id={}, address={}'.format(pkg.id, pkg.address))
        self.packages.append(pkg)
        return


# Reads notes from incoming packages to determine necessary actions before day starts;
# only sorts statuses, does not take action on packages.
# O(1)
def process_note(pkg):
    note = pkg.note
    if "Can only be on truck" in note:
        update_status(pkg, "Preassigned")
    elif "Delayed on flight---will not arrive to depot until" in note:
        update_status(pkg, "Delayed")
    elif "Wrong address listed" in note:
        update_status(pkg, "Correction needed")
    elif "Must be delivered with" in note:
        update_status(pkg, "Bundling")
    else:
        update_status(pkg, "At hub")
    return


# Relocates package from one state in a table to another.
# O(1)
def update_status(pkg, new_status):
    status_log = 'Updating package status: package_id={}, old_status={}, new_status={}'
    logging.info(status_log.format(pkg.id, pkg.status, new_status))
    pkg.status = new_status
    return


# Checks if a package exists within lists associated with two packages.
# O(N*M), where N = package count in bundle A; M = package count in bundle B
def common_bundle(pkg_a, pkg_b):
    return any(pkg in pkg_a for pkg in pkg_b)


# Converts time string (HH:MM) to count in seconds to allow easy comparison.
# O(1)
def to_sec(time_str):
    hour = int(time_str.split(":")[0])
    minute = int(time_str.split(":")[1])
    return hour * 3600 + minute * 60


# Returns list of trucks currently located at Hub.
# O(N), where N = truck count
def available_trucks(graph, truck_lst):
    hub_vertex = graph.get_vertex('HUB')
    return list(filter(lambda truck: truck.location is hub_vertex, truck_lst))
