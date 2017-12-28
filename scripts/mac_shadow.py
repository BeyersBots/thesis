#!/usr/bin/python
import sys, time, datetime

from scapy.all import *

# Device IPs to shadow
DEVICES= ["192.168.1.4"]
# Device MACs to shadow
MACS= ["a0:18:28:33:34:f8"]
# Device IP that is always on the network to make spoofed packets appear real
DST_IP = "192.168.1.54"
# Device MAC to send packets to
DST_MAC = "08:66:98:ed:1e:19"
# Network Interface to use to send packets
INTERFACE = 'wlan0'
# Time format
TIME_FORMAT = '%Y-%m-%d %H:%M:%S'


def main():
    # will hold all of the src/dst ethernet tuples for scapy
    ethers = []
    # will hold all of the src/dst IP tuples for scapy
    ips = []
    # tcp destination port
    tcp = TCP(dport=4242)
    # message to send for fun
    data = '\xccWhat is the answer to the Ultimate Question of Life, The Universe, and Everything?'

    # for each ip and mac address provided above, create the tuples for scapy
    for ip, mac in zip(DEVICES, MACS):
        ethers.append(Ether(src=mac, dst=DST_MAC))
        ips.append(IP(src=ip, dst=DST_IP))

    # infinite loop
    while 1:
        # initialize variables
        all_present = True
        absent_devices = []
        # for each device, check if it is present. If it is not present
        # add device IP and ethernet tuples to the list of absent devices
        for ip, ether, dev in zip(ips, ethers, DEVICES):
            device_present = check_device(dev)
            if device_present != True:
                all_present = False
                absent_devices.append([ether,ip, dev])

        # if all devices are present, sleep for 5 min, then check again
        if all_present == True:
            print 'all devices present; sleeping for 4 min'
            time.sleep(240)

        # if they are not all present, send 10 packets at random intervals from the device
        # then sleep between one and 3 minutes before checking for devices again
        else:
            print 'All devices not present'
            for dev in absent_devices:
                print 'Sending ten messages on behalf of:', dev[2], 'at', pretty_time(time.time())
                for _ in range(10):
                    sendp(dev[0]/dev[1]/tcp/data, iface=INTERFACE, verbose=0)
                    sleep_time = random.randint(1,100)
                    time.sleep(sleep_time/100)
            sleep_time = random.randint(180,240)
            print 'Done sending, going to sleep for', sleep_time, 'seconds then restart.'
            time.sleep(sleep_time)

        del absent_devices[:]


def check_device(dev):
    print 'Checking to see if device at ', dev, ' is on the network at ', pretty_time(time.time())
    # ICMP ping
    # ans,unans=sr(IP(dst=dev)/ICMP(),timeout=2, verbose=0)
    # for s, r in ans:
    #     if r[IP].src == dev:
    #         print 'Device responded to ICMP ping'
    #         print 'Device is present'
    #         return True
    # print 'Device did not respond to ICMP ping'

    # ARP ping
    ans,unans=srp(Ether(dst="ff:ff:ff:ff:ff:ff:ff")/ARP(pdst=dev),timeout=2, verbose=0, retry=10)
    for s, r in ans:
        if r[ARP].psrc == dev:
            print 'Device responded to ARP'
            print 'Device is present'
            return True
    print 'Device did not respond to ARP'
    print 'Device is not present'
    return False


def pretty_time(pkt_time):
    """
    Takes epoch time and transforms it into a better format.

    Parameters
    ----------
    pkt_time: (pkt.frame_info.time_epoch) Time of packet in epoch format.

    Returns
    ----------
    time: (datetime) Time of packet in datetime format.
    """
    return datetime.fromtimestamp(float(pkt_time)).strftime(TIME_FORMAT)

if __name__ == "__main__":
    main()
