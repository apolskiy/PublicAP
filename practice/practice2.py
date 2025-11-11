"""Practicing regular expressions in Python"""
#Aleksandr Polskiy
import re
def show_time_of_pid(line):
    """show_time_of_pid function returns the time and pid from a log line"""
    pattern = r"^(\w{3})\s+(\d{1,2})\s+(\d{2}:\d{2}:\d{2}).*?\[(\d+)\]"
    result = re.split(pattern, line)
    separator=" "
    #final_result = result.group(1)+"pid:"+result.group(2)
    return result[1]+separator+result[2]+separator+result[3]+separator+"pid:"+result[4]
# Jul 6 14:01:23 pid:29440
print(show_time_of_pid("Jul 6 14:01:23 computer.name CRON[29440]: USER (good_user)"))

# Jul 6 14:02:08 pid:29187
print(show_time_of_pid("Jul 6 14:02:08 computer.name jam_tag=psim[29187]: (UUID:006)"))

# Jul 6 14:02:09 pid:29187
print(show_time_of_pid("Jul 6 14:02:09 computer.name jam_tag=psim[29187]: (UUID:007)"))

# Jul 6 14:03:01 pid:29440
print(show_time_of_pid("Jul 6 14:03:01 computer.name CRON[29440]: USER (naughty_user)"))

# Jul 6 14:03:40 pid:29807
print(show_time_of_pid("Jul 6 14:03:40 computer.name cacheclient[29807]: "
                       "start syncing from \"0xDEADBEEF\""))

# Jul 6 14:03:40 pid:29807
print(show_time_of_pid("Jul 6 14:03:40 computer.name cacheclient[29807]: "
                       "start syncing from \"0xDEADBEEF\""))

# Jul 6 14:04:01 pid:29440
print(show_time_of_pid("Jul 6 14:04:01 computer.name CRON[29440]: USER (naughty_user)"))

# Jul 6 14:05:01 pid:29440
print(show_time_of_pid("Jul 6 14:05:01 computer.name CRON[29440]: "
                       "USER (naughty_user)"))
