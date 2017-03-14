#!/usr/bin/env python
# ############################################################################
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
#
# TECHNICAL ASSISTANCE CENTER (TAC) SUPPORT IS NOT AVAILABLE FOR THIS SCRIPT.
# 
# Always check for the latest version via dCloud.cisco.com
# ############################################################################
# This sample script illustrates how to run a Path Trace in APIC-EM via it's
# REST APIs. This includes
# 1) posting a path trace request
# 2) checking it's task status
# 3) querying and parsing the resulting path trace JSON document
# ############################################################################
# $Id$
# ############################################################################

##############################################################################
# Imports below
##############################################################################
from pprint import pprint
from pprint import pformat
from tabulate import tabulate

import datetime
import io
import time
import json
import requests
import sys
import os
from asciimatics.effects import Cycle, Stars
from asciimatics.renderers import FigletText
from asciimatics.scene import Scene
from asciimatics.screen import Screen

# Disable Certificate warning
try:
  requests.packages.urllib3.disable_warnings()
except:
  pass


reload(sys)
sys.setdefaultencoding('utf-8')


##############################################################################
# Variables below
##############################################################################


APIC_IP = 'sandboxapic.cisco.com:9443'
APIC_BASE = 'https://%s/api/v1' % APIC_IP
APIC_LOGIN = 'blackbelts'
APIC_PASSWD = 'Blackb3lts'



##############################################################################
# Start API Session APIC_EM
##############################################################################
apic_credentials = json.dumps({'username':APIC_LOGIN,'password':APIC_PASSWD})
tmp_headers = {'Content-type': 'application/json'}
tmp_get = '%s/ticket' % APIC_BASE
#print('My GET Request: ' + tmp_get)
print("Connecting to APIC-EM ..."+'\r\n')
req = requests.post(tmp_get, data=apic_credentials, verify=False, headers=tmp_headers)
#print('APIC-EM Response: ' + req.text)

# Add session ticket to my http header for subsequent calls
apic_session_ticket = req.json()['response']['serviceTicket']
apic_headers = {'Content-type': 'application/json', "X-Auth-Token": apic_session_ticket}
print("Connecting to APIC-EM Done" +'\r\n')

##############################################################################
# Start API Session SPARK
##############################################################################
SPARK_ROOM_NAME = 'SDN BB Hands-on'
SPARK_ROOM_ID = None

SPARK_BASE = 'https://api.ciscospark.com/v1'
SPARK_MESSAGES = '%s/messages' % SPARK_BASE 
SPARK_ROOMS = '%s/rooms' % SPARK_BASE 

# Get your access token: 
# 1) Login to developer.ciscospark.com 
# 2) Copy the Access Token from top-right corner portrait icon
# 3) replace YOUR-ACCESS-TOKEN-HERE in the line below, leave preceding "Bearer " intact  
SPARK_TOKEN = 'Bearer PLACE_YOUR_TOKEN_HERE'
SPARK_HEADERS = {'Content-type': 'application/json', 'Authorization': SPARK_TOKEN}
print("Connecting to SPARK ..."+'\r\n')
r = requests.get(SPARK_ROOMS, headers=SPARK_HEADERS, verify=False)
j = json.loads(r.text)

for tmproom in j['items']:
	if tmproom['title'] == SPARK_ROOM_NAME:
		SPARK_ROOM_ID = tmproom['id']
    	print("Found room ID for '" + SPARK_ROOM_NAME + "' : " + SPARK_ROOM_ID)
    	break
        
	if SPARK_ROOM_ID is None:
  		print("Failed to find room ID for '" + SPARK_ROOM_NAME + "'")
  		sys.exit(1)
print("Connecting to SPARK Done"+'\r\n')
# ############################################################################
# Post to Spark Room
# ############################################################################
def sparkpost(msg):
	m = json.dumps({'roomId':SPARK_ROOM_ID,'text':msg})
	#print('Spark Request: ' + SPARK_MESSAGES + m)
	r = requests.post(SPARK_MESSAGES, data=m, headers=SPARK_HEADERS, verify=False)
	#print('Spark Response: ' + r.text)
	return;
	
# ############################################################################
# Save to File
# ############################################################################
def savetofile(content):
	devicename = filename = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ' -inventory.txt'
	file_Conf = open(devicename, 'w')
	file_Conf .write(content)
	file_Conf.close()
	return;


##############################################################################
# Get a Device Count Request
##############################################################################
def devicecount():
	tmp_count = '%s/network-device/count' % APIC_BASE
	#print('My GET Request: ' + tmp_count)
	req = requests.get(tmp_count,verify=False, headers=apic_headers)
	#Parsing
	parsed_result=req.json()
	response=parsed_result['response']
	return(response);


