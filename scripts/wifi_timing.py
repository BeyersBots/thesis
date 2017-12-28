#!/usr/bin/python
# Prerequisites: pyshark
# Pyshark can be downloaded from https://github.com/KimiNewt/pyshark or via pip install pyshark.
import helpers
import pyshark
import matplotlib.dates as m_dates
import sys, getopt, csv, os, datetime, time, logging

#######################################################################################################################
# GLOBAL VARIABLES
# defined MAC addresses
ROUTER = 'ec:4f:82:73:d1:1c'
RASPI = 'b8:27:eb:09:1a:81'

# list of devices on the Wi-Fi network to include all IoT devices, router, and Raspberry Pi
WIFI_DEVICES = {'b8:27:eb:09:1a:81', '14:91:82:24:dd:35', '60:38:e0:ee:7c:e5', 'a0:18:28:33:34:f8', '08:66:98:ed:1e:19',
                'b4:75:0e:0d:33:d5', 'b4:75:0e:0d:94:65', '94:10:3e:2b:7a:55', '14:91:82:c8:6a:09', 'ec:1a:59:f1:fb:21',
                'ec:1a:59:e4:fd:41', 'ec:4f:82:73:d1:1c'}
# 'ec:4f:82:73:d1:1a', '30:8c:fb:3a:1a:ad', '84:20:96:22:ef:c1'}

# list of devices that are assumed to be IoT devices. This is ascertained via the OUI results
IOT_DEVICES = {'14:91:82:24:dd:35', '60:38:e0:ee:7c:e5', 'b4:75:0e:0d:33:d5', 'b4:75:0e:0d:94:65', '94:10:3e:2b:7a:55',
               '14:91:82:c8:6a:09', 'ec:1a:59:f1:fb:21', 'ec:1a:59:e4:fd:41'}
# '30:8c:fb:3a:1a:ad', '84:20:96:22:ef:c1'}

# list of devices and associated IDs used for the network mapper
DEVICE_ID = {'ec:4f:82:73:d1:1c': 's01', 'ec:1a:59:e4:fd:41': 's02', 'b4:75:0e:0d:33:d5': 's03',
             'b4:75:0e:0d:94:65': 's04', '94:10:3e:2b:7a:55': 's05', '14:91:82:c8:6a:09': 's06',
             'ec:1a:59:f1:fb:21': 's07', '14:91:82:24:dd:35': 's08', '60:38:e0:ee:7c:e5': 's09',
             'b8:27:eb:09:1a:81': 's10', 'a0:18:28:33:34:f8': 's11', '08:66:98:ed:1e:19': 's12'}
# '30:8c:fb:3a:1a:ad': 's13', '84:20:96:22:ef:c1': 's14'}

DEVICE_NAME = {'ec:4f:82:73:d1:1c': 'Router', 'ec:1a:59:e4:fd:41': 'NetCam', 'b4:75:0e:0d:33:d5': 'Switch1',
               'b4:75:0e:0d:94:65': 'Switch2', '94:10:3e:2b:7a:55': 'Switch3', '14:91:82:c8:6a:09': 'Switch4',
               'ec:1a:59:f1:fb:21': 'Motion', '14:91:82:24:dd:35': 'Insight', '60:38:e0:ee:7c:e5': 'Mini',
               'b8:27:eb:09:1a:81': 'Pi', 'a0:18:28:33:34:f8': 'iPhone', '08:66:98:ed:1e:19': 'AppleTV'}

# directory to store and read csv files for devices
SRC_DIR = './Source/'
DST_DIR = './Destination/'
TIMING_PKT_NUMBER = 25000
MAC_TRACK_TIME = 300
path_name = os.getcwd()
DATE = path_name[path_name.rindex('/')+1:]
PROC_TIME = "wifi_processing_time_" + DATE + ".csv"
#######################################################################################################################

logging.basicConfig(stream=sys.stderr, level=logging.INFO)


