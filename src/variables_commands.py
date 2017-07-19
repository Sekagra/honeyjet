import jinja2
import re
import json

FACTORY_VARIABLES_FILE = "conf/factory_variables.json"
DEFAULT_VARIABLES_FILE = "conf/default_variables.json"
ENVIRONMENT_VARIABLES_FILE = "conf/environment_variables.json"
UNIQUE_VARIABLES_FILE = "conf/unique_variables.json"
RANGES_FILE = 'conf/PJL_INFO_VARIABLES'
TEMPLATE_DIR = "conf"

# Common retrieval of output strings for INFO commands using jinja templates
def getOutput(commandId):
    # get the template environment
    template = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_DIR)).get_template(commandId)
    temp = variables['default'].copy()
    temp.update(variables['unique'])
    return template.render(temp) + '\n\n'

# get the specified variable value from the environment variables
def PJL_INQUIRE(line, socket):
    value = None
    name = __getVariableName(line)
    if name in variables['environment']:
        value = variables['environment'][name]
    elif name in variables['unique']:
        value = variables['unique'][name]
    if value is not None:
        socket.write(line)
        socket.write(str(value) + '\n')
        socket.flush()

# get the specified variable value from the default variables
def PJL_DINQUIRE(line, socket):
    value = None
    name = __getVariableName(line)
    if name in variables['default']:
        value = variables['default'][name]
    elif name in variables['unique']:
        value = variables['unique'][name]
    if value is not None:
        socket.write(line)
        socket.write(str(value) + '\n')
        socket.flush()

# set the value in the environment variables dictionary
def PJL_SET(line, socket):
    name = __getVariableName(line)
    value = __getVariableValue(line)
    if name in variables['environment'] and __checkValue(name, value):
        variables['environment'][name] = value
    #set can be used to hard reset the pagecount, check uniqure variables
    if name in variables['unqiue'] and __checkValue(name, value):
        variables['unique'][name] = value
        with open(UNIQUE_VARIABLES_FILE, 'w') as outfile:
            json.dump(variables['unique'], outfile)   

# set the value in the default variables dictionary
def PJL_DEFAULT(line, socket):
    name = __getVariableName(line)
    value = __getVariableValue(line)
    if name in variables['default'] and __checkValue(name, value):
        variables['default'][name] = value
        with open(DEFAULT_VARIABLES_FILE, 'w') as outfile:
            json.dump(variables['default'], outfile)

# Reset current values and default values to the factory values
def PJL_INITIALIZE(line, socket):
    variables['default'] = variables['factory'].copy()
    with open(DEFAULT_VARIABLES_FILE, 'w') as outfile:
        json.dump(variables['default'], outfile)
    variables['environment'] = variables['default'].copy()

# Reset current values to the default values
def PJL_RESET(line, socket):
    variables['environment'] = variables['default'].copy()

def incPageCount():
    # increase page count
    variables['unique']['PAGECOUNT'] = variables['unique']['PAGECOUNT'] + 1
    with open(UNIQUE_VARIABLES_FILE, 'w') as outfile:
        json.dump(variables['unique'], outfile)  

def __getVariableName(input):
    result = re.search('@PJL (INQUIRE|DINQUIRE|SET|DEFAULT) ([^=]+)', input)
    if result is not None:
        return result.group(2).lstrip().rstrip().replace(":", "_").replace(" ", "_")

def __getVariableValue(input):
    result = re.search('@PJL (SET|DEFAULT) ([^=]+)= ?(.*)', input)
    if result is not None:
        value = result.group(3).rstrip('\n')
        return int(value) if value.isdigit() else value

def __checkValue(k, v):
    if k in ranges:
        if ranges[k][0] == "RANGE":
            return int(ranges[k][1][0]) < int(v) < int(ranges[k][1][1])
        elif ranges[k][0] == "ENUMERATED":
            return v in ranges[k][1]
        elif ranges[k][0] == "STRING":
            return True
    return False

def __parseValueRange():
    # read ranges dynamically from PJL_INFO_VARIABLES file
    d = {}
    regex = re.compile("([A-Z0-9: ]+)=([^\[])*\[[0-9]+ (ENUMERATED|RANGE|STRING)( READONLY)?\]\n((\t([A-Z0-9 \.]+)?\n)*)")
    with open(RANGES_FILE, 'r') as varfile:
        content = varfile.read()
        for r in regex.findall(content):
            d[r[0]] = (r[2], [x.lstrip().rstrip() for x in r[4].split('\n\t')])
    return d


# DEVICE ATTENDANCE COMMANDS

# RDYMSG
def PJL_RDYMSG(line, socket):
    result = re.search('@PJL RDYMSG DISPLAY.?=.?(.+)', line)
    if result is not None:
        variables['unique']['DISPLAY2'] = result.group(1).lstrip('"').rstrip('"')
        with open(UNIQUE_VARIABLES_FILE, 'w') as outfile:
            json.dump(variables['unique'], outfile)   

# enhancements: OPMSG, STMSG
# test when having physical access as it kills the printer temporarily


ranges = __parseValueRange()

variables = {}
# Central json for variables
f = open(FACTORY_VARIABLES_FILE, 'r')
variables['factory'] = json.load(f)
f.close()
f = open(DEFAULT_VARIABLES_FILE, 'r')
variables['default'] = json.load(f)
f.close()
f = open(DEFAULT_VARIABLES_FILE, 'r')
variables['environment'] = json.load(f)
f.close()
f = open(UNIQUE_VARIABLES_FILE, 'r')
variables['unique'] = json.load(f)
f.close()