##############################################################################
# Get a Device Inventory (Mac Address + hostname + Mgmt IP + SKU)
##############################################################################
def getdeviceinventory():
	#global device_list
	tmp_inv = '%s/network-device' % APIC_BASE
	dev_inv= requests.get(tmp_inv,verify=False, headers=apic_headers)
	parsed_result= dev_inv.json()
	dev_list=parsed_result['response']
	
	device_list = []
	i = 0

	for item in dev_list:
		i+=1
		device_list.append([i,item["macAddress"],item["hostname"],item["managementIpAddress"],item["platformId"],item["id"]])
	return(device_list);

##############################################################################
# Create a formated list of Device Inventory
##############################################################################

def creatematrix(list):	
	tableau=tabulate(list, headers=['Index','Mac Address','Hostname','Mgmt IP','SKU','ID'], tablefmt="fancy_grid")
	return(tableau);


##############################################################################
# Save Config to File
##############################################################################
def saveconf(id,device_list):
	dev_id = device_list[int(id)-1][5]
	##Request to get the config base on the ID
	tmp_conf= APIC_BASE + '/network-device/' + dev_id + '/config'
	req = requests.get(tmp_conf, verify=False, headers=apic_headers)
	parsed_result=req.json()
	config=parsed_result['response']
	##Save to File
	filename = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + device_list[int(id)-1][2] +' -config.txt'
	savetofile(filename, config);

##############################################################################
# Test reachability of a device based on the device ID
##############################################################################
def reachabletest(id,device_list):
	ip_address = device_list[int(id)-1][3]
	tmp_conf=APIC_BASE + '/reachability-info/ip-address/' + ip_address
	req=requests.get(tmp_conf, verify=False, headers=apic_headers)
	parsed_result = req.json()['response']
	return(parsed_result);
	
##############################################################################
# Happy End
##############################################################################

def happyend(screen):
    effects = [
        Cycle(
            screen,
            FigletText("FRENCH TEAM", font='big'),
            int(screen.height / 2 - 8)),
        Cycle(
            screen,
            FigletText("ROCKS!", font='big'),
            int(screen.height / 2 + 3)),
        Stars(screen, 200)
    ]
    screen.play([Scene(effects, 500)])
    
##############################################################################
# Core Program
##############################################################################

os.system('cls' if os.name == 'nt' else 'clear')
devcount=devicecount()
deviceinventory = getdeviceinventory()
matrix = creatematrix(deviceinventory)



while True:
	os.system('cls' if os.name == 'nt' else 'clear')
	print('=================================================')
	print ( " Device Count " + str(devcount))
	print('================================================='+'\r\n')
	print(matrix+'\r\n')
	print("********* MENU *********")
	print("1. Save Inventory")
	print("2. Save Device Config")
	print("3. Test Reachibility")
	print("4. Quit")
	print("************************")
	answer = raw_input(" Please Enter you choice ")


	if (int(answer) == 1):
		while True:
			try:
				savetofile(str(matrix))
				msg= (" Inventory has been saved by " + APIC_LOGIN + '\r\n')
				print(" A notification has been sent to the Spark Room " + SPARK_ROOM_NAME + '\r\n' )
				sparkpost(msg)
				break
			except KeyboardInterrupt:
				print(" Exiting")
				sys.exit()
			except:
				print ("Oups, something wrong here, try again...")
	elif (int(answer) == 2):
		while True:
			try:
				print('=================================================')
				id = raw_input('\r\n'+"Enter Device Index to save the config: ")
				print('================================================='+'\r\n')
				saveconf(id,deviceinventory)
				msg= (deviceinventory[int(id)-1][2] + " config has been saved by " + APIC_LOGIN + '\r\n')
				print(msg)
				print(" A notification has been sent to the Spark Room " + SPARK_ROOM_NAME + '\r\n' )
				sparkpost(msg)
				break
			except KeyboardInterrupt:
				print(" Exiting")
				sys.exit()
			except:
				print ("Unable to get the config of this device, try again...")
	elif (int(answer) == 3):
		while True:
			try:
				print('=================================================')
				id = raw_input('\r\n'+"Enter Device Index : ")
				print('================================================='+'\r\n')
				result=reachabletest(id,deviceinventory)
				if (result['reachabilityStatus'] == "REACHABLE"):
					msg = (deviceinventory[int(id)-1][2] + " is reachable " + '\r\n')
					print(msg)
					print(" A notification has been sent to the Spark Room " + SPARK_ROOM_NAME + '\r\n' )
					sparkpost(msg)
				else:
					print(deviceinventory[int(id)-1][2] + " is not reachable " + '\r\n')
				break
			except KeyboardInterrupt:
				print(" Exiting")
				sys.exit()
			except:
				print ("Oups, something wrong here, try again...")
	elif (int(answer) == 4):
		print(" Bye !!")
		Screen.wrapper(happyend)
	
print('\r\n'+"That's all Folks, See You "+'\r\n')


##############################################################################
# EOF
##############################################################################