def main(argv):
    """
    Main function that calls appropriate functions depending on operation mode selected by user input

    The main function is called in four modes:
    wifi.py -h/--help: Provides usage.
    wifi.py -p <pcap file>: Begins preprocessing on the file capture provided and tracks devices.
    wifi.py -t: Provides graphs to help training classifier. Preprocessing mode must be ran first.
    wifi.py -c: Classifies devices, identifies events, and maps the network.
    """
    try:
        opts, args = getopt.getopt(argv, "hp:tc", ["help"])
    except getopt.GetoptError:
        print 'usage error'
        print 'for preprocessing or tracking: wifi.py -p <pcap file>'
        print 'for training: wifi.py -t'
        print 'for classification and network mapping: wifi.py -c'
        print 'exiting'
        sys.exit(2)
    for opt, arg, in opts:
        if opt in ("-h", "--help"):
            print 'for preprocessing or tracking: wifi.py -p <pcap file>'
            print 'for training: wifi.py -t'
            print 'for classification and network mapping: wifi.py -c'
            sys.exit()

        # preprocessing unit
        elif opt == '-p':
            start_time = time.time()
            preprocessor(arg)
            print "Finish preprocessor:", time.time() - start_time

        # training unit for classifier
        elif opt == '-t':
            start_time = time.time()
            trainer()
            print "Finish trainer:", time.time() - start_time

        # classifier unit
        elif opt == '-c':
            start_time = time.time()
            classifier()
            print "Finish classifier:", time.time() - start_time

#######################################################################################################################
# PREPROCESSOR UNIT
#######################################################################################################################


def preprocessor(file_name):
    """
    Unit that parses each packet in  file capture and stores packets into CSV files. Also provides device tracking
    information.

    Parses capture file and stores 4-tuples in the form [time, frame size, source, destination]
    for each packet into two files for each device. Device source files include 4-tuples in which
    every tuple has the device as the source MAC address. Device destination files include
    4-tuples in which every tuplehas the device as the destination MAC address. Also provides a
    CSV file with device addresses, arrival time, and departure time.

    Parameters
    ----------
    file_name: (string) File name of capture provided by user.

    Returns
    ----------

    """

    helpers.delete_file(PROC_TIME)
    pt_file = open(PROC_TIME, 'w')
    csv.writer(pt_file).writerow(["Unit", "Total Packets Processed", "Total Process Time", "Average Process Time"])
    pt_file.close()
    pkt_cntr = 0
    total_time_preproc = 0
    total_time_mac = 0

    total_time_start = time.time()
    # initialize dictionaries to store file object for each device
    tgt_files_by_src = {}
    tgt_files_by_dst = {}
    # initialize dictionary to store tracking information for each device
    macs = {}

    # initialize file names
    cap = pyshark.FileCapture(file_name)
    mac_track_file = "mac_track_" + DATE + ".csv"
    helpers.delete_file(mac_track_file)
    helpers.init_dirs()

    # obtain time for first packet
    prev_pkt_time = cap[0].frame_info.time_epoch

    # open target files to write output to
    for device in WIFI_DEVICES:
        tgt_files_by_src[device] = open(SRC_DIR + device.replace(':', '.') + ".csv", 'a')
        tgt_files_by_dst[device] = open(DST_DIR + device.replace(':', '.') + ".csv", 'a')
    tgt_mac_track_file = open(mac_track_file, 'a')

    # iterate through each packet in the capture, store tuples to files, and
    # track when devices are on the network
    for pkt in cap:
        pkt_cntr += 1

        # check if device is gone for more than five minutes and set time as previous time
        time_start = time.time()
        prev_pkt_time, macs = mac_track(pkt, tgt_mac_track_file, prev_pkt_time, macs)
        total_time_mac += (time.time() - time_start)

        time_start = time.time()
        if pkt.highest_layer == 'DATA':
            parse_pkt(pkt, tgt_files_by_src, tgt_files_by_dst)
            total_time_preproc += time.time() - time_start

    time_start = time.time()
    # using the last packet in the capture, check which devices are still on the network
    mac_track_final(tgt_mac_track_file, prev_pkt_time, macs)
    total_time_mac += time.time() - time_start

    total_time = time.time() - total_time_start


    # close files
    for k, v in tgt_files_by_src.iteritems():
        v.close()
    for k, v in tgt_files_by_dst.iteritems():
        v.close()
    tgt_mac_track_file.close()


    classifier()
    final_time = time.time()

    normalized_total_time = (TIMING_PKT_NUMBER * total_time) / pkt_cntr
    normalized_mac_time = (TIMING_PKT_NUMBER * (total_time - total_time_preproc)) / pkt_cntr
    normalized_preproc_time = (TIMING_PKT_NUMBER * (total_time - total_time_mac)) / pkt_cntr

    print "Total number of packets preprocessor: ", pkt_cntr
    print "Total time preprocessor: ", total_time
    print "Normalized total preprocessor time per 25000 packets: ", normalized_total_time
    print "Total time mac track: ", total_time_mac
    print "Normalized time mac track: ", normalized_mac_time
    print "Total time preproc: ", total_time_preproc
    print "Normalizedtime preproc: ", normalized_preproc_time
    pt_file = open(PROC_TIME, 'a')
    csv.writer(pt_file).writerow(["MAC Track+Preproc", pkt_cntr, total_time, normalized_total_time])
    csv.writer(pt_file).writerow(["MAC Track", pkt_cntr, total_time_mac, normalized_mac_time])
    csv.writer(pt_file).writerow(["Preprocesser", pkt_cntr, total_time_preproc, normalized_preproc_time])
    csv.writer(pt_file).writerow(["Start and finish time", total_time_start, final_time, final_time-total_time_start])
    pt_file.close()


