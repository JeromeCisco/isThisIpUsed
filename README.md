# isThisIpUsed

Written by Jerome Durand, Gilles Clugnac and Benjamin Oschmann
aka the Pragmatic Dinosaurs during the CISCO SDN Blackbelts
Summit in Berlin on March 2017

This simple app tells you if an IPv4 address is already used 
in your network
  - if the IP belongs to the host connected on your network
  - if the IP is configured on one of the network devices

This app relies on the great and only APIC-EM controller which
abstract the network.
You will need to provide all APIC-EM details (IP and credentials)
in a configuration file. "isThisIpUsed.conf" file is
provided as an example.

All rights reserved - copyright Jerome Durand
If you copy you will have a free pass for Guantanamo
