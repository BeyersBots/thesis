#!/usr/bin/python
import sys, getopt, csv, datetime

BLE_DEVICES = {'Eve Energy 556E', 'Eve Room 4A04', 'PLAYBULB', 'Instant Pot Smart',
               'Eve Motion 31A7', 'Eve Weather 943D', 'Gunbox', 'BLELock', '00000b67', 'Eve Door 91B3'}

def main(argv):
    ble_log_file_name = ""
    wifi_log_file_name = ""
    ble_events_file_name = ""
    wifi_events_file_name = ""

    try:
        opts, args = getopt.getopt(argv, "ha:b:c:d:", ["help"])
    except getopt.GetoptError:
        print 'results.py -a <ble_log.csv> -b <wifi_log> -c <ble_vents.csv> -d <wifi_events'
        sys.exit(2)
    for opt, arg, in opts:
        if opt in ("-h", "--help"):
            print "Help:"
            print 'results.py -a <ble_log.csv> -b <wifi_log> -c <ble_vents.csv> -d <wifi_events'
            sys.exit()
        elif opt == '-a':
            ble_log_file_name = arg
        elif opt == '-b':
            wifi_log_file_name = arg
        elif opt == '-c':
            ble_events_file_name = arg
        elif opt == '-d':
            wifi_events_file_name = arg

    total_true_pos = 0
    total_false_pos = 0
    total_false_neg = 0
    total_num_events = 0
    total_num_events_id = 0


    date = ""
    results_file_name = ""
    ble_logs = []
    ble_events = []
    wifi_logs = []
    wifi_events = []

    ble_csv_entries = []
    wifi_csv_entries = []
    total_csv_entries = []
    total_true_pos_list = []
    total_false_pos_list = []
    total_false_neg_list = []

    if (ble_log_file_name != "") and (ble_events_file_name != ""):
        with open(ble_log_file_name, 'rb') as curr_file:
            reader = csv.reader(curr_file)
            ble_logs = list(reader)

        with open(ble_events_file_name, 'rb') as curr_file:
            reader = csv.reader(curr_file)
            ble_events = list(reader)

        pkt_time = ble_logs[0][0]

        date = datetime.datetime.strptime(pkt_time, '%Y-%m-%d %H:%M').strftime('%d%b%y')

        results_file_name = "results_" + date + ".csv"

        ble_csv_entries.append(["BLE Results:",""])

        true_pos, false_pos, false_neg, num_events, num_events_id, csv_entries, \
            true_pos_list, false_pos_list, false_neg_list = calculate_results(ble_logs, ble_events)

        total_true_pos += true_pos
        total_false_pos += false_pos
        total_false_neg += false_neg
        total_num_events += num_events
        total_num_events_id += num_events_id
        ble_csv_entries = ble_csv_entries + csv_entries
        total_true_pos_list = total_true_pos_list + true_pos_list
        total_false_pos_list = total_false_pos_list + false_pos_list
        total_false_neg_list = total_false_neg_list + false_neg_list

    if (wifi_log_file_name != "") and (wifi_events_file_name != ""):
        with open(wifi_log_file_name, 'rb') as curr_file:
            reader = csv.reader(curr_file)
            wifi_logs = list(reader)

        with open(wifi_events_file_name, 'rb') as curr_file:
            reader = csv.reader(curr_file)
            wifi_events = list(reader)

        pkt_time = wifi_logs[0][0]

        date = datetime.datetime.strptime(pkt_time, '%Y-%m-%d %H:%M').strftime('%d%b%y')

        results_file_name = "results_" + date + ".csv"

        wifi_csv_entries.append(["Wi-Fi Results:",""])

        true_pos, false_pos, false_neg, num_events, num_events_id, csv_entries, \
            true_pos_list, false_pos_list, false_neg_list = calculate_results(wifi_logs, wifi_events)

        total_true_pos += true_pos
        total_false_pos += false_pos
        total_false_neg += false_neg
        total_num_events += num_events
        total_num_events_id += num_events_id
        wifi_csv_entries = wifi_csv_entries + csv_entries
        total_true_pos_list = total_true_pos_list + true_pos_list
        total_false_pos_list = total_false_pos_list + false_pos_list
        total_false_neg_list = total_false_neg_list + false_neg_list

    total_csv_entries.append(["Total Results:", ""])
    total_csv_entries.append(["True Positives", total_true_pos])
    total_csv_entries.append(["False Positives", total_false_pos])
    total_csv_entries.append(["False Negatives", total_false_neg])
    total_csv_entries.append(["Number of events logged", total_num_events])
    total_csv_entries.append(["Number of events identified", total_num_events_id])
    total_csv_entries.append(["Event identification success rate",
                        float(total_true_pos) / float(total_num_events) * 100])
    total_csv_entries.append(["Event identification false positive rate",
                        float(total_false_pos) / float(total_num_events_id) * 100])
    total_csv_entries.append(["Event identification false negative rate",
                        float(total_false_neg) / float(total_num_events) * 100])

    if(ble_log_file_name != "") and (wifi_log_file_name != ""):
        combined_csv_entries = [x+y+z for x, y, z in zip (ble_csv_entries, wifi_csv_entries, total_csv_entries)]
    elif ble_log_file_name == "":
        combined_csv_entries = wifi_csv_entries
    elif wifi_log_file_name == "":
        combined_csv_entries = ble_csv_entries

    with open(results_file_name, 'w') as curr_file:
        for line in combined_csv_entries:
            csv.writer(curr_file).writerow(line)

        csv.writer(curr_file).writerow(["True Positives:"])
        for line in total_true_pos_list:
            csv.writer(curr_file).writerow(line)

        csv.writer(curr_file).writerow(["False Positives:"])
        for line in total_false_pos_list:
            csv.writer(curr_file).writerow(line)

        csv.writer(curr_file).writerow(["False Negatives:"])
        for line in total_false_neg_list:
            csv.writer(curr_file).writerow(line)

    combined_logs_file = "logs_" + date + ".csv"
    combined_logs = ble_logs + wifi_logs
    combined_events_file = "events_" + date + ".csv"
    combined_events = ble_events + wifi_events

    with open(combined_logs_file, 'w') as curr_file:
        for line in combined_logs:
            csv.writer(curr_file).writerow(line)

    with open(combined_events_file, 'w') as curr_file:
        for line in combined_events:
            csv.writer(curr_file).writerow(line)


