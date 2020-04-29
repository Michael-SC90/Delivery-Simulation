# Michael Craig, 000955248
from .rh_table import RobinHoodHashTable
from .classes.city import City, Address


# Load package list from CSV.
# Runs with time complexity of O(N), where N = number of lines in file
def load_package_csv(filename):
    table = RobinHoodHashTable()
    file = open(filename, "r")
    lines = file.readlines()
    for line in lines:
        try:
            p_id, address, city, state, p_zip, p_deadline, weight, note = line.split(",,,,,\n")[0].split(",")
            if "EOD" not in p_deadline:
                deadline_hour = p_deadline.split(":")[0]
                deadline_min = p_deadline.split(":")[1].split(" ")[0]
                p_deadline = (int(deadline_hour) * 3600 + int(deadline_min) * 60)
            else:
                p_deadline = 86399
            table.insert(int(p_id), address, p_deadline, city, state, p_zip, weight, note)
        except (ValueError, IndexError):
            try:
                p_id, address, city, state, p_zip, p_deadline, weight = line.split(',"')[0].split(',', 6)
                note = line.split(',"')[1].split('",')[0]
                if "EOD" not in p_deadline:
                    hour = p_deadline.split(":")[0]
                    minute = p_deadline.split(":")[1].split(" ")[0]
                    p_deadline = (int(hour) * 3600 + int(minute) * 60)
                else:
                    p_deadline = 86399
                table.insert(int(p_id), address, p_deadline, city, state, p_zip, weight, note)
            except (ValueError, IndexError):
                pass
    return table


# Produces graph object from distance file.
# Runs with complexity of O(N*M), where N is number if lines and
# M is number of addresses extracted from lines.
def load_city_csv(filename):
    graph = City()
    file = open(filename, "r")
    lines = file.readlines()
    address_lst = []
    count = 0
    for line in lines:
        if '","' in line:
            address_string = line.split('," ')[1].split("\n")[0]
            new_address = Address(address_string)
            graph.add_address(new_address)
            address_lst.append(new_address)
            count += 1
        elif "HUB" in line:
            address_string = line.split('", ')[1].split(",0")[0]
            new_address = Address(address_string)
            graph.add_address(new_address)
            address_lst.append(new_address)
            count += 1
        if line[0] == "(":
            try:
                # Reference last assigned new_address for current series of weights
                weights = line.split('",')[1].split(",,")[0].split(",", count)
                for address in address_lst:
                    graph.add_route(address_lst[count - 1], address, round(float(weights[address_lst.index(address)]),
                                                                           2))
            except IndexError:
                weights = line.split('",')[1].split(",", count)
                for address in address_lst:
                    graph.add_route(address_lst[count - 1], address, round(float(weights[address_lst.index(address)]),
                                                                           2))
        else:
            pass
    return graph
