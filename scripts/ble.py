#!/usr/bin/python
import helpers
import pyshark
import sys, getopt, csv

#######################################################################################################################
# GLOBAL VARIABLES
ADV_IND = '0'
SCAN_RESP = '4'
CONNECT_REQ = '5'
#######################################################################################################################

def main(argv):
    try:
        opts, args = getopt.getopt(argv, "hc:", ["help"])
    except getopt.GetoptError:
        print 'parse_controller.py -c <pcap file>'
        sys.exit(2)
    for opt, arg, in opts:
        if opt in ("-h", "--help"):
            print 'parse_controller.py -c <pcap file>'
            sys.exit()
        elif opt == '-c':
            classifier(arg)


def classifier(file_name):
    """
    Classifying unit for Bluetooth Low Energy.

    Utilizes the provided packet capture to parse data looking for connection events.
    Provides two files: one with each device's MAC address and name and
    one with the time, access address, master, and slave of each connection event.

    Parameters
    ----------
    file_name: (string) File name of capture provided by user.

    Returns
    ----------

    """
    # initialize files
    cap = pyshark.FileCapture(file_name)
    btle_output_file = "ble_events.csv"
    helpers.delete_file(btle_output_file)
    btle_device_file = "ble_devices.csv"
    helpers.delete_file(btle_device_file)

    # initialize dictionary to store device information
    devices = {}
    # initialize list to store connection information
    connections = []

    # parse each packet in the capture looking for advertising indication, scan response and connect request packets
    for pkt in cap:
        try:
            if pkt.btle.advertising_header_pdu_type == ADV_IND:
                devices = ble_adv_ind(pkt, devices)

            elif pkt.btle.advertising_header_pdu_type == SCAN_RESP:
                devices = ble_scan_response(pkt, devices)

            elif pkt.btle.advertising_header_pdu_type == CONNECT_REQ:
                connections = ble_connect_req(pkt, devices, connections)

        except AttributeError:
            # ignore packets that are malformed
            pass

    # write results to files
    with open(btle_output_file, 'a') as curr_file:
        for file_input in connections:
            csv.writer(curr_file).writerow(file_input)

    with open(btle_device_file, 'a') as curr_file:
        for k, v in devices.iteritems():
            csv.writer(curr_file).writerow([k, v])


def ble_adv_ind(pkt, devices):
    """
    Parse Advertising Indication packets.

    Extract device name provided in Advertising Indication packets.

    Parameters
    ----------
    pkt: (pyshark packet) Pyshark packet object containing packet information from capture.
    devices: (dictionary) Uses the device address as the key and the name of the device as the value.

    Returns
    ----------
    devices: (dictionary) Updated dictionary of device addresses and corresponding names
    """
    # if a device name has not been found, then extract the name from the Advertising Indication packet and store it
    adv_addr = pkt.btle.advertising_address
    if adv_addr not in devices:
        device_name = pkt.btle.btcommon_eir_ad_entry_device_name
        # from trial and error some weird device names can appear, so ignore some that have been encountered
        if (len(device_name) > 2) and not(device_name.startswith('\\x')):
            devices[adv_addr] = device_name

    return devices


def ble_scan_response(pkt, devices):
    """
    Parse Scan Response packets.

    Extract device name provided in Scan Response packets. These packet types provide more information than an
    Advertising Packet, so overwrite if a device name was found from an Advertising Indication packets.

    Parameters
    ----------
    pkt: (pyshark packet) Pyshark packet object containing packet information from capture.
    devices: (dictionary) Uses the device address as the key and the name of the device as the value.

    Returns
    ----------
    devices: (dictionary) Updated dictionary of device addresses and corresponding names
    """
    # attempt to extract a device name from the Scan Response packet
    # Scan Response packets provide better naming information so overwrite previously found names
    try:
        device_name = pkt.btle.btcommon_eir_ad_entry_device_name
        devices[pkt.btle.advertising_address] = device_name
    except AttributeError:
        # ignore packets with no device name
        pass

    return devices
        

def ble_connect_req(pkt, devices, connections):
    """
    Parse Connection Request packets.

    Find Connection Request packets and record the time, access address, master device name, and slave device name.

    Parameters
    ----------
    pkt: (pyshark packet) Pyshark packet object containing packet information from capture.
    devices: (dictionary) Uses the device address as the key and the name of the device as the value.
    connections: (list) 2-D list containing the following information for each connection event:
        packet time, access address, master device name, and slave device name.

    Returns
    ----------
    connections: (list) Updated list of connection events
    """
    # extract required information from Connection Request packets (packet time, master/slave mac addresses, and
    # access address
    pkt_time = pkt.frame_info.time_epoch
    pkt_time = helpers.pretty_time(pkt_time)[:pkt_time.rindex(':')]
    # pkt_mstr_mac = pkt.btle.initiator_address
    pkt_slv_mac = pkt.btle.advertising_address
    # pkt_lladdr = pkt.btle.link_layer_data_access_address
    # pkt_mstr_id = pkt_slv_id = "No ID"

    # obtain device names using MAC addresses found in the Connection Request packet and device names found in
    # Advertising Indication and Scan Response packets
    # if pkt_mstr_mac in devices: pkt_mstr_id = devices[pkt_mstr_mac]
    if pkt_slv_mac in devices: pkt_slv_id = devices[pkt_slv_mac]
    
    # fields = [pkt_time, pkt_lladdr, pkt_mstr_mac + " (" + pkt_mstr_id + ")", pkt_slv_mac + " (" + pkt_slv_id + ")"]
    fields = [pkt_time, pkt_slv_id, '1']

    # if the slave address cannot be resolved to a device name, ignore it as it does not provide valuable information
    # also, sometimes multiple connections occur during one event so only acknowledge one event per device per minute.
    # This sample interval provides enough precision for the problem at hand
    if ('No ID' not in pkt_slv_id) and (fields not in connections):
        connections.append(fields)

    return connections


# call main
if __name__ == "__main__":
    main(sys.argv[1:])
