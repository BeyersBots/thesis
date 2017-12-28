#!/usr/bin/python
import csv
import datetime
import sys, getopt

devices = {'Switch 1': 'b4:75:0e:0d:33:d5', 
           'Switch 2': 'b4:75:0e:0d:94:65', 
           'Switch 3': '94:10:3e:2b:7a:55', 
           'Switch 4': '14:91:82:24:dd:35', 
           'Mini': '60:38:e0:ee:7c:e5', 
           'Insight': '14:91:82:24:dd:35', 
           'Motion': 'ec:1a:59:f1:fb:21', 
           'NetCam': 'ec:1a:59:e4:fd:41'}
actions = {'Set state: On', 'Set state: Off', 'Motion Sensor: Detected'}

def main(argv):
    try:
        opts, args = getopt.getopt(argv, "hf:", ["help"])
    except getopt.GetoptError:
        print 'parse_log.py -f <pcap file>'
        sys.exit(2)
    for opt, arg, in opts:
        if opt in ("-h", "--help"):
            print 'parse_log.py -f <pcap file>'
            sys.exit()
        elif opt == '-f':
            file_name = arg
            
    f = open(file_name, 'r')
    content = f.readlines()
    lines = []
    for line in content:
        a = stringbtwn(line, '[', 2, ']', 2).replace(',', '')
        b = stringbtwn(line, ']', 3, '-', 1).strip()
        c = stringbtwn(line, '-', 1, '\n', 1).strip()
        lines.append([a,b,c])
    
    events = []
    for x in lines:
        for k, v in devices.items():
            if (k == x[1]):
                for act in actions:
                    if (act == x[2]):
                        events.append([x[0], v, x[2]])
    
    csv_file = file_name.replace('.txt', '.csv')
    with open(csv_file, 'a') as curr_file:
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


# call main
if __name__ == "__main__":
	main(sys.argv[1:])