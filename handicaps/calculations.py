from handicaps.conversions import time_conversions

class maths:


    def median(competitor_list):
        list_length = len(competitor_list)
        sorted_list = sorted(competitor_list)
        return (sum(sorted_list[list_length//2-1:list_length//2+1])/2.0, sorted_list[list_length//2])[list_length % 2] if list_length else None

class handicap_calculations:

    def corrected_time(boat, time, handicap):
        s = time_conversions.tosecs(time)
        return time_conversions.fromsecs(round((s/handicap)*1000))

    def actual_time(time, target):
        return time_conversions.tosecs(time)/(target/1000)