def parse_pkt(pkt, tgt_files_by_src, tgt_files_by_dst):
    """
    Parses each 802.11 Data packet within the provided capture file.

    Extracts the time, frame size, source, and destination of each 802.11 Data packet. Stores
    the resulting 4-tuple into two files depending on the source and destination of the packet.

    Parameters
    ----------
    pkt: (pyshark packet) Pyshark packet object containing packet information from capture.
    tgt_files_by_src: (file object) Uses the device address as keys and file objects as values.
        Every packet with a source address corresponding to the key will be appended to the file object.
    tgt_files_by_dst: (dictionary) Uses the device address as keys and file objects as values.
        Every packet with a destination address corresponding to the key will be appended to the file object.

    Returns
    ----------
    void
    """
    try:
        pkt_dst = pkt.wlan.da
        pkt_src = pkt.wlan.sa
        if (pkt_src in WIFI_DEVICES) and (pkt_dst in WIFI_DEVICES):
            pkt_len = pkt.length
            pkt_time = helpers.pretty_time(pkt.frame_info.time_epoch)
            file_input = [pkt_time, pkt_len, pkt_src, pkt_dst]
            csv.writer(tgt_files_by_src[pkt_src]).writerow(file_input)
            csv.writer(tgt_files_by_dst[pkt_dst]).writerow(file_input)

    except AttributeError:
        # ignore corrupt packet
        print "ignored: ", pkt.number


def mac_track(pkt, tgt_mac_track_file, prev_pkt_time, macs):
    """
    Records devices with no network traffic for more than five minutes.

    Compares the time of each packet with the last time a device sent a message and, if greater tha five minutes,
    marks the device as no longer present and stores the device MAC address, first time the device sent a packet
    (arrival time), and last time the device sent a packet (departure time) in a csv file.

    Parameters
    ----------
    pkt: (pyshark packet) Pyshark packet object containing packet information from capture.
    tgt_mac_track_file: (file object) CSV file to append tracking data.
    prev_pkt_time: (frame_info.time_epoch) Time value obtained from the previous packet.
    macs: (dictionary) Uses the device address as keys and a 2-tuple containing the arrival time and departure time
        for each device.

    Returns
    ----------
    pkt_time: (frame_info.time_epoch) Current packet time.
    macs: (dictionary) Updated list of device addresses with 2-tuple arrival and departure time.
    """
    # get packet time of every packet to compare time
    pkt_time = pkt.frame_info.time_epoch
    
    # check if two consecutive packets are only 2 seconds apart
    # to ensure corrupt packets do not provide invalid time
    if 0 > float(pkt_time) - float(prev_pkt_time) > 2:
        # provide error information to assist in troubleshooting
        print "packet number for time error: ", pkt.number
        print "prev pkt time: ", prev_pkt_time
        print "current pkt time: ", pkt_time
        return prev_pkt_time, macs
    
    try:
        pkt_src = pkt.wlan.sa
        if pkt_src in WIFI_DEVICES:

            # if first time seeing the packet the packet source then
            # add it with the time set as the arrive and depart
            # if the packet is still in the collection, then update the depart time
            if pkt_src not in macs:
                macs[pkt_src] = [pkt_time, pkt_time] #, pkt.number]
            else:
                macs[pkt_src][1] = pkt_time
                # macs[pkt_src][2] = pkt.number
                
            # check each device in the collection of macs to see if it has been more than 
            # five minutes since the last time seeing it.
            for k, v in macs.items():
                if (float(pkt_time) - float(v[1])) > MAC_TRACK_TIME:
                    file_input = [k, helpers.pretty_time(v[0]), helpers.pretty_time(v[1])]#, v[2]]
                    csv.writer(tgt_mac_track_file).writerow(file_input)
                    del macs[k]

    except AttributeError:
        # ignore packets that aren't 802.11
        pass
    
    return pkt_time, macs


