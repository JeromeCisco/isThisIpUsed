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

# Disable Certificate warning
try:
  requests.packages.urllib3.disable_warnings()
except:
  pass

reload(sys)
sys.setdefaultencoding('utf-8')

##############################################################################
# READ PARAMETERS
##############################################################################

parser = argparse.ArgumentParser()

parser.add_argument('-c', action='store', dest='config_file',help='Config file name')
parser.add_argument('-m', action='store', dest='macaddress_file',help='MAC address file name')
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
# READ CONFIGURED MAC ADDRESSES AND PUT THEM IN AN ARRAY
##############################################################################

macaddressfile = open(results.macaddress_file, "r")
macaddresstable = []
for line in macaddressfile:
  line.strip()
  if re.match("[0-9a-f]{2}([-:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", line.lower()):
    macaddresstable.append(line)
    print "Reading MAC address in file MAC file: %s" % line
  else:
    print "Bad MAC address in file MAC file: %s" % line

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
    host_list.append([i,str(item["hostMac"]),str(item["hostIp"])])
  return host_list;

##############################################################################
# Get all prioritized IP addresses
##############################################################################

def getPrioritized():
  url = '%s/policy/flow' %APIC_BASE
  req_inv = requests.get(url,verify=False, headers=apic_headers)
  parsed_result= req_inv.json()
  req_list=parsed_result['response']
  prioritized_host_list = []
  for item in req_list:
    prioritized_host_list.append([str(item["sourceIP"]),str(item["id"]),str(item["protocol"])])
  return prioritized_host_list;

##############################################################################
# Prioritize an IP
##############################################################################

def prioritizeIp(Ip):
  url = '%s/policy/flow' % APIC_BASE
  payload = {"flowType": "VIDEO", "sourceIP": Ip, "protocol": "tcp"}
  r = requests.post(url, data=json.dumps(payload), verify=False, headers=apic_headers)
  payload = {"flowType": "VIDEO", "sourceIP": Ip, "protocol": "udp"}
  r = requests.post(url, data=json.dumps(payload), verify=False, headers=apic_headers)

##############################################################################
# Find a MAC address in APIC-EM in get its IP address
##############################################################################

def getIpByMac(mac):
  url = '%s/host?hostMac=%s' %(APIC_BASE,mac)
  req_inv = requests.get(url,verify=False, headers=apic_headers)
  parsed_result= req_inv.json()
  req_list=parsed_result['response']
  return str(req_list[0]["hostIp"]);

##############################################################################
# Remove a priority based on its ID
##############################################################################

def priorityRemove(id):
  url = '%s/policy/flow/%s' %(APIC_BASE,id)
  req_inv = requests.delete(url,verify=False, headers=apic_headers)

##############################################################################
# Find a MAC address in APIC-EM in get its IP address
##############################################################################

def getMacByIp(ip):
  url = '%s/host?hostIp=%s' %(APIC_BASE,ip)
  req_inv = requests.get(url,verify=False, headers=apic_headers)
  parsed_result= req_inv.json()
  req_list=parsed_result['response']
  return str(req_list[0]["hostMac"]);

##############################################################################
# Core Program
##############################################################################

prioritized_ip_list =  getPrioritized()

##############################################################################
# For all current priority rules, validate they are still required
##############################################################################

for item in prioritized_ip_list:
  mac = getMacByIp(item[0])
  if mac in macaddresstable:
    print "MAC address %s is currently prioritized and needs to be kept" % mac
    macaddresstable.remove(mac)
  else:
    print "MAC address %s is currently prioritized and needs to be removed" % mac
    priorityRemove(item[1])
    print "MAC address %s removed" % mac

##############################################################################
# Prioritize all MAC not yet prioritized
##############################################################################

for mac in macaddresstable:
  print 'MAC address %s configured' % mac
  ip = getIpByMac(mac)
  print 'Prioritizing IPv4 address %s corresponding to MAC address %s...' % (ip,mac)
  prioritizeIp(ip) 
  print 'IPv4 address %s prioritized' % ip
