#!/usr/bin/env python

import sys
import os
import json
import datetime
from gevent import socket
from gevent.server import StreamServer
from commands import *
from file_system_commands import *
from variables_commands import *

LOG_DIR = "logs"

def processCommand(line, socket):
    line = line.lstrip('%-12345X')
    if line.startswith("@PJL"):
        cmd = line.rstrip().lstrip('@').replace(' ', '_')        
        # delegate to commands if prefix matches with an existing function
        matchingCommand = findMatchingCommand(cmd)
        if matchingCommand:
            matchingCommand(line, socket)
        # for fixed output stored in a file, get the file content
        elif cmd in outputs:
            #socket.write(line) # input no longer repeated as it can differ
            socket.write(getOutput(cmd))
            socket.flush()
        # for info commands not implemented, return "?"
        elif cmd.startswith('PJL_INFO_') or cmd.startswith('PJL_INQUIRE') or cmd.startswith('PJL_DINQUIRE'):
            socket.write(line)  # Repeat the input as this is done by the printer
            socket.write('"?"\r\n\r\n')
            socket.flush()
        #print nothing in all other cases

def handle_connection(sock, address):
    # create log for this session
    logName = "{}:{}_{}".format(address[0], address[1], str(datetime.datetime.now()).replace(' ', 'T'))
    logPath = os.path.join(LOG_DIR, logName)

    with open(logPath + '.pcl', 'wb') as log:
        fp = sock.makefile()
        while True:
            line = fp.readline()
            if line:
                log.write(line)
                processCommand(line, fp)
            else:
                break
        sock.shutdown(socket.SHUT_WR)
        sock.close()

    # print log to pdf via GhostPCL6
    os.system("bin/pspcl6 -o {} -sDEVICE=pdfwrite {}".format(logPath + ".pdf", logPath + ".pcl"))
    if os.path.isfile(logPath + ".pdf"):
        incPageCount()

def findMatchingCommand(cmd):
    for k,v in cmds.iteritems():
        if cmd.startswith(k):
            return v


cmds = {}
# get functions starting with PJL and files providing output
this = sys.modules[__name__]
for f in dir():
    if f.startswith("PJL"):
        cmds[f] = getattr(this, f)

# get files faking output of informational commands
outputs = []
for f in os.listdir(TEMPLATE_DIR):
    if f.startswith("PJL"):
        outputs.append(f)

server = StreamServer(('', 9100), handle_connection)
server.serve_forever()