#!/usr/bin/python
import pyshark
import datetime, os, errno, shutil, sys
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

#######################################################################################################################
# GLOBAL VARIABLES
DEVICE_NAME = {'ec:4f:82:73:d1:1c': 'Router', 'ec:1a:59:e4:fd:41': 'NetCam', 'b4:75:0e:0d:33:d5': 'Switch1',
               'b4:75:0e:0d:94:65': 'Switch2', '94:10:3e:2b:7a:55': 'Switch3', '14:91:82:c8:6a:09': 'Switch4',
               'ec:1a:59:f1:fb:21': 'Motion', '14:91:82:24:dd:35': 'Insight', '60:38:e0:ee:7c:e5': 'Mini',
               'b8:27:eb:09:1a:81': 'Pi', 'a0:18:28:33:34:f8': 'iPhone', '08:66:98:ed:1e:19': 'AppleTV'}

SRC_DIR = './Source/'
DST_DIR = './Destination/'
GRPH_DIR = './Graphs/'
TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
UNKNOWN = 0
OUTLET = 1
SENSOR = 2
CAMERA = 3
#######################################################################################################################


def init_dirs():
    """
    Initializes directory for storing files. If the directory exists delete it then create an empty dir.
    """
    src_dir = os.path.dirname(SRC_DIR)
    dst_dir = os.path.dirname(DST_DIR)

    if os.path.exists(src_dir):
        try:
            shutil.rmtree(src_dir)
        except OSError:
            print "Issue removing files within ", src_dir, " check if files are read only."
            sys.exit()
    os.makedirs(src_dir)
    if os.path.exists(dst_dir):
        try:
            shutil.rmtree(dst_dir)
        except OSError:
            print "Issue removing files within ", dst_dir, " check if files are read only."
            sys.exit()
    os.makedirs(dst_dir)


def init_training_dirs():
    """
    Initializes directory for graph files. If the directory exists delete it then create an empty dir.
    """
    grph_dir = os.path.dirname(GRPH_DIR)
    if os.path.exists(grph_dir):
        try:
            shutil.rmtree(grph_dir)
        except OSError:
            print "Issue removing files within ", grph_dir, " check if files are read only."
            sys.exit()
    os.makedirs(grph_dir)


def delete_file(filename):
    """
    Deletes file.

    Parameters
    ----------
    filename: (string) file to delete.
    """
    try:
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


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
    # have to account for timestamp issue on host computer during first four days of trial
    if float(pkt_time) < 1503370800:
        return datetime.datetime.fromtimestamp(float(pkt_time) + 42).strftime(TIME_FORMAT)
    elif float(pkt_time) < 1503702000:
        return datetime.datetime.fromtimestamp(float(pkt_time)+48).strftime(TIME_FORMAT)
    else:
        return datetime.datetime.fromtimestamp(float(pkt_time)).strftime(TIME_FORMAT)


class Graph(object):
    """
    Helper function to create graphs using the matplotlib library
    """
    def __init__(self, plots= [], names= [], date_format = '%m-%d %H:%M:%S',
                 title= "Figure"):
        # get the datetime and value for each device and packet
        self.plots = plots
        # get the name for each device
        self.names = names
        self.title = title
        # self.id = id
        self.date_format = date_format
        # create figure and axes
        self.fig = plt.figure()
        self.ax = plt.subplot(111)

        # setup formatting for datetime axes
        self.seconds = mdates.SecondLocator()
        self.hours = mdates.HourLocator()
        self.minutes = mdates.MinuteLocator()
        self.hourFmt = mdates.DateFormatter('%H')

        # create the initial graph
        self.curr_pos = 0

        # call self.update everytime a 'key_press_event' happens
        self.cid = self.fig.canvas.mpl_connect('key_press_event', self.update)

    def graph(self):
        """
        Presents graph of device packets
        """
        self.set_axes_parameters()

        # set the plot data and x-axis range
        self.ax.plot_date(self.dates, self.values)

        plt.show()

    def update(self, e):
        """
        Updates graphs when moving between the different devices
        e: (event) function called on arrow key event
        """
        if e.key == "right":
            self.curr_pos += 1
        elif e.key == "left":
            self.curr_pos -= 1
        else:
            return

        # allow it to loop
        self.curr_pos = self.curr_pos %len(self.plots)

        self.ax.cla()

        self.set_axes_parameters()

        self.ax.plot_date(self.dates, self.values)

        # regraph
        self.fig.canvas.draw()

    def save_files(self):
        """
        Saves graphs into files
        """
        self.curr_pos = 0
        for name in self.names:
            self.fig = plt.figure()
            self.ax = plt.subplot(111)

            self.set_axes_parameters()

            self.ax.plot_date(self.dates, self.values)

            self.fig.savefig(GRPH_DIR + name + '.png')
            self.ax.cla()
            self.curr_pos += 1

    def set_axes_parameters(self):
        """
        Setup the axes parameters
        """
        # update date, values, and name to the current device
        self.dates = self.plots[self.curr_pos][0]
        self.values = self.plots[self.curr_pos][1]

        # set the title of the figure and axes
        self.fig.canvas.set_window_title(self.title)
        name = self.names[self.curr_pos]
        self.ax.set_title(name)
        self.ax.set_xlabel('Time (hour)')
        self.ax.set_ylabel('Frame Size (bytes)')

        # setup formatting for datetime axes
        self.ax.xaxis.set_major_locator(self.hours)
        self.ax.xaxis.set_major_formatter(self.hourFmt)
        self.ax.format_xdata = mdates.DateFormatter(self.date_format)
        self.ax.set_xlim(self.dates.min()-.001, self.dates.max()+.001)
        self.ax.grid(True)
        self.fig.autofmt_xdate()

    def delete(self):
        plt.close('all')
        self.fig.canvas.mpl_disconnect(self.cid)


# write category of device to csv
def categorize_device_by_dst(pkt_size, device_category):
    """
    Categorize devices using traffic destined to device and criteria found during training.

    Parameters
    ----------
    pkt_size: (pkt.length) Contains the frame size of a packet sent to the device.

    Returns
    ----------
    category: (string) Return the category of the device based on which criteria is met by the packet.
    """
    if device_category != 'OUTLET':
        # criteria for an outlet
        if 619 <= pkt_size <= 632:
            return 'OUTLET'
        # criteria for a camera
        elif pkt_size == 281:
            return 'CAMERA'
        # criteria for a sensor
        elif pkt_size == 269:
            return 'SENSOR'

    return device_category


def id_events_by_dst(pkt_time, pkt_size, pkt_src, pkt_dst, event_identification, events):
    """
    Identify events using traffic from the Raspberry Pi to device and criteria found during training.

    Parameters
    ----------
    pkt_time: (datetime) Contains the time, frame size, source, and destination of each packet sent to a device.
    pkt_size: (pkt.length) Uses device address as keys and the assigned category as values.
    pkt_src: (pkt.wlan.sa) Source address of the packet.
    pkt_dst: (pkt.wlan.da) Destination address of the packet.
    event_identification: (list) 2-D list with each entry containing the time, source, and destination of an event.
    events: (list) Contains a time to the minute of events that occurred.

    Returns
    ----------
    event_identification: (list) Updated event identification list.
    """
    if 619 <= pkt_size <= 632:
        pkt_time = pkt_time[:pkt_time.rindex(':')]
        # sometimes multiple packets are sent due to retransmission attempts so only acknowledge one
        # event per device per minute. This sample interval provides enough precision for the problem at hand
        if pkt_time not in events:
            events.append(pkt_time)
            # event_identification.append([pkt_time, DEVICE_NAME[pkt_src], DEVICE_NAME[pkt_dst], '1'])
            event_identification.append([pkt_time, DEVICE_NAME[pkt_dst], '1'])

    return event_identification, events


def identify_events_by_src(device_by_src, pkt_src, pkt_dst, device_categorization, event_identification):
    """
    Identify events using traffic from a device to the router and criteria found during training.

    Parameters
    ----------
    device_by_src: (dictionary) Keys are the time of the packet time to the minute and values are the sum of all packets
        sent in one minute.
    pkt_src: (pkt.wlan.sa) Source address of the packet.
    pkt_dst: (pkt.wlan.da) Destination address of the packet.
    device_categorization: (dictionary) Uses device addresses as keys and assigned category as values.
    event_identification: (list) 2-D list containing the time, source, and destination of each identified event.

    Returns
    ----------
    event_identification: (list) Updated 2-D list containing the time, source, and destination of each identified event.
    """
    if device_categorization[pkt_src] == 'CAMERA':
        for k, v in sorted(device_by_src.iteritems()):
            if v > 100000:
                if check_motion_event(k, pkt_src, event_identification):
                    # event_identification.append([k, DEVICE_NAME[pkt_src], DEVICE_NAME[pkt_dst], '1'])
                    event_identification.append([k, DEVICE_NAME[pkt_src], '1'])
    elif device_categorization[pkt_src] == 'SENSOR':
        for k, v in sorted(device_by_src.iteritems()):
            if v > 10000:
                if check_motion_event(k, pkt_src, event_identification):
                    # event_identification.append([k, DEVICE_NAME[pkt_src], DEVICE_NAME[pkt_dst], '1'])
                    event_identification.append([k, DEVICE_NAME[pkt_src], '1'])

    return event_identification

# Because motion events take time to send, if one was sent the minute before then ignore a potential new event
# could cause us to miss two events in a row, but most motion devices have at least a 60 second no motion sensor
# before restarting, so this should not be an issue.
def check_motion_event(pkt_time, pkt_src, event_identification):
    date = datetime.datetime.strptime(pkt_time, '%Y-%m-%d %H:%M')
    check_date = date - datetime.timedelta(minutes=1)
    new_date = check_date.strftime('%Y-%m-%d %H:%M')
    if [new_date, DEVICE_NAME[pkt_src], '1'] in event_identification:
        return False
    return True