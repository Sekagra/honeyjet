import os
import re
import shutil
import time

# FILE SYSTEM COMMANDS
FS_DIR = "filesystem"
FS_DIR_RESET = "filesystem_reset"
FS_BASE_DIR = os.path.join(FS_DIR, "hpmnt/dsk_ram0/")

def PJL_FSAPPEND(line, socket):
    m = re.search('^@PJL FSAPPEND FORMAT:BINARY SIZE=(?P<size>[0-9]+) NAME="(?P<path>0:[\\\/A-Za-z0-9\.-_]*)"', line)
    if m is not None:
        size = int(m.group('size'))
        # Get next line from user
        content = socket.readline()

        path = __validatePath(m.group('path'))
        # remove files or empty directories
        if path is not None and size <= len(content): #somehow a real printer inflates the size by 1 (for whole files LF is always appended)
            if not os.path.isdir(path) and path.startswith(os.path.abspath(FS_BASE_DIR)):
                with open (path, 'a') as f: f.write(content[:size])


def PJL_FSDIRLIST(line, socket):
    # Parse parameter (they are ALL needed for a response)
    # e.g. @PJL FSDIRLIST NAME="0:\" ENTRY=1 COUNT=5
    m = re.search('^@PJL FSDIRLIST NAME="(?P<path>0:[\\\/A-Za-z0-9\.-_]*)" ENTRY=(?P<offset>[0-9]+) COUNT=(?P<count>[0-9]+)', line)
    if m is not None:
        offset = int(m.group('offset'))
        count = int(m.group('count'))
        path = __validatePath(m.group('path'))

        # replay command without ENTRY and COUNT
        cmd_replay = '@PJL FSDIRLIST NAME="' + m.group('path') + '" ENTRY=' + str(offset)

         # execute ls and parse the result to represent the output of a legit printer
        if path is not None and 0 < offset and offset <= 65535 and 0 < count and count <= 65535:
            #check path existence
            if os.path.exists(path):
                # iterate over directory
                elements = ['.', '..']
                files = os.listdir(path)
                files.sort()
                elements.extend(files)
                # apply <offset> and <count>
                elements = elements[offset-1:offset+count-1]
                # get correct type (DIR or FILE) and the size in case of files
                response = "\r\n".join([e + __getFileType(os.path.join(path, e)) + __getFileSize(os.path.join(path, e)) for e in elements])
            else:
                #Not found error
                response = 'FILEERROR=3'

            socket.write("{}\r\n{}\r\n".format(cmd_replay, response))
            socket.flush()

def PJL_FSDELETE(line, socket):
    m = re.search('^@PJL FSDELETE NAME="(?P<path>0:[\\\/A-Za-z0-9\.-_]*)"', line)
    if m is not None:
        path = __validatePath(m.group('path'))
        # remove files or empty directories
        if path is not None and os.path.exists(path) and path.startswith(os.path.abspath(FS_BASE_DIR)):
            if os.path.isdir(path):
                if os.listdir(path) == []:  # is empty?
                    os.rmdir(path)
            else:
                os.remove(path)
    # no output, even if the location does not exist

def PJL_FSDOWNLOAD(line, socket):
    m = re.search('^@PJL FSDOWNLOAD FORMAT:BINARY SIZE=(?P<size>[0-9]+) NAME="(?P<path>0:[\\\/A-Za-z0-9\.-_]*)"', line)
    if m is not None:
        size = int(m.group('size'))
        # Get next line from user
        content = socket.readline().rstrip() + '\n'

        path = __validatePath(m.group('path'))
        # don't write a file if the size is larger than the inserted content
        if path is not None and size <= len(content) and path.startswith(os.path.abspath(FS_BASE_DIR)):
            if not os.path.isdir(path):
                with open (path, 'w') as f: f.write(content[:size])

def PJL_FSINIT(line, socket):
    # rename the file system at the moment of resetting
    os.rename(FS_DIR, FS_DIR + "_" + str(int(time.time())))

    # remove and restore the old file system
    #shutil.rmtree(FS_DIR)
    shutil.copy(FS_DIR_RESET, FS_DIR)

def PJL_FSMKDIR(line, socket):
    m = re.search('^@PJL FSMKDIR NAME="(?P<path>0:[\\\/A-Za-z0-9\.-_]*)"', line)
    if m is not None:
        path = __validatePath(m.group('path'))
        if path is not None and not os.path.exists(path) and path.startswith(os.path.abspath(FS_BASE_DIR)):
            os.mkdir(path)

def PJL_FSQUERY(line, socket):
    m = re.search('^@PJL FSQUERY NAME="(?P<path>0:[\\\/A-Za-z0-9\.-_]*)"', line)
    if m is not None:
        cmd_replay = '@PJL FSQUERY NAME="' + m.group('path') + '"'

        path = __validatePath(m.group('path'))
        #check path existence
        if path is not None and os.path.exists(path):
            response = __getFileType(path) + __getFileSize(path)
        else:
            #Not found error
            response = '\r\nFILEERROR=3'
        
        socket.write("{}{}\r\n".format(cmd_replay, response))
        socket.flush()

def PJL_FSUPLOAD(line, socket):
    m = re.search('^@PJL FSUPLOAD NAME="(?P<path>0:[\\\/A-Za-z0-9\.-_]*)" OFFSET=(?P<offset>[0-9]+) SIZE=(?P<size>[0-9]+)', line)
    if m is not None:
        offset = int(m.group('offset'))
        size = int(m.group('size'))
        path = __validatePath(m.group('path'))
        if path is not None and not os.path.isdir(path):
            if os.path.exists(path):
                size = min(os.path.getsize(path)+1-offset, size)
                with open (path, 'r') as f: 
                    response = f.read()
                    response = response[offset:offset+size]
                cmd_replay = '@PJL FSUPLOAD FORMAT:BINARY NAME="{}" OFFSET={} SIZE={}'.format(m.group('path'), str(offset), str(size))
            else:
                cmd_replay = '@PJL FSUPLOAD NAME="' + m.group('path') + '"'
                response = '\r\nFILEERROR=3'  #Not found error

            socket.write("{}\r\n{}".format(cmd_replay, response))
            
            socket.flush()

def __validatePath(p):
    # replace '0:' with base path
    p = p.replace('\\', '/')
    p = p.rstrip('/')
    p = p.replace('0:', FS_BASE_DIR)
    p = os.path.abspath(p)   #evaluate path
    #confirm that the path is valid and still contained in the filesystem directory
    if p.startswith(os.path.abspath(FS_DIR)):
        return p

def __getFileType(f):
    if os.path.isdir(f):
        return " TYPE=DIR"
    elif os.path.isfile(f):
        return " TYPE=FILE"
    return ""

def __getFileSize(f):
    if __getFileType(f) == " TYPE=FILE":
        return " SIZE=" + str(os.path.getsize(f)) #somehow a real printer 
    return ""