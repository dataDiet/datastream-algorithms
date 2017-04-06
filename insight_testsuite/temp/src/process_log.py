import datetime
import operator
import sys
import re
import os
from collections import deque


def processLog(input_path, hosts_path, resources_path, hours_path, blocked_path, scrape_path=None):
    """
    Main section of script to process input log file.
    :param input_path:
    :param hosts_path:
    :param resources_path:
    :param hours_path:
    :param blocked_path:
    :param scrape_path:
    :return: (void)

    Main data items are named after the features that they correspond to.
     f1 - frequent ip addresses feature
        dictionary with frequencies corresponding to ip addreses
     f2 - heavy bandwidth site feature
        dictionary with frequencies corresponding to datetime stamps
     f3 - frequent 60 minute windows feature
     f4_potential - dictionary of potential ip addresses to send to block list based on 20 second window.
     f4_blocked - dictionary of blocked ip addresses to log data from based on 5 minute windows
     f5 - based on optional ip bandwidth volume, similar to feature 2 in operation

     output of data is written to log_output based files hosts.txt, hours.txt, resources.txt, blocked.txt, (optional) scraper.txt
    """
    f1 = {}
    f2 = {}
    f3 = deque()
    f4_potential = {}
    f4_blocked = {}
    f4_list = deque()
    f5 = {}

    ln = 0

    with open(input_path, 'r') as streamFile:
        for line in streamFile:
            ln += 1
            m = re.match(r"([^ ]+) .*\[([^\]]+)\] +\"[A-Z]+ ([^ \"]+).*\" +(\d+) +([-\d]+)", line)
            g = m.groups()
            ip = g[0]
            dt = datetime.datetime.strptime(g[1], "%d/%b/%Y:%H:%M:%S %z")
            resource = g[2]
            reply=g[3]
            if g[4] == '-':
                bytes_delivered = 0
            else:
                bytes_delivered = int(g[4])

            # Feature 1
            f1[ip] = f1.get(ip, 0)+1

            # Feature 2
            f2[resource] = f2.get(resource, 0)+bytes_delivered

            # Feature 3
            if ln == 1 or f3[-1][0] != dt:
                f3.append([dt,1])
            else:
                f3[-1][1] += 1
            # Feature 4
            if ip in f4_blocked:
                if dt <= f4_blocked[ip]+datetime.timedelta(minutes=5):
                    f4_list.append(line)
                    continue
                else:
                    del f4_blocked[ip]
            if reply == '401':
                if ip in f4_potential:
                    stat = f4_potential[ip]
                    if dt > stat[0]+datetime.timedelta(seconds=20):
                        stat[0] = dt
                        stat[1] = 1
                    else:
                        stat[1] += 1
                    if stat[1] == 3:
                        del f4_potential[ip]
                        f4_blocked[ip] = dt
                else:
                    f4_potential[ip] = [dt, 1]
            if reply == '200' and\
                    (ip in f4_potential) and\
                    (dt <= f4_potential[ip][0]+datetime.timedelta(seconds=20)):
                    del f4_potential[ip]

            # Feature 5
            if scrape_path:
                f5[ip] = f5.get(ip, 0)+bytes_delivered


    # Write data to files
    writeDict(hosts_path, f1, 'k,v')
    writeDict(resources_path, f2, 'k')
    writeHours(hours_path, computeHours(f3))
    writeBlocked(blocked_path, f4_list)
    if scrape_path:
        writeDict(scrape_path, f5, 'k,v')

def computeHours(second_list):
    """
    This function determines the hours of operation during which traffic is heaviest.

    left - time window boundary based on the earliest datetime value given in the input.
    right - time window boundary based on 60 minutes from left
    The function first sums all numbers of accesses inside the window frame while not exceeding the length of the input
    The function then shifts the time window by one second and determines accesses that fall newly inside the window and newly
     outside the window adjusting the summation (sum_of_accesses accordingly)
    index_right - right window boundary for actual frequency input
    index_left - left window boundary for actual frequency input
    :param second_list: list of datetime values with frequencies accessed given
    :return: sorted list of top 10 frequently accessed datetime listed in descending order
    """
    top_10_list = []
    left = second_list[0][0]
    right = second_list[0][0]+datetime.timedelta(hours=1)
    sum_of_accesses = 0
    index_right = 0
    index_left = 0

    while index_right < len(second_list) and second_list[index_right][0] <= right:
            sum_of_accesses += second_list[index_right][1]
            index_right += 1
    top_10_list.append((sum_of_accesses, left))
    while left <= second_list[-1][0]:
        left += datetime.timedelta(seconds=1)
        right += datetime.timedelta(seconds=1)
        if index_right < len(second_list) and second_list[index_right][0] <= right:
            sum_of_accesses += second_list[index_right][1]
            index_right += 1
        if index_left < len(second_list) and second_list[index_left][0] < left:
            sum_of_accesses = sum_of_accesses-second_list[index_left][1]
            index_left += 1
        top_10_list.append((sum_of_accesses, left))
    return sorted(top_10_list, key=operator.itemgetter(0), reverse=True)[0:min(10, len(top_10_list))]


def writeDict(path, dict_to_write, opt):
    """
    Function for outputting results of features 1,2, and 5.
    :param path:
    :param dict_to_write:
    :param opt:
    :return:
    """
    with open(path, 'w') as file_handle:
        for key, value in sorted(dict_to_write.items(), key=operator.itemgetter(1), reverse=True)[0:10]:
                if opt == 'k,v':
                    file_handle.write(','.join([str(key), str(value)])+'\n')
                elif opt == 'k':
                    file_handle.write(key+'\n')
    file_handle.close()


def writeHours(path, hours_list):
    """
    Function for outputting results for feature 3.
    :param path:
    :param hours_list:
    :return:
    """
    with open(path, 'w') as file_handle:
        for cnt, dt in hours_list:
            file_handle.write(dt.strftime("%d/%b/%Y:%H:%M:%S %z")+','+str(cnt)+'\n')
    file_handle.close()


def writeBlocked(path, f4_list):
    """
    Function for outputting results for feature 4.
    :param path:
    :param f4_list:
    :return:
    """
    with open(path, 'w') as file_handle:
        for line in f4_list:
            file_handle.write(line)
    file_handle.close()

if __name__ == "__main__":
    """
    Take file inputs and first remove non utf-8 characters from input log file.
    Then proceed to process that log file.
    """
    input_file = sys.argv[1]
    os.system("iconv -f utf-8 -t utf-8 -c %s > ./cleaned_file.txt" % input_file)
    input_file = 'cleaned_file.txt'
    output_hosts = sys.argv[2]
    output_resources = sys.argv[4]
    output_hours = sys.argv[3]
    output_blocked = sys.argv[5]
    if len(sys.argv) == 7:
        output_scrape = sys.argv[6]
        processLog(input_file, output_hosts, output_resources, output_hours, output_blocked, output_scrape)
    else:
        processLog(input_file, output_hosts, output_resources, output_hours, output_blocked)
    os.remove(input_file)

