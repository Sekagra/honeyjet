import os
import re

UNIQUE_VARIABLES_FILE = "conf/unique_variables.json"

# STATUS READBACK COMMANDS

def PJL_ECHO(line, socket):
    socket.write(line + '\n')
    socket.flush()

