#!/usr/bin/python
import sys, getopt, csv, datetime

DEVICES = {'Switch 1': 'b4:75:0e:0d:33:d5', 'Switch 2': 'b4:75:0e:0d:94:65',
           'Switch 3': '94:10:3e:2b:7a:55', 'Switch 4': '14:91:82:c8:6a:09',
           'Mini': '60:38:e0:ee:7c:e5', 'Insight': '14:91:82:24:dd:35',
           'WeMo Motion': 'ec:1a:59:f1:fb:21', 'NetCam': 'ec:1a:59:e4:fd:41',
           'NetCam Motion,smbeyer8': 'ec:1a:59:e4:fd:41', 'Motion': 'ec:1a:59:f1:fb:21'}
ACTIONS = {'Set state: On', 'Set state: Off', 'Motion Sensor: Detected'}
DEVICE_NAME = {'ec:1a:59:e4:fd:41': 'NetCam', 'b4:75:0e:0d:33:d5': 'Switch1',
               'b4:75:0e:0d:94:65': 'Switch2', '94:10:3e:2b:7a:55': 'Switch3',
               '14:91:82:c8:6a:09': 'Switch4', 'ec:1a:59:f1:fb:21': 'Motion',
               '14:91:82:24:dd:35': 'Insight', '60:38:e0:ee:7c:e5': 'Mini'}

TIME_FORMAT = '%Y-%m-%d %H:%M'


def main(argv):
    try:
        opts, args = getopt.getopt(argv, "hw:b:", ["help"])
    except getopt.GetoptError:
        print 'parse_log.py -w <wifi log file> -b <ble log file>'
        sys.exit(2)
    for opt, arg, in opts:
        if opt in ("-h", "--help"):
            print 'parse_log.py -w <wifi log file> -b <ble log file>'
            sys.exit()
        elif opt == '-w':
            print "arg:", arg
            file_name = arg
            parse_wifi_log(file_name)
        elif opt == '-b':
            file_name = arg
            parse_ble_log(file_name)


def parse_wifi_log(file_name):
    f = open(file_name, 'r')
    content = f.readlines()
    lines = []
    for line in content:
        a = stringbtwn(line, '[', 2, ']', 2).replace(',', '')
        b = stringbtwn(line, ']', 3, '-', 1).strip()
        c = stringbtwn(line, '-', 1, '\n', 1).strip()
        lines.append([a,b,c])
    
    events = []
    for line in lines:
        device = line[1]
        action = line[2]
        if (device in list(DEVICES.keys())) and (action in ACTIONS):
            date = line[0]
            date = datetime.datetime.strptime(date, "%m/%d/%Y %I:%M:%S %p").strftime(TIME_FORMAT)
            event = [date, DEVICE_NAME[DEVICES[device]], '1']
            if event not in events:
                events.append(event)

    file_date = datetime.datetime.strptime(date, TIME_FORMAT).strftime("%d%b%y")
    csv_file = "wifi_log_" + file_date + ".csv"
    with open(csv_file, 'w') as curr_file:
        for event in events:
            csv.writer(curr_file).writerow(event)
            
        
def findnth(string, char, n):
    parts=string.split(char, n)
    if len(parts)<=n:
        return -1
    return len(string)-len(parts[-1])-len(char)

def stringbtwn(string, char1, n1, char2, n2):
    a = findnth(string, char1, n1)
    b = findnth(string, char2, n2)
    if (a == -1) or (b == -1):
        return ""
    return string[a+1:b]


def parse_ble_log(file_name):
    with open(file_name, 'rb') as curr_file:
        reader = csv.reader(curr_file)
        contents = list(reader)

    lines = []
    for line in contents:
        date = line[0]
        date = datetime.datetime.strptime(date, "%m/%d/%Y %H:%M").strftime(TIME_FORMAT)
        device = line[1]
        value = line[2]
        lines.append([date,device,value])

    with open(file_name, 'w') as curr_file:
        for line in sorted(lines):
            csv.writer(curr_file).writerow(line)


# call main
if __name__ == "__main__":
	main(sys.argv[1:])
