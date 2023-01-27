import re


class time_conversions:

        def tosecs(time):
            split_time = re.split(r'\.',str(time))
            if len(split_time) > 2:
                h = int(split_time[0])*3600
                m = int(split_time[1])*60
                s = int(split_time[2])
                return h+m+s
            else:
                m = int(split_time[0])*60
                s = int(split_time[1])
                return m+s

        def fromsecs(seconds):
            h = seconds // 3600
            m = seconds % 3600 // 60
            s = seconds % 3600 % 60
            return f'{h}.{m}.{s}'