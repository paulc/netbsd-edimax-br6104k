#!/usr/bin/env python
"""
   Upload firmware to ADM5120 router.

   bifferos@yahoo.co.uk  2007
"""
import fdpexpect, os, sys, tempfile, struct, termios, time, thread
from optparse import OptionParser

import string, struct, socket, select, thread, StringIO, os, gzip


g_usage = "%prog [options] <image filename>"

g_description = """
This program expects to connect to a BR-6104K(P) running Vlad's ftp bootloader.
The program waits for the ADM5120 to power up, then configures the
bootloader tftp parameters, starts a tftp server and transfers the specified
kernel image to either DRAM or Flash.
"""

opt = OptionParser(version="%prog v2.1", usage=g_usage, 
                   description=g_description)
opt.add_option("-d","--device", dest="device", default="/dev/tty.usbserial-FTD2W8AR",
               help="Serial communication device (default: %default)")
opt.add_option("-a","--address", dest="address", default="10.0.0.30",
               help="BR-6104KP IP address for tftp client (default: %default)")
opt.add_option("-n","--netif", dest="netif", default="en0",
               help="Network interface for tftp server (default: %default)")
opt.add_option("-w","--write", dest="write", default=False, action="store_true",
               help="Write image to flash (default: False)")

(opts, args) = opt.parse_args()

if not args or not os.path.isfile(args[0]) :
        opt.print_help()
        sys.exit(0)



# IP address of the server (this machine) 
TFTP_HOST = [ x.split()[1] for x in os.popen("/sbin/ifconfig %s inet" % opts.netif).readlines() 
                                 if x.strip().startswith('inet') ][0]

#
# TFTP Errors
#
class TFTPError(Exception):
    pass