def calculate_results(logs, events):
    true_pos = 0
    false_pos = 0
    false_neg = 0
    true_pos_list =[]
    false_pos_list = []
    false_neg_list = []

    for line in logs:
        if line in events:
            true_pos += 1
            true_pos_list.append(line)
        if line not in events:
            if line[1] == "NetCam" or line[1] == "Motion" or line[1] in BLE_DEVICES:
                if check_motion_event(line, events) != False:
                    true_pos += 1
                    true_pos_list.append(line)
                else:
                    false_neg += 1
                    false_neg_list.append(line)
            else:
                false_neg += 1
                false_neg_list.append(line)

    for line in events:
        if line not in logs:
            if line[1] == "NetCam" or line[1] == "Motion" or line[1] in BLE_DEVICES:
                time = check_motion_event(line, logs)
                if time == False:
                    false_pos += 1
                    false_pos_list.append(line)
                else:
                    line[0] = time
            else:
                false_pos += 1
                false_pos_list.append(line)

    num_events = len(logs)
    num_events_id = len(events)
    csv_entries = []

    csv_entries.append(["True Positives", true_pos])
    csv_entries.append(["False Positives", false_pos])
    csv_entries.append(["False Negatives", false_neg])
    csv_entries.append(["Number of events logged", num_events])
    csv_entries.append(["Number of events identified", num_events_id])
    csv_entries.append(["Event identification success rate",
                                    float(true_pos)/float(num_events)*100])
    csv_entries.append(["Event identification false positive rate",
                                    float(false_pos) / float(num_events_id)*100])
    csv_entries.append(["Event identification false negative rate",
                                    float(false_neg) / float(num_events)*100])
    csv_entries.append(["True positives:"])

    return true_pos, false_pos, false_neg, num_events, num_events_id, csv_entries, \
           true_pos_list, false_pos_list, false_neg_list


# Because motion events take time to send, if one was sent the minute before then ignore a potential new event
# could cause us to miss two events in a row, but most motion devices have at least a 60 second no motion sensor
# before restarting, so this should not be an issue.
def check_motion_event(line, check_list):
    pkt_time = line[0]
    device = line[1]
    date = datetime.datetime.strptime(pkt_time, '%Y-%m-%d %H:%M')
    date_minus_1 = date - datetime.timedelta(minutes=1)
    date_minus_1 = date_minus_1.strftime('%Y-%m-%d %H:%M')
    date_plus_1 = date + datetime.timedelta(minutes=1)
    date_plus_1 = date_plus_1.strftime('%Y-%m-%d %H:%M')
    if [date_minus_1, device, '1'] in check_list:
        print "got minus 1"
        return date_minus_1
    elif [date_plus_1, device, '1'] in check_list:
        print "got plus 1"
        return date_plus_1
    else:
        return False


# call main
if __name__ == "__main__":
    main(sys.argv[1:])