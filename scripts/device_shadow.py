#!/usr/bin/python
import sys, time, datetime, multiprocessing

from scapy.all import *

DEVICES = {'B4:75:0E:0D:33:D5': '192.168.1.40', 'B4:75:0E:0D:94:65': '192.168.1.41',
           '94:10:3E:2B:7A:55': '192.168.1.42', '14:91:82:C8:6A:09': '192.168.1.7',
           '14:91:82:24:DD:35': '192.168.1.47', '60:38:E0:EE:7C:E5': '192.168.1.51',
           'EC:1A:59:F1:FB:21': '192.168.1.43', 'EC:1A:59:E4:FD:41': '192.168.1.44'}
RASPI_MAC = 'B8:27:EB:09:1A:81'
RASPI_IP = '192.168.1.50'
ROUTER_MAC = 'ec:4f:82:73:d1:1c'
ROUTER_IP = '192.168.1.1'
tcp = TCP(dport=4242)

OUTLET_DATA = '\xccWhat is the answer to the Ultimate Question of Life, The Universe, and Everything? The answer is ' \
              '42! The test test testtesttateaerasdfasdfjflaksdjf;kljasd;asaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' \
              'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' \
              'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' \
              'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' \
              'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
SENSOR_DATA = '\xccWhat is the answer to the Ultimate Question of Life, The Universe, and Everything? The answer is ' \
              '42! aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' \
              'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' \
              'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' \
              'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' \
              'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' \
              'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' \
              'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' \
              'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' \
              'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' \
              'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' \
              'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' \
              'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' \
              'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' \
              'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
CAMERA_DATA = "\xccWhat is the answer to the Ultimate Question of Life, The Universe, and Everything? The answer is " \
              "42! aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" \
              "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" \
              "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" \
              "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" \
              "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" \
              "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" \
              "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" \
              "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" \
              "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" \
              "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" \
              "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" \
              "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" \
              "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" \
              "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
# Time Format
TIME_FORMAT = '%Y-%m-%d %H:%M:%S'


def main():
    functions = [outlet_devices, sensor_devices, camera_devices]
    while 1:
        random.shuffle(functions)
        for function in functions:
            function()
            sleep_time = random.randint(60,120)
            print 'sleeping for ', sleep_time, ' seconds.'
            time.sleep(sleep_time)
        sleep_time = random.randint(600,900)
        print 'sleeping for ', sleep_time, ' seconds.'
        time.sleep(sleep_time)

# Spoof the traffic signature sent from the Raspberry Pi to an outlet. For each device in a random order send a 
# TCP packet of size 620 bytes from the raspberry pi to each device
def outlet_devices():
    print 'outlet device'
    keys = list(DEVICES.keys())
    random.shuffle(keys)
    for key in keys:
        for _ in range(3):
            print "sending packet on behalf of ", RASPI_MAC, ' to ', key, ' at ', pretty_time(time.time())
            ether = Ether(src=RASPI_MAC, dst=key)
            ip = IP(src=RASPI_IP, dst=DEVICES[key])
            sendp(ether / ip / tcp / OUTLET_DATA, iface='eth0', verbose=0)
        time.sleep(1)


# Spoof the traffic signature sent from a sensor to the router. For each device in a random order send a series of 
# TCP packets totaling a size of at least 10000 bytes from the device to the router in one minute
def sensor_devices():
    print 'sensor device'
    keys = list(DEVICES.keys())
    random.shuffle(keys)
    for key in keys:
        for _ in range(10):
            print "sending packet on behalf of ", key, ' to ', ROUTER_MAC, ' at ', pretty_time(time.time())
            ether = Ether(src=key, dst=ROUTER_MAC)
            ip = IP(src=DEVICES[key], dst=ROUTER_IP)
            sendp(ether / ip / tcp / SENSOR_DATA, iface='wlan0', verbose=0)
        time.sleep(1)


# Spoof the traffic signature sent from a camera to the router. For each device in a random order send a series of 
# TCP packets totaling a size of at least 100000 bytes from the device to the router in one minute
def camera_devices():
    print 'camera device'
    keys = list(DEVICES.keys())
    random.shuffle(keys)
    jobs = []
    for key in keys:
        for _ in range(5):
            p = multiprocessing.Process(target=camera_msg, args =(key,))
            jobs.append(p)
            p.start()
    # block until all processes are done
    for job in jobs:
        job.join()


def camera_msg(key):
    for _ in range(5):
        print "sending packet on behalf of ", key, ' to ', ROUTER_MAC, ' at ', pretty_time(time.time())
        ether = Ether(src=key, dst=ROUTER_MAC)
        ip = IP(src=DEVICES[key], dst=ROUTER_IP)
        sendp(ether / ip / tcp / CAMERA_DATA, iface='wlan0', verbose=0)

# source = camera/Sensor & dest = ec:4f:82:73:d1:1c
# source = b8:27:eb:09:1a:81 & dest = outlet

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