def mac_track_final(tgt_mac_track_file, pkt_time, macs):
    """
    Records status of devices after last packet in capture.

    After the last packet is parsed, store each device MAC along with arrival time and time of last packet. This
    provides timing information for devices still on the network at the end of the packet capture.

    Parameters
    ----------
    tgt_mac_track_file: (file object) CSV file to append tracking data.
    pkt_time: (frame_info.time_epoch) Time value obtained from the last packet.
    macs: (dictionary) Uses the device address as keys and a 2-tuple containing the arrival time and departure time
        for each device.

    Returns
    ----------
    Void
    """
    for k, v in macs.items():
        file_input = [k, helpers.pretty_time(v[0]), helpers.pretty_time(pkt_time)]
        csv.writer(tgt_mac_track_file).writerow(file_input)
        del macs[k]

#######################################################################################################################
# TRAINING UNIT
#######################################################################################################################


def trainer():
    """
    Unit that provides graphs to help train classifier.

    Provides user with two graphs for each device showing each packet sent to a device and each packet sent from a
    device. Stores these graphs into files.

    Parameters
    ----------

    Returns
    ----------

    """

    pt_file = open(PROC_TIME, 'a')

    total_time_start = time.time()

    helpers.init_training_dirs()

    pkt_cntr = training_by_dst()

    pkt_cntr += training_by_src()

    total_time = time.time() - total_time_start
    print "Total number of packets: ", pkt_cntr
    print "Total time: ", total_time
    print "Average time: ", (TIMING_PKT_NUMBER*total_time)/pkt_cntr

    csv.writer(pt_file).writerow(["MAC Track", pkt_cntr, total_time, (TIMING_PKT_NUMBER * total_time) / pkt_cntr])
    pt_file.close()


def training_by_dst():
    """
    Provide graphs to help train classifier.

    Provides user with a graphical representation of each packet sent to a device and saves each graph to a file.

    Parameters
    ----------

    Returns
    ----------

    """
    grph_plots = []
    grph_names = []

    packets = 0

    # gather all packets sent to a device by using the destination csv files
    # from preprocessing that contain packets sent to a particular device
    for filename in os.listdir(DST_DIR):
        device_by_dst = []
        device = filename.replace('.csv', '').replace('.', ':')

        if device in IOT_DEVICES:
            # load all packets into a list
            with open(DST_DIR + filename, 'rb') as curr_file:
                reader = csv.reader(curr_file)
                contents = list(reader)

            for line in contents:
                packets += 1
                pkt_time = line[0]
                pkt_size = int(line[1])
                pkt_src = line[2]
                pkt_dst = line[3]
                if pkt_src == RASPI:
                    device_by_dst.append([pkt_time, pkt_size, pkt_src, pkt_dst])

            # setup formatting and graph values
            if len(device_by_dst) != 0:
                dates = [datetime.datetime.strptime(d[0], '%Y-%m-%d %H:%M:%S') for d in device_by_dst]
                dates = m_dates.date2num(dates)
                values = [d[1] for d in device_by_dst]
                grph_plots.append([dates, values])
                grph_names.append("Packets sent from Raspberry Pi to " + DEVICE_NAME[device])

    # create the graphs, show them, and save them
    my_graph_2 = helpers.Graph(grph_plots, grph_names, '%m-%d %H:%M:%S', "Pkts from Raspberry Pi to device")
    my_graph_2.graph()
    my_graph_2.save_files()
    my_graph_2.delete()
    return packets