#
# A class for a TFTP Connection
#
class TFTPConnection:

    RRQ  = 1
    WRQ  = 2
    DATA = 3
    ACK  = 4
    ERR  = 5
    HDRSIZE = 4  # number of bytes for OPCODE and BLOCK in header

    def __init__(self, host="", port=0, blocksize=512, timeout=2.0, retry=5):
        self.host = host
        self.port = port
        self.blocksize = blocksize
        self.timeout   = timeout
        self.retry     = retry

        self.client_addr = None
        self.sock        = None
        self.active      = 0
        self.blockNumber = 0
        self.lastpkt     = ""

        self.mode        = ""
        self.filename    = ""
        self.file        = None

        self.bind(host, port)

    def bind(self, host="", port=0):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock = sock
        if host or port:
            sock.bind(host, port)

    def send(self, pkt=""):
        self.sock.sendto(pkt, self.client_addr)
        self.lastpkt = pkt

    def recv(self):
        sock        = self.sock
        F           = sock.fileno()
        client_addr = self.client_addr
        timeout     = self.timeout            
        retry       = self.retry

        while retry:
            r,w,e = select.select( [F], [], [F], timeout)
            if not r:
                # We timed out -- retransmit
                retry = retry - 1
                self.retransmit()
            else:
                # Read data packet
                pktsize = self.blocksize + self.HDRSIZE
                data, addr = sock.recvfrom(pktsize)
                if addr == client_addr:
                    break
        else:
            raise TFTPError(4, "Transfer timed out")
        
        return self.parse(data)

    def parse(self, data, unpack=struct.unpack):
        buf = buffer(data)
        pkt = {}
        opcode = pkt["opcode"] = unpack("!h", buf[:2])[0]
        if ( opcode == self.RRQ ) or ( opcode == self.WRQ ):
            filename, mode, junk  = string.split(data[2:], "\000")
            pkt["filename"] = filename
            pkt["mode"]     = mode
        elif opcode == self.DATA:
            block  = pkt["block"] = unpack("!h", buf[2:4])[0]
            data   = pkt["data"]  = buf[4:]
        elif opcode == self.ACK:
            block  = pkt["block"] = unpack("!h", buf[2:4])[0]
        elif opcode == self.ERR:
            errnum = pkt["errnum"] = unpack("!h", buf[2:4])[0]
            errtxt = pkt["errtxt"] = buf[4:-1]
        else:
            raise TFTPError(4, "Unknown packet type")

        return pkt

    def retransmit(self):
        self.sock.sendto(self.lastpkt, self.client_addr)
        return

    def connect(self, addr, data):
        self.client_addr = addr
        RRQ  = self.RRQ
        WRQ  = self.WRQ
        DATA = self.DATA
        ACK  = self.ACK
        ERR  = self.ERR

        try:
            pkt    = self.parse(data)
            opcode = pkt["opcode"]
            if opcode not in (RRQ, WRQ):
                raise TFTPError(4, "Bad request")
            
            # Start lock-step transfer
            self.active = 1
            if opcode == RRQ:
                self.handleRRQ(pkt)
            else:
                self.handleWRQ(pkt)

            # Loop until done
            while self.active:
                pkt = self.recv()
                opcode = pkt["opcode"]
                if opcode == DATA:
                    self.recvData(pkt)
                elif opcode == ACK:
                    self.recvAck(pkt)
                elif opcode == ERR:
                    self.recvErr(pkt)
                else:
                    raise TFTPError(5, "Invalid opcode")
        except TFTPError, detail:
            self.sendError( detail[0], detail[1] )

        return

    def recvAck(self, pkt):
        if pkt["block"] == self.blockNumber:
            # We received the correct ACK
            self.handleACK(pkt)
        return

    def recvData(self, pkt):
        if pkt["block"] == self.blockNumber:
            # We received the correct DATA packet
            self.active = ( self.blocksize == len(pkt["data"]) )
            self.handleDATA(pkt)
        return

    def recvErr(self, pkt):
        self.handleERR(pkt)
        self.retransmit()
    
    def sendData(self, data, pack=struct.pack):
        blocksize = self.blocksize
        block     = self.blockNumber = self.blockNumber + 1
        lendata   = len(data)
        format = "!hh%ds" % lendata
        pkt = pack(format, self.DATA, block, data)
        self.send(pkt)
        self.active  = (len(data) == blocksize)

    def sendAck(self, pack=struct.pack):
        block            = self.blockNumber
        self.blockNumber = self.blockNumber + 1
        pkt = pack("!hh", self.ACK, block)
        self.send(pkt)
        
    def sendError(self, errnum, errtext, pack=struct.pack):
        errtext = errtext + "\000"
        format = "!hh%ds" % len(errtext)
        outdata = pack(format, self.ERR, errnum, errtext)
        self.sock.sendto(outdata, self.client_addr)
        return
    
    #
    # Override these handle* methods as needed
    #

    def handleRRQ(self, pkt):
        filename  = pkt["filename"]
        mode      = pkt["mode"]
        self.file = self.readRequest(filename, mode)
        self.sendData( self.file.read(self.blocksize) )
        return

    def handleWRQ(self, pkt):
        filename  = pkt["filename"]
        mode      = pkt["mode"]
        self.file = self.writeRequest(filename, mode)
        self.sendAck()
        return

    def handleACK(self, pkt):
        if self.active:
            self.sendData( self.file.read(self.blocksize) )
        return
    
    def handleDATA(self, pkt):
        self.sendAck()
        data = pkt["data"]
        self.file.write( data )
        
    def handleERR(self, pkt):
        print pkt["errtxt"]
        return

    #
    # You should definitely override these
    #
    def readRequest(self, filename, mode):
        return StringIO.StringIO("")

    def writeRequest(self, filename, mode):
        return StringIO.StringIO()


