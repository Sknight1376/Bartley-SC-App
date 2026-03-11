from handicaps.conversions import time_conversions

class maths:


    def median(competitor_list):
        list_length = len(competitor_list)
        sorted_list = sorted(competitor_list)
        return (sum(sorted_list[list_length//2-1:list_length//2+1])/2.0, sorted_list[list_length//2])[list_length % 2] if list_length else None

class handicap_calculations:

    def corrected_time(time, handicap):
        s = time_conversions.tosecs(time)
        return time_conversions.fromsecs(round((s*1000)/handicap))

    def actual_time(time, target):
        s = time_conversions.tosecs(time)

        return round(s/(target/1000))

    

class compare_to_median:

    def __init__(self, times):

        list = [time_conversions.tosecs(time['corrected_time']) for time in times]
        self.median = maths.median(list)
        
    def comparison(self, corrected_times):

        
        for row in corrected_times:

            comparable_PY = handicap_calculations.actual_time(row['Time'], self.median)

            row['adjusted_handicap'] = comparable_PY

        return corrected_times

            
        