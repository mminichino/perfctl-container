#!/usr/bin/env python

'''
Create Bind zone file from template
'''

import os
import sys
import argparse
import json
import re
import ipaddress
from jinja2 import Template, FileSystemLoader, Environment
import netifaces
import subprocess
from pwd import getpwnam
import getpass

class zoneConfig(object):

    def __init__(self):
        self.parse_args()

        if self.dnsKeyFileUser:
            self.homeDir = "/home/" + self.dnsKeyFileUser
        else:
            self.homeDir = os.environ['HOME']
        self.dnsKeyFileDir = self.homeDir + "/.dns"
        self.dnsKeyFile = self.homeDir + "/.dns/dns.key"

        if not self.zoneTemplateFile:
            self.zoneTemplateFile = 'zone.template'
        if not self.arpaTemplateFile:
            self.arpaTemplateFile = 'in-addr.arpa.template'
        if not self.cfgTemplateFile:
            self.cfgTemplateFile = 'named.conf.template'
        if not self.resolvTemplateFile:
            self.resolvTemplateFile = 'resolv.conf.template'

        self.create_files()

    def create_files(self):
        zoneTemplateFile = self.zoneTemplateFile
        arpaTemplateFile = self.arpaTemplateFile
        cfgTemplateFile = self.cfgTemplateFile
        resolvTemplateFile = self.resolvTemplateFile
        hostAddrs = []
        runCommand = []
        ip_address = None
        in_addr_arpa = None
        ip_arpa_address = None
        tsig_key = None
        userUid = None
        userGid = None
        if self.dnsKeyFileUser:
            try:
                userUid = getpwnam(self.dnsKeyFileUser).pw_uid
                userGid = getpwnam(self.dnsKeyFileUser).pw_gid
            except Exception as e:
                print("Could not get uid and gid for user: %s" % str(e))
                sys.exit(1)
        else:
            userUid = getpwnam(getpass.getuser()).pw_uid
            userGid = getpwnam(getpass.getuser()).pw_gid

        try:
            if not os.path.exists(self.dnsKeyFileDir):
                os.makedirs(self.dnsKeyFileDir)
                if self.dnsKeyFileUser:
                    os.chown(self.dnsKeyFileDir, userUid, userGid)
        except Exception as e:
            print("Could not make dns key file directory: %s" % str(e))
            sys.exit(1)

        try:
            templateLoader = FileSystemLoader(searchpath="./")
            templateEnv = Environment(loader=templateLoader)
            zoneTemplate = templateEnv.get_template(zoneTemplateFile)
        except Exception as e:
            print("Could not process zone template file: %s" % str(e))
            sys.exit(1)

        try:
            templateLoader = FileSystemLoader(searchpath="./")
            templateEnv = Environment(loader=templateLoader)
            arpaTemplate = templateEnv.get_template(arpaTemplateFile)
        except Exception as e:
            print("Could not process reverse zone template file: %s" % str(e))
            sys.exit(1)

        try:
            templateLoader = FileSystemLoader(searchpath="./")
            templateEnv = Environment(loader=templateLoader)
            cfgTemplate = templateEnv.get_template(cfgTemplateFile)
        except Exception as e:
            print("Could not process named.conf template file: %s" % str(e))
            sys.exit(1)

        try:
            templateLoader = FileSystemLoader(searchpath="./")
            templateEnv = Environment(loader=templateLoader)
            resolvTemplate = templateEnv.get_template(resolvTemplateFile)
        except Exception as e:
            print("Could not process resolv.conf template file: %s" % str(e))
            sys.exit(1)

        hostInterfaces = netifaces.interfaces()

        for i in range(len(hostInterfaces)):
            if hostInterfaces[i] != 'lo':
                try:
                    addrs = netifaces.ifaddresses(hostInterfaces[i])
                    addressBlock = {}
                    addressBlock['interface'] = hostInterfaces[i]
                    addressBlock.update(addrs[netifaces.AF_INET][0])
                    hostAddrs.append(addressBlock)
                except KeyError:
                    pass

        for i in range(len(hostAddrs)):
            if 'addr' in hostAddrs[i]:
                ipAddress = hostAddrs[i]['addr']
                netMask = hostAddrs[i]['netmask']
                hostInterface = hostAddrs[i]['interface']
                addressCidr = '/'.join([ipAddress, netMask])

                interfaceAddress = ipaddress.IPv4Network(addressCidr, strict=False)
                rest = int((interfaceAddress.max_prefixlen - interfaceAddress.prefixlen) / 8)
                reverseAddress = interfaceAddress.network_address.reverse_pointer.split(".", rest)[-1]
                hostAddrs[i]['reverse'] = reverseAddress
                networkAddress = ipaddress.IPv4Address(ipAddress)
                hostAddrs[i]['arpa_addr'] = '.'.join(networkAddress.reverse_pointer.split(".", rest)[:rest])

                print(" %d) %s: %s" % (i+1, hostInterface, ipAddress))

        interface_answer = None
        while True:
            interface_answer = input("Interface for DNS zone: ")
            if interface_answer:
                try:
                    int(interface_answer)
                except ValueError:
                    continue
                if int(interface_answer) < 1 or int(interface_answer) > len(hostAddrs):
                    continue
                break

        ip_address = hostAddrs[int(interface_answer)-1]['addr']
        in_addr_arpa = hostAddrs[int(interface_answer)-1]['reverse']
        ip_arpa_address = hostAddrs[int(interface_answer)-1]['arpa_addr']

        runCommand.append('tsig-keygen')
        runCommand.append('-a')
        runCommand.append('hmac-sha256')
        runCommand.append('dynamicdns')
        runProccess = subprocess.Popen(runCommand, stdout=subprocess.PIPE)
        stdout_text = runProccess.stdout.read()
        key_block = stdout_text.decode('utf-8')

        for line in key_block.split('\n'):
            line = line.strip()
            tokens = line.split()
            for i in range(len(tokens)):
                if tokens[i] == 'secret':
                    tsig_key = tokens[i+1]

        tsig_key = tsig_key.strip(';')
        tsig_key = tsig_key.strip('"')

        zoneBlock = zoneTemplate.render(ip_address=ip_address)
        arpaBlock = arpaTemplate.render(in_addr_arpa=in_addr_arpa, ip_arpa_address=ip_arpa_address)
        cfgBlock = cfgTemplate.render(tsig_key=tsig_key, in_addr_arpa=in_addr_arpa)
        resolvBlock = resolvTemplate.render(ip_address=ip_address)

        zoneFileOut = '/var/named/cblab.local.db'
        arpaFileOut = '/var/named/' + in_addr_arpa + '.db'
        cfgFileOut = '/etc/named.conf'
        resolvFileOut = '/etc/resolv.conf'

        dnsKeyFileJson = {}
        dnsKeyFileJson['keyname'] = 'dynamicdns'
        dnsKeyFileJson['dnskey'] = tsig_key

        try:
            with open(zoneFileOut, 'w') as writeFile:
                writeFile.write(zoneBlock)
                writeFile.write("\n")
                writeFile.close()
        except OSError as e:
            print("Can not write to zone file: %s" % str(e))
            sys.exit(1)

        try:
            with open(arpaFileOut, 'w') as writeFile:
                writeFile.write(arpaBlock)
                writeFile.write("\n")
                writeFile.close()
        except OSError as e:
            print("Can not write to reverse zone file: %s" % str(e))
            sys.exit(1)

        try:
            with open(cfgFileOut, 'w') as writeFile:
                writeFile.write(cfgBlock)
                writeFile.write("\n")
                writeFile.close()
        except OSError as e:
            print("Can not write to named.conf file: %s" % str(e))
            sys.exit(1)

        try:
            with open(resolvFileOut, 'w') as writeFile:
                writeFile.write(resolvBlock)
                writeFile.write("\n")
                writeFile.close()
        except OSError as e:
            print("Can not write to resolv.conf file: %s" % str(e))
            sys.exit(1)

        try:
            with open(self.dnsKeyFile, 'w') as writeFile:
                json.dump(dnsKeyFileJson, writeFile, indent=4)
                writeFile.write("\n")
                writeFile.close()
        except OSError as e:
            print("Can not write to dns key file: %s" % str(e))
            sys.exit(1)

        try:
            os.chown(self.dnsKeyFile, int(userUid), int(userGid))
        except Exception as e:
            print("Could not change ownership on dns key file: %s" % str(e))
            sys.exit(1)

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--zone', action='store')
        parser.add_argument('--arpa', action='store')
        parser.add_argument('--resolv', action='store')
        parser.add_argument('--config', action='store')
        parser.add_argument('--user', action='store')
        self.args = parser.parse_args()
        self.zoneTemplateFile = self.args.zone
        self.arpaTemplateFile = self.args.arpa
        self.cfgTemplateFile = self.args.config
        self.resolvTemplateFile = self.args.resolv
        self.dnsKeyFileUser = self.args.user

def main():
    zoneConfig()

if __name__ == '__main__':

    try:
        main()
    except SystemExit as e:
        if e.code == 0:
            os._exit(0)
        else:
            os._exit(e.code)