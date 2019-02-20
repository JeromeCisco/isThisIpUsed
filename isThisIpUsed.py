#!/usr/bin/env python

##############################################################################
# Imports below
##############################################################################
from pprint import pprint
from pprint import pformat

import datetime
import io
import time
import json
import requests
import sys
import os
import ConfigParser
import argparse
import re

# Check Python version
if sys.version_info.major == 3:
  raise "Works only with Python 2 at the time being... Sorry... but please feel free to contribute!"
  exit()

# Disable Certificate warning
try:
  requests.packages.urllib3.disable_warnings()
except:
  pass

reload(sys)
sys.setdefaultencoding('utf-8')

if len(sys.argv) < 2:
  print "Usage: isThisIpUsed.py -c file.conf"
  exit()


##############################################################################
# READ PARAMETERS
##############################################################################

parser = argparse.ArgumentParser()

parser.add_argument('-c', action='store', dest='config_file',help='Config file name')
parser.add_argument('--version', action='version', version='%(prog)s 1.0')

results = parser.parse_args()

##############################################################################
# READ VARIABLES
##############################################################################

config = ConfigParser.ConfigParser()
config.read(results.config_file)
APIC_IP = config.get("APIC_Parameters","APIC_IP")
APIC_LOGIN = config.get("APIC_Parameters","APIC_LOGIN")
APIC_PASSWD = config.get("APIC_Parameters","APIC_PASSWD")
PROXY = config.get("APIC_Parameters","PROXY")

# Creates APIC_BASE url based on APIC_IP
APIC_BASE = 'https://%s/api/v1' % APIC_IP

# Makes Proxy Exception if configured 
if PROXY == "No":
  os.environ['no_proxy'] = '%s' % APIC_IP

##############################################################################
# Start API Session APIC_EM
##############################################################################

apic_credentials = json.dumps({'username':APIC_LOGIN,'password':APIC_PASSWD})
tmp_headers = {'Content-type': 'application/json'}
tmp_get = '%s/ticket' % APIC_BASE
print("Connecting to APIC-EM ..."+'\r\n')
req = requests.post(tmp_get, data=apic_credentials, verify=False, headers=tmp_headers)

# Add session ticket to my http header for subsequent calls
apic_session_ticket = req.json()['response']['serviceTicket']
apic_headers = {'Content-type': 'application/json', 'X-Auth-Token': apic_session_ticket}
print("Connecting to APIC-EM Done" +'\r\n')

##############################################################################
# Get a Host Inventory (Mac Address + IP address)
##############################################################################

def gethostinventory():
  #global host_list
  url = '%s/host' % APIC_BASE
  req_inv = requests.get(url,verify=False, headers=apic_headers)
  parsed_result= req_inv.json()
  req_list=parsed_result['response']
  host_list = []
  i = 0
  for item in req_list:
    i = i + 1
    host_list.append([i,str(item["hostMac"]),str(item["hostIp"]),str(item["connectedInterfaceName"]),str(item["connectedNetworkDeviceIpAddress"])])
  return host_list;

##############################################################################
# Get IPs on network devices
##############################################################################

def getinterfaceinventory():
  #global host_list
  url = '%s/interface' % APIC_BASE
  req_inv = requests.get(url,verify=False, headers=apic_headers)
  parsed_result= req_inv.json()
  req_list=parsed_result['response']
  interface_list = []
  i = 0
  for item in req_list:
    i = i + 1
    interface_list.append([i,str(item["ipv4Address"]),str(item["ipv4Mask"]),str(item["portName"]),str(item["serialNo"])])
  return interface_list;


##############################################################################
# Core Program
##############################################################################

ip = raw_input(" [>] Enter IPv4 address to check:  ")

if re.match(r'^((\d{1,2}|1\d{2}|2[0-4]\d|25[0-5])\.){3}(\d{1,2}|1\d{2}|2[0-4]\d|25[0-5])$', ip):  
  print "\nValid IPv4\n"  
else:
  print "\nInvalid IPv4... start again and please don't screw up next time...\n"
  quit()

##############################################################################
# Checking if this IP is used by a host...
##############################################################################

print "Checking if this IP is used by a host...\n"
isUsed = 0
for line in gethostinventory():
  if line[2] == ip:
    isUsed = 1
    break

if isUsed == 1:
  print ("IP address %s is currently used by host with MAC address %s on interface %s of switch with IP address %s\n" % (ip,line[1],line[3],line[4]))
else:
  print ("IP address %s is currently not used by a host\n" % ip)

##############################################################################
# Checking if this IP is used on a network device...
##############################################################################

print "Checking if this IP is used on a network device...\n"
isUsed = 0
for line in getinterfaceinventory():
  if line[1] == ip:
    isUsed = 1
    break

if isUsed == 1:
  print ("IP address %s is currently used by network device with Serial number %s on interface %s\n" % (ip,line[4],line[3]))
else:
  print ("IP address %s is currently not used by a network device\n" % ip)