def training_by_src():
    """
    Provide graphs to help train classifier.

    Provides user with a graphical representation of each packet sent from a device and saves each graph to a file.

    Parameters
    ----------

    Returns
    ----------

    """
    grph_plots = []
    grph_names = []
    packets = 0

    # gather all packets sent from a device by using the source csv files
    # from preprocessing that contain packets sent from a particular device
    for filename in os.listdir(SRC_DIR):
        device_by_src = []
        device = filename.replace('.csv', '').replace('.', ':')

        if device in IOT_DEVICES:
            # load all packets into a list
            with open(SRC_DIR+filename, 'rb') as curr_file:
                reader = csv.reader(curr_file)
                contents = list(reader)

                for line in contents:
                    packets += 1
                    pkt_time = line[0]
                    pkt_size = int(line[1])
                    pkt_src = line[2]
                    pkt_dst = line[3]

                    if pkt_dst == ROUTER:
                        device_by_src.append([pkt_time, pkt_size, pkt_src, pkt_dst])

                # setup formatting and graph values
                if len(device_by_src) != 0:
                    dates = [datetime.datetime.strptime(d[0], '%Y-%m-%d %H:%M:%S') for d in device_by_src]
                    dates = m_dates.date2num(dates)
                    values = [d[1] for d in device_by_src]
                    grph_plots.append([dates, values])
                    grph_names.append("Packets sent from " + DEVICE_NAME[device] + " to Router")

    # create the graphs, show them, and save them
    my_graph = helpers.Graph(grph_plots, grph_names, '%m-%d %H:%M', "Pkts from device to Router")
    my_graph.graph()
    my_graph.save_files()
    my_graph.delete()
    return packets


#######################################################################################################################
# CLASSIFIER UNIT
#######################################################################################################################


def classifier():
    """
    Unit that classifies devices, identifies events, and information to create a network map.

    Provides user with three CSV files:
        (i) A CSV file which contains each device and corresponding classification type.
        (ii) A CSV file which contains the time, source, and destination for each event.
        (iii) A CSV file which contains the total size of all packets sent between two devices.

    Parameters
    ----------

    Returns
    ----------

    """
    total_time_class = 0
    total_time_map = 0
    pt_file = open(PROC_TIME, 'a')

    total_time_start = time.time()

    # initialize file names
    dev_cat_file = "wifi_devices_" + DATE + ".csv"
    helpers.delete_file(dev_cat_file)
    event_id_file = "wifi_events_" + DATE + ".csv"
    helpers.delete_file(event_id_file)
    network_edge_file = "network_edge_" + DATE + ".csv"
    helpers.delete_file(network_edge_file)

    start_time = time.time()
    # open network edge csv file to write nodes and edges into
    with open(network_edge_file, 'a') as network_file:
        # initialize first line of network edge csv with column names required by R-Script
        csv.writer(network_file).writerow(['from', 'to', 'weight'])
    total_time_map += time.time() - start_time

    start_time = time.time()
    # classify devices and identify events by destination
    device_categorization, event_identification, pkt_cntr = events_by_dst()
    total_time_class += time.time() - start_time

    # identify events by destination
    event_identification, pkts, t_class, t_map = events_by_src(network_edge_file, device_categorization,
                                                               event_identification, total_time_class, total_time_map)

    pkt_cntr += pkts
    total_time_class += t_class
    total_time_map += t_map

    start_time = time.time()
    # write device categories to file
    with open(dev_cat_file, 'a') as curr_file:
        for k, v in device_categorization.iteritems():
            csv.writer(curr_file).writerow([DEVICE_NAME[k], v])

    # write events to file
    with open(event_id_file, 'a') as curr_file:
        for event in sorted(event_identification):
            csv.writer(curr_file).writerow(event)
    total_time_class += time.time() - start_time

    total_time = time.time() - total_time_start
    normalized_total_time = (TIMING_PKT_NUMBER * total_time)/pkt_cntr
    normalized_class_time = (TIMING_PKT_NUMBER * (total_time - total_time_map))/pkt_cntr
    normalized_map_time = (TIMING_PKT_NUMBER * (total_time - total_time_class))/pkt_cntr

    print "Total number of packets classifier: ", pkt_cntr
    print "Total time classifier: ", total_time
    print "Normalized total time classifier per 25000 packets: ", normalized_total_time
    csv.writer(pt_file).writerow(["Class+NtwkMapper", pkt_cntr, total_time, normalized_total_time])
    print "Total time class: ", total_time_class
    print "Normalized time class: ", normalized_class_time
    csv.writer(pt_file).writerow(["Classifier", pkt_cntr, total_time_class, normalized_class_time])
    print "Total time network mapper: ", total_time_map
    print "Normalized time network mapper: ", normalized_map_time
    csv.writer(pt_file).writerow(["Network Mapper", pkt_cntr, total_time_map, normalized_map_time])
    pt_file.close()


