#%%

from datetime import datetime
import math
import csv
from typing import KeysView
import re
import json

##############################

def median(lst):
    n = len(lst)
    s = sorted(lst)
    return (sum(s[n//2-1:n//2+1])/2.0, s[n//2])[n % 2] if n else None

def tosecs(tm):
    x = re.split(r'\.',tm)
    if len(x) > 2:
        h = int(x[0])*3600
        m = int(x[1])*60
        s = int(x[2])
        return h+m+s
    else:
        m = int(x[0])*60
        s = int(x[1])
        return m+s

def fromsecs(seconds):
    h = seconds // 3600
    m = seconds % 3600 // 60
    s = seconds % 3600 % 60
    return f'{h}.{m}.{s}'

def corr_time(boat, seconds, handicaps):
    s = tosecs(seconds)
    h = int(handicaps[boat.upper()])
    return round((s/h)*1000)

def actual(time, tar):
    return tosecs(time)/(tar/1000)

def corrected_times(races, handicaps):
    corrected = {}
    for key, value in races.items():
        for sail, time in value.items():
            if key in list(corrected.keys()):
                corrected[key].update({sail: fromsecs(corr_time(key, time, handicaps))})
            else:
                corrected[key] = {sail: fromsecs(corr_time(key, time, handicaps))}
    return corrected

def actual_handicaps(races, target):
    actuals = {}
    for key, value in races.items():
        for sail, time in value.items():
            if key in list(actuals.keys()):
                actuals[key].update({sail: round(actual(time, target))})
            else:
                actuals[key] = {sail: round(actual(time, target))}
    return actuals

handicaps = {}

with open('handicaps.csv') as file:
    data = csv.reader(file)

    for k in data:
        if k [0] not in 'Class Name':
            handicaps.update({k[0]:k[1]})

races = {}

with open('Races.csv') as file:
    data = csv.reader(file)

    for k in data:
        if k[0] in list(races.keys()):
            races[k[0]].update({k[1]:k[2]})
        else:
            races[k[0]] = {k[1]:k[2]}

corrected_times = corrected_times(races, handicaps)

only_times = [[t for s,t in v.items()] for k,v in corrected_times.items()]

all_times = []
for group in only_times:
    for each in group:
        all_times.append(tosecs(each))

target = round(median(all_times))

print(actual_handicaps(races, target))
# %%
with open('corrected_times.json', 'w', encoding='utf-8') as f:
    json.dump(corrected_times, f, ensure_ascii=False, indent=4)
# %%
# %%
