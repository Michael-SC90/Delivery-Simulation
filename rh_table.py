# Michael Craig, 000955248


# requires table to be less than half-full to guarantee finding open bucket
def quad_hash(key, c1, c2, i, size):
    return (hash(key) + c1 * i + c2 * i * i) % size


# References assert object locations within table
class EmptyBucket:
    pass


class RobinHoodHashTable:
    def __init__(self, capacity=40):
        self.EMPTY_SINCE_START = EmptyBucket()
        self.EMPTY_AFTER_REMOVAL = EmptyBucket()
        self.table = [self.EMPTY_SINCE_START] * int(capacity // .5)
        self.C1 = 13
        self.C2 = 3

    # Places item into table
    def insert(self, p_id, address, deadline, city, state, p_zip, weight, status):
        probe_count = 0
        bucket = quad_hash(p_id, self.C1, self.C2, probe_count, len(self.table))
        while probe_count < len(self.table):
            if isinstance(self.table[bucket], EmptyBucket):
                self.table[bucket] = [(p_id, address, deadline, city, state, p_zip, weight, status), probe_count]
                return
            elif self.table[bucket][1] < probe_count:
                temp = self.table[bucket][0]
                self.table[bucket] = [(p_id, address, deadline, city, state, p_zip, weight, status), probe_count]
                self.insert(temp)
                return
            probe_count += 1
            bucket = quad_hash(p_id, self.C1, self.C2, probe_count, len(self.table))
        raise ValueError

    # Returns package from package table
    def get(self, p_id, address, deadline, city, state, p_zip, weight, status):
        count = 0
        bucket = quad_hash(p_id, self.C1, self.C2, count, len(self.table))
        while self.table[bucket] is not self.EMPTY_SINCE_START and count < len(self.table):
            if not isinstance(self.table[bucket], EmptyBucket):
                if self.table[bucket][0][0] == p_id:
                    return self.table[bucket][0]
            count += 1
            bucket = quad_hash(p_id, self.C1, self.C2, count, len(self.table))
        raise ValueError('Object does not exist: Key=%s' % str(p_id))

    # Returns list of all objects in table
    def get_all(self):
        lst = []
        for foo in self.table:
            if isinstance(foo, EmptyBucket):
                pass
            else:
                lst.append(foo[0])
        return lst

    # Removes package from package table
    # use when updating packages or removing them from location's package tables
    def remove(self, p_id, address, deadline, city, state, p_zip, weight, status):
        count = 0
        bucket = quad_hash(p_id, self.C1, self.C2, count, len(self.table))
        while self.table[bucket] is not self.EMPTY_SINCE_START and count < len(self.table):
            if not isinstance(self.table[bucket], EmptyBucket):
                if self.table[bucket][0][0] == p_id:
                    self.table[bucket] = self.EMPTY_AFTER_REMOVAL
                    return
            count += 1
            bucket = quad_hash(p_id, self.C1, self.C2, count, len(self.table))
        raise ValueError('Object does not exist: %s' % p_id)

    # Overload string for cleaner: print(hashtable)
    def __str__(self):
        s = "\n"
        index = 0
        for bucket in self.table:
            if isinstance(bucket, EmptyBucket):
                pass
                # if bucket is self.EMPTY_SINCE_START: value = 'E/S'
                # else: value = 'E/R'
            else:
                s += "\t------------------------------------------------------------------\n"
                s += "|{:2}:\n".format(index)
                value = str(bucket[0])
                s += '{:^6}|\n'.format(value)
                s += "\t------------------------------------------------------------------\n"
            index += 1
        return s


# Converts time (in seconds count for day) to 24-hour format
def convert_seconds_to_time(seconds):
    hour = seconds / 3600
    minute = int(seconds % 3600 / 60)
    if minute < 10:
        minute = "0%d" % minute
    return '%d:%s' % (hour, minute)
