"""This script contains three functions to help manage
processing network device statuses and collect downtime information"""
import unittest
def get_off_time_for_device(device:list[list[int]]) -> list[list[int]]:
    """This function takes a list of device timestamps and network statuses
    e.g. [5,0] time stamp device off, [7,1] timestamp device off
    process it and outputs device off time ranges"""
    off_times = []
    current_time=device[0][0]
    current_state=device[0][1]

    for entry in device[1:]:
        previous_time=current_time
        previous_state=current_state
        current_time=entry[0]
        current_state=entry[1]
        if current_state == 0 and previous_state == 1:
            off_times.append([previous_time,current_time])
    return off_times

def matching_device_off_times(off_times:list[list[list[int]]]) -> list[list[int]]:

    duplicate_intervals=[]
    flat_intervals = [interval for device in off_times for interval in device]

    flat_intervals.sort()
    for items in range(len(flat_intervals)-1):
        current_item=flat_intervals[items]
        next_item=flat_intervals[items+1]
        if current_item == next_item:
            if not duplicate_intervals or duplicate_intervals[-1]!=current_item:
                duplicate_intervals.append(current_item)


    return duplicate_intervals




def overlapping_off_times(off_times:list[list[list[int]]]) -> list[list[int]]:
    overlapping_intervals  = []
    flat_intervals = [interval for device in off_times for interval in device]

    # Sort primarily by start time, secondarily by end time
    flat_intervals.sort(key=lambda x: (x[0], x[1]))

    n = len(flat_intervals)
    for index in range(n):
        for index2 in range(index + 1, n):
            start1, end1 = flat_intervals[index]
            start2, end2 = flat_intervals[index2]

            # Since intervals are sorted by start time, if start2 >= end1,
            # no subsequent interval will overlap with interval i
            if start2 >= end1:
                break

            # Calculate intersection
            overlap_start = max(start1, start2)
            overlap_end = min(end1, end2)

            # Ensure valid non-zero duration overlap
            if overlap_start < overlap_end:
                overlap = [overlap_start, overlap_end]
                if overlap not in overlapping_intervals:
                    overlapping_intervals.append(overlap)

    return overlapping_intervals

class TestDevices(unittest.TestCase):
    def test_single_device(self):
        """This test, tests the get_off_time_for_device function
         to determine if off time intervals for the device is calculated
         correctly"""
        data=[[5,1],[7,0],[30,1],[32,0],[36,1]]
        expected = [[5, 7], [30,32]]
        self.assertEqual(get_off_time_for_device(data), expected)

    def test_multiple_devices(self):
        """This function tests the matching_device_off_times function
        taking input of list of integer off intervals for multiple devices and
        figuring out which intervals between devices match, outputting only intervals
        that occur more than once"""
        data=[[[5, 7], [30,32]],[[6,8],[16,20],[22,25],[30,32],[40,41]],[[5,7],[11,12],[16,18],[22,25],[51,60]]]
        expected=[[5,7],[22,25],[30,32]]
        self.assertEqual(matching_device_off_times(data), expected)

    def test_multiple_devices_overlapping(self):
        """This function tests the overlapping_off_times function
        taking input of list of integer off intervals for multiple devices and
        outputting only intervals which overlap"""
        data = [
            [[5, 7], [30, 32]],
            [[6, 8], [16, 20], [22, 25], [30, 32], [40, 41]],
            [[5, 7], [11, 12], [16, 18], [22, 25], [51, 60]]
        ]
        # Includes partial overlaps like [5,7] & [6,8] -> [6,7]
        # as well as nested overlaps like [16,20] & [16,18] -> [16,18]
        expected = [[5, 7], [6, 7], [16, 18], [22, 25], [30, 32]]
        self.assertEqual(overlapping_off_times(data), expected)

if __name__ == "__main__":
    unittest.main()