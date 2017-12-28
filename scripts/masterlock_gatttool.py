#!/usr/bin/python
import time
import pexpect

def main():
    # target device MAC
    DEVICE = "D0:B5:C2:A2:B0:0E"
    
    print "MasterLock address: " , DEVICE
    
    print "Run gatttool..."
    child = pexpect.spawn("gatttool -I")
    
    # Connect to the device.
    connect(child, DEVICE)

    child.sendline("mtu 185")

    # login to lock
    # handle: 0x001C
    # data: AT+PASSKEY="LOCK_PIN"
    write_char(child, "0x000e", "0100")
    
    write_char(child, "0x000d", "0080832834065300362e5bacbaf0bf507fa9"
                                "74f3f8ff302885fbb7ee15b9e1f4da55b443"
                                "4baeb82d347d3ba583c32bba9348965b057b"
                                "dee548ea4a7a6d89f99abed1c49c5df62a")

    # write_char(child, "0x000d", "010001c76b9483d9e2fc67f3")
    #
    write_char(child, "0x000e", "0100")
    #
    # write_char(child, "0x000d", "010001b54861c01eb762c7a9")
    #
    write_char(child, "0x000e", "0100")
    #
    # write_char(child, "0x000d", "010001db4b4971b4ca88f737")
    
# Connect do device
def connect(child, device):
        print "Connecting to ", device
        child.sendline("connect {0}".format(device))
        child.expect("Connection successful",  timeout=5)
        print "Connected"

# Write characteristic to given handle with given data
def write_char(child, handle, data):
    child.sendline("char-write-req " + handle + " " + data)
    child.expect("Characteristic value was written successfully", timeout=10)
    child.expect("\r\n", timeout=10)
    #print "Characteristic value was written successfully"


if __name__ == "__main__":
    main()