class TFTPServer:

    """TFTP Server
    Implements a threaded TFTP Server.  Each request is handled
    in its own thread
    """

    def __init__(self, host="", port=16869,
                 conn=TFTPConnection, srcports=[] ):
        self.host = host
        self.port = port
        self.conn = conn
        self.srcports = srcports

        self.sock = None
        self.bind(host, port)

    def bind(self, host, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock = sock
        sock.bind( (host, port) )

    def serve(self):
        data, addr = self.sock.recvfrom(516)
        self.handle(addr, data)     
        
    def forever(self):
        while 1:
            self.serve()

    def handle(self, addr, data):
        if self.srcports:
            nextport = self.srcports.pop(0)
            self.srcports.append( nextport )
            T = self.conn( self.host, nextport )
        else:
            T = self.conn( self.host )
        T.connect(addr,data)

#
# Subclass to create our own TFTP Connection object
#


def tftp_server(data):
    class MyTFTP( TFTPConnection ):
        def readRequest(self, filename, mode):
            print "tftp request:",filename
            return StringIO.StringIO(data)
        def writeRequest(self, filename, mode):
            raise TFTPError(4, "Bad request")
    try:
        serv = TFTPServer("",69,conn=MyTFTP)
        serv.serve()
    except KeyboardInterrupt, SystemExit:
        pass

def SetupSerial(device) :
  print "Setting device '%s' to 112500, 8N1" % device
  fd = os.open(device, os.O_RDWR|os.O_NONBLOCK)
  params = termios.tcgetattr(fd)
  params[0] = termios.IGNBRK        # iflag, 1
  params[1] = 0                     # oflag, 0
  # cflag:  0x18b2
  params[2] = (termios.CS8 |     # 0x30    8-bit data
              termios.CLOCAL |   # 0x800   ignore modem ctrl lines.
              termios.CREAD)    # 0x80
  params[3] = 0                  # lflag
  params[4] = termios.B115200   # ispeed
  params[5] = termios.B115200   # ospeed
  # leave cc flags as-is.
  termios.tcsetattr(fd, termios.TCSANOW, params)


def Upload(image, device, write=False) :

  print "Connecting to serial device..."
  fd = os.open(device, os.O_RDWR|os.O_NONBLOCK|os.O_NOCTTY)
  m = fdpexpect.fdspawn(fd)
  m.setecho(False)

  print "Waiting for device to be switched on...."

  # Wait for device to power up
  m.expect("to enter boot menu..")

  # Three spaces to interrupt the boot
  m.send("   ")
  m.expect("Please enter your number:")

  # Set parameters
  m.send("4")
  m.expect("serial number: ")
  m.send("\n")    # unchanged
  m.expect("hardware version: ")
  m.send("\n")    # unchanged
  m.expect("AA-AA-AA-AA-AA-AA\): ")
  m.send("00-00-01-02-03-04\n")
  m.expect("\(between 1-8\): ")
  m.send("8")
  m.expect("IP address for this board: ")
  m.send("%s\n" % opts.address)
  m.expect("enter your number:")
  m.send("2")
  m.expect("Enter your option:")
  m.send("s")
  m.expect("TFTP Server IP : ")
  m.send("%s\n" % TFTP_HOST)
  m.expect("Remote File Name : ")
  m.send("boot\n")
  m.expect("Enter your option:")
  m.send("d")
  m.expect("Enter your option:")
  m.send("x")
  m.expect("enter your number:")
  if write:
      print "Writing image to Flash..."
      m.send("7")    # write to flash
  else:
      print "Starting from SDRAM..."
      m.send("6")    # start from DRAM
  # Done with expect, close the device
  m.read_nonblocking()
  del m

  # re-connect to serial device
  fd = os.open(device, os.O_RDWR|os.O_NONBLOCK|os.O_NOCTTY)
  m = fdpexpect.fdspawn(fd)

  # Connect to the terminal
  m.interact()


def check_csys(fname):
    csys = "CSYS\x00\x00\x50\x80"
    return open(fname).read(8) == csys

def check_gzip(data):
    return data[:2] == "\x1f\x8b"

def gzip_filename(data):
    return data[10:data.find("\000",10)]

if __name__ == '__main__':
    fname = args[0]
    data = open(fname).read()

    if check_gzip(data):
        print "Gzip Image: %s (Original File: %s, Length: %dKb)" % \
                        (fname,gzip_filename(data),len(data)/1024)
    else:
        raise Exception("Invalid Image format")

    if len(data) > (1984 * 1024):
        raise Exception("Image too large (max size 1984Kb)")
        
    try:
        socket.socket(socket.AF_INET, socket.SOCK_DGRAM).bind(("",69))
        thread.start_new_thread(tftp_server,(data,))
        SetupSerial(opts.device)
        Upload(fname,opts.device,opts.write)
    except socket.error, e:
        print "Unable to bind to TFTP port:", e[1]

