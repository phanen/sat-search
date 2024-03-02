import time
import re


def grep(pattern, path):
    with open(path) as f:
        re.match(pattern, f.read())


def gen_timer():
    timetable = {}

    def tick(name):
        t = time.time()
        if name in timetable:
            timetable[name].append(t)
        else:
            timetable[name] = [t]
        return t

    def cost(name):
        return timetable[name][-1] - timetable[name][-2]

    return tick, cost


tick, cost = gen_timer()