def events_by_dst():
    """
    Identify devices and identify events by destination.

    Uses the files created in preprocessing which contain packets with the device as the destination
    to classify devices and identify events according to classifier parameters.

    Parameters
    ----------

    Returns
    ----------
    device_categorization: (dictionary) Uses device addresses as keys and assigned category as values.
    event_identification: (list) 2-D list containing the time, source, and destination of each identified event
    """
    device_categorization = {}
    event_identification = []
    pkt_cntr = 0
    # analyze all of the packets sent to a device by using the destination csv files
    # from preprocessing that contain packets destined for a particular device
    for filename in os.listdir(DST_DIR):
        device_by_dst = []
        device = filename.replace('.csv', '').replace('.', ':')
        events = []

        # if the file contains packets destined to an IoT device, then read the file into a list
        if device in IOT_DEVICES:
            device_category = 'UNKNOWN'
            with open(DST_DIR + filename, 'rb') as curr_file:
                reader = csv.reader(curr_file)
                contents = list(reader)

            # for each packet in the file, obtain the time, frame size, source, and destination and store in a list
            for line in contents:
                pkt_cntr += 1
                pkt_time = line[0]
                pkt_size = int(line[1])
                pkt_src = line[2]
                pkt_dst = line[3]
                if pkt_src == RASPI:
                    device_by_dst.append([pkt_time, pkt_size, pkt_src, pkt_dst])
                    device_category = helpers.categorize_device_by_dst(pkt_size, device_category)

                    # if the device was previously categorized as an outlet,
                    # then identify events from packets sent to the outlet
                    if device_category == 'OUTLET':
                        event_identification, events = helpers.id_events_by_dst(pkt_time, pkt_size, pkt_src, pkt_dst,
                                                                                event_identification, events)
            device_categorization[device] = device_category

    return device_categorization, event_identification, pkt_cntr


def events_by_src(network_edge_file, device_categorization, event_identification, total_time_class, total_time_map):
    """
    Identify events by source.

    Uses the files created in preprocessing which contain packets with the device as the source
    to identify events according to classifier parameters. Simultaneously records the amount of data sent
    between two devices.

    Parameters
    ----------    network_edge_file: (file object) File used to record amount of data sent between two devices.
    device_categorization: (dictionary) Uses device addresses as keys and assigned category as values.
    event_identification: (list) 2-D list containing the time, source, and destination of each identified event

    Returns
    ----------
    event_identification: (list) 2-D list containing the time, source, and destination of each identified event
    """

    pkt_cntr = 0
    # analyze all of the packets sent from a device by using the source csv files
    # from preprocessing that contain packets from a particular device
    for filename in os.listdir(SRC_DIR):
        device_by_src = {}
        device = filename.replace('.csv', '').replace('.', ':')
        pkt_src = ''

        # initialize dictionary for mapping devices; the key is the dst device and the value is the
        # total size of packets sent to that device
        map_dst_device = {}

        with open(SRC_DIR+filename, 'rb') as curr_file:
            reader = csv.reader(curr_file)
            contents = list(reader)

            # for each packet, obtain the time, frame size, source, and destination
            # for the time, only include up to the minute
            for line in contents:
                pkt_cntr += 1
                pkt_time = line[0]
                pkt_time = pkt_time[:pkt_time.rindex(':')]
                pkt_size = int(line[1])
                pkt_src = line[2]
                pkt_dst = line[3]

                start_time = time.time()
                # classification
                if pkt_dst == ROUTER:
                    # for every packet sent in the same minute, sum the packet size
                    if pkt_time in device_by_src:
                        device_by_src[pkt_time] = device_by_src[pkt_time] + pkt_size
                    else:
                        device_by_src[pkt_time] = pkt_size
                        total_time_class += time.time() - start_time

                start_time = time.time()
                # mapping
                # find the total frame size of all packets sent to any destination device
                if pkt_dst in map_dst_device:
                    map_dst_device[pkt_dst] = map_dst_device[pkt_dst] + pkt_size
                else:
                    map_dst_device[pkt_dst] = pkt_size
                total_time_map += time.time() - start_time

            start_time = time.time()
            # attempt to identify events based off of packets sent from a device
            if (device in IOT_DEVICES) and (len(device_by_src) != 0):
                event_identification = helpers.identify_events_by_src(device_by_src, pkt_src, ROUTER,
                                                                      device_categorization, event_identification)
            total_time_class += time.time() - start_time

        start_time = time.time()
        # write the source, destination, and total frame size to the network edge csv file
        # The R-Script requires IDs instead of names, so store with ID
        with open(network_edge_file, 'a') as network_file:
            for k, v in map_dst_device.iteritems():
                csv.writer(network_file).writerow([DEVICE_ID[device.replace('.', ':')], DEVICE_ID[k], v])
        total_time_map += time.time() - start_time

    return event_identification, pkt_cntr, total_time_class, total_time_map


#######################################################################################################################
# EXTRA
#######################################################################################################################


# Function not used during the experiment, but used to analyze different kinds of cameras
# and ways to sum packets over time. Currently, this function takes a moving average
# of the frame size sent by a device over five seconds
def events_by_src_2(network_edge_file, device_categorization, event_identification):
    grph_plots = []
    grph_names = []

    for filename in os.listdir(SRC_DIR):
        device_by_src = {}
        device = filename.replace('.csv', '').replace('.', ':')
        pkt_src = ''

        # initialize dictionary in which the key is the destination device and the value is the
        # total size of packets sent to that device
        map_dst_device = {}

        with open(SRC_DIR+filename, 'rb') as curr_file:
            reader = csv.reader(curr_file)
            contents = list(reader)

            for line in contents:
                pkt_time = line[0]
                pkt_size = int(line[1])
                pkt_src = line[2]
                pkt_dst = line[3]

                # classification
                if pkt_dst == ROUTER:
                    if time in device_by_src:
                        device_by_src[pkt_time] = device_by_src[pkt_time] + pkt_size
                    else:
                        device_by_src[pkt_time] = pkt_size

                # mapping
                # find the total frame size of all packets sent to any destination device
                if pkt_dst in map_dst_device:
                    map_dst_device[pkt_dst] = map_dst_device[pkt_dst] + pkt_size
                else:
                    map_dst_device[pkt_dst] = pkt_size

                    norm_size_complete = {}
                    d_list = list(sorted(device_by_src.keys()))
                    for i in range(0, len(d_list)-1):
                        count = 1
                        norm_size = device_by_src[d_list[i]]
                        if i > 0:
                            norm_size = norm_size + device_by_src[d_list[i-1]]
                            count += 1
                        if i > 1:
                            norm_size = norm_size + device_by_src[d_list[i - 2]]
                            count += 1
                        if i < len(d_list)-1:
                            norm_size = norm_size + device_by_src[d_list[i+1]]
                            count += 1
                        if i < len(d_list)-2:
                            norm_size = norm_size + device_by_src[d_list[i+2]]
                            count += 1
                        norm_size_complete[d_list[i]] = norm_size/count
                    print "----------", pkt_src, "----------"

                    for k in sorted(norm_size_complete.iterkeys()):
                        if int(norm_size_complete[k]) > 50000:
                            print k, norm_size_complete[k]

            if device in IOT_DEVICES:
                helpers.identify_events_by_src(norm_size_complete, pkt_src, ROUTER, device_categorization,
                                               event_identification)

                if len(device_by_src) != 0:
                    dates = [datetime.datetime.strptime(d, '%Y-%m-%d %H:%M:%S') for d in norm_size_complete.keys()]
                    dates = m_dates.date2num(dates)
                    values = norm_size_complete.values()
                    grph_plots.append([dates, values])
                    grph_names.append(filename.replace('.csv', ''))

        # write the source, destination, and total frame size to the network edge csv file
        # The R-Script requires IDs instead of names, so store with ID
        with open(network_edge_file, 'a') as network_file:
            for k, v in map_dst_device.iteritems():
                csv.writer(network_file).writerow([DEVICE_ID[device.replace('.', ':')], DEVICE_ID[k], v])

    my_graph = helpers.Graph(grph_plots, grph_names, '%m-%d %H:%M', "Pkts from device to ec:4f:82:73:d1:1c")
    my_graph.graph()
    my_graph.save_files()
    my_graph.delete()

    return event_identification

# call main
if __name__ == "__main__":
    main(sys.argv[1:])
