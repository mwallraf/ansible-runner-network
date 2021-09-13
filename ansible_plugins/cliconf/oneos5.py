# (c) 2019 Nokia
#
# Licensed under the BSD 3 Clause license
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
---
author: Nokia
cliconf: nokia.sros.classic
short_description: Cliconf plugin to configure and run CLI commands on Nokia SR OS devices (classic mode)
description:
  - This plugin provides low level abstraction APIs for sending CLI commands and
    receiving responses from Nokia SR OS network devices.
"""

import re
import json

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils.common._collections_compat import Mapping
from ansible.module_utils._text import to_text
from ansible.plugins.cliconf import CliconfBase, enable_mode

from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.config import NetworkConfig

try:
    from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import to_list

except ImportError:
    # if netcommon is not installed, fallback for Ansible 2.8 and 2.9
    from ansible.module_utils.network.common.utils import to_list


class Cliconf(CliconfBase):

    def get_device_operations(self):
        return {                                    # supported: ---------------
    #         'supports_commit': False,                # identify if commit is supported by device or not
    #         'supports_rollback': False,              # identify if rollback is supported or not
    #         'supports_defaults': True,              # identify if fetching running config with default is supported
            'supports_onbox_diff': False,            # identify if on box diff capability is supported or not
    #                                                 # unsupported: -------------
    #         'supports_replace': False,              # no replace candidate >> running
    #         'supports_admin': False,                # no admin-mode
    #         'supports_multiline_delimiter': False,  # no multiline delimiter
    #         'supports_commit_label': False,         # no commit-label
    #         'supports_commit_comment': False,       # no commit-comment
            'supports_generate_diff': True,        # not supported
            'supports_diff_replace': True,         # not supported
    #         'supports_diff_match': False,           # not supported
    #         'supports_diff_ignore_lines': False     # not supported
        }

    def get_oneos_rpc(self):
        return [
            'get_diff'
            # 'get_config',          # Retrieves the specified configuration from the device
            # 'edit_config',         # Loads the specified commands into the remote device
            # 'get_capabilities',    # Retrieves device information and supported rpc methods
            # 'get',                 # Execute specified command on remote device
            # 'get_default_flag'     # CLI option to include defaults for config dumps
        ]

    def get_option_values(self):
        return {
            'format': ['text'],
            'diff_match': ['line', 'strict', 'exact', 'none'],
            'diff_replace': ['line', 'block', 'config'],
            'output': []
        }


    def get_diff(self, candidate=None, running=None, diff_match='line', diff_ignore_lines=None, path=None, diff_replace='line'):
        diff = {} 

        device_operations = self.get_device_operations()
        option_values = self.get_option_values()   

        if candidate is None and device_operations['supports_generate_diff'] and diff_match != 'none':
            raise ValueError("candidate configuration is required to generate diff")

        if diff_match not in option_values['diff_match']:
            raise ValueError("'match' value %s in invalid, valid values are %s" % (diff_match, ', '.join(option_values['diff_match'])))

        if diff_replace not in option_values['diff_replace']:
            raise ValueError("'replace' value %s in invalid, valid values are %s" % (diff_replace, ', '.join(option_values['diff_replace'])))

        # prepare candidate configuration
        candidate_obj = NetworkConfig(indent=1)
        candidate_obj.load(candidate)

        if running and diff_match != 'none':
            # running configuration
            running_obj = NetworkConfig(indent=1, contents=running, ignore_lines=diff_ignore_lines)
            configdiffobjs = candidate_obj.difference(running_obj, path=path, match=diff_match, replace=diff_replace)
        else:
            configdiffobjs = candidate_obj.items

        if configdiffobjs and diff_replace == 'config':
            diff['config_diff'] = candidate
        elif configdiffobjs:
            configlines = list()
            for i, o in enumerate(configdiffobjs):
                configlines.append(o.text)
                if i + 1 < len(configdiffobjs):
                    levels = len(o.parents) - len(configdiffobjs[i + 1].parents)
                else:
                    levels = len(o.parents)
                if o.text == 'end':
                    levels -= 1
                if levels > 0:
                    for i in range(levels):
                        configlines.append("end")
            diff['config_diff'] = "\n".join(configlines)
        else:
            diff['config_diff'] = ''

        return diff




    def get_device_info(self):
        """
        homeoffice159#show system status

        System Information for device MB90Ss0UFPE0SNWsd+xG S/N T1938008109107849

        Software version    : ONEOS90-MONO_FT-V5.2R2E4_HA2
        Software created on : 08/11/17 18:10:42
        License token       : None
        Boot version        : BOOT90-SEC-V5.2R2E17
        Boot created on     : 08/03/18 14:11:34

        Boot Flags          : 0x00000008

        Current system time : 14/11/20 21:16:54
        System started      : 14/11/20 20:40:57
        Start caused by     : Power Fail detection
        Sys Up time         : 0d 0h 35m 57s
        System clock ticks  : 107879

        Current CPU load    : 7.6%
        Current Critical Tasks CPU load           : 4.4%
        Current Non Critical Tasks CPU load       : 3.2%
        Average CPU load (5 / 60 Minutes)         : 6.6% / 4.2%

        Free / Max RAM      :  323,53 /  443,58 MB

        homeoffice159#show system hardware

        HARDWARE DESCRIPTION

        Device   : LBB_4G+
        CPU      : Freescale P1021E - Quick Engine - Security Engine

        Core Freq : 800MHz   DDR Freq : 533MHz
        Core Complex Bus Freq : 400MHz   Platform Freq : 400MHz
        CPLD Index : 6   CPLD Version : 10
        Physical Ram size : 512Mo   OneOS Ram size : 512Mo
        Nand Flash size : 256Mo
        Ram disk :   1Mo   Flash disk : 246Mo

        Local : x Uplink :      ISDN :      Radio : x Usb0 :      Usb1 :

        Local  : SFP ETHERNET + GIGABIT ETHERNET + SWITCH ETHERNET / 4 ports
        Radio  : Cellular radio module
        Dsp    : 0
        Wlan   : VendorID (0x168c) / DeviceID (0x002e)

        homeoffice159#show product-info-area

        +----------------------------------------------------------------+
        |                       Product Info Area                        |
        +------------------------------+---------------------------------+
        | Key                          | Value                           |
        +------------------------------+---------------------------------+
        | mac0                         | 70:FC:8C:0D:D5:46               |
        +------------------------------+---------------------------------+
        | mac1                         | 70:FC:8C:11:D5:46               |
        +------------------------------+---------------------------------+
        | mac2                         | 70:FC:8C:15:D5:46               |
        +------------------------------+---------------------------------+
        | mac3                         | 70:FC:8C:19:D5:46               |
        +------------------------------+---------------------------------+
        | mac4                         | 70:FC:8C:1D:D5:46               |
        +------------------------------+---------------------------------+
        | mac5                         | 70:FC:8C:21:D5:46               |
        +------------------------------+---------------------------------+
        | mac6                         | 70:FC:8C:25:D5:46               |
        +------------------------------+---------------------------------+
        | mac7                         | 70:FC:8C:29:D5:46               |
        +------------------------------+---------------------------------+
        | mac8                         | 70:FC:8C:0D:D5:47               |
        +------------------------------+---------------------------------+
        | mac9                         | 70:FC:8C:11:D5:47               |
        +------------------------------+---------------------------------+
        | mac10                        | 70:FC:8C:15:D5:47               |
        +------------------------------+---------------------------------+
        | mac11                        | 70:FC:8C:19:D5:47               |
        +------------------------------+---------------------------------+
        | mac12                        | 70:FC:8C:1D:D5:47               |
        +------------------------------+---------------------------------+
        | mac13                        | 70:FC:8C:21:D5:47               |
        +------------------------------+---------------------------------+
        | mac14                        | 70:FC:8C:25:D5:47               |
        +------------------------------+---------------------------------+
        | mac15                        | 70:FC:8C:29:D5:47               |
        +------------------------------+---------------------------------+
        | Manufacturing File Reference | 1090 00 N 0048109A00 BB         |
        +------------------------------+---------------------------------+
        | Motherboard Type             | MB90Ss0UFPE0SNWsd+xG            |
        +------------------------------+---------------------------------+
        | Manufacturing Location       | TOAB                            |
        +------------------------------+---------------------------------+
        | Manufacturing Date           | 18/09/2019                      |
        +------------------------------+---------------------------------+
        | Serial Number                | T1938008109107849               |
        +------------------------------+---------------------------------+
        | Product name                 | LBB_4G+                         |
        +------------------------------+---------------------------------+
        | Commercial name              | LBB4G+                          |
        +------------------------------+---------------------------------+
        | Mreturn1                     |                                 |
        +------------------------------+---------------------------------+
        | Mreturn2                     |                                 |
        +------------------------------+---------------------------------+
        | Mreturn3                     |                                 |
        +------------------------------+---------------------------------+
        | Mreturn4                     |                                 |
        +------------------------------+---------------------------------+
        homeoffice159#
        homeoffice159#cat /BSA/bsaBoot.inf
        flash:/BSA/binaries/oneosrun
        flash:/BSA/config/bsaStart.cfg
        homeoffice159#
        homeoffice159#
        homeoffice159#ls /BSA/binaries
        Listing the directory /BSA/binaries
        .                                       0
        ..                                      0
        OneOs                            16302911
        oneosrun                         16302911
        homeoffice159#
        homeoffice159#
        homeoffice159#ls /BSA/config
        Listing the directory /BSA/config
        .                                       0
        ..                                      0
        bsaStart.cfg                         9443
        homeoffice159#        
        homeoffice159#show boot version
        Boot version    : BOOT90-SEC-V5.2R2E17
        Boot created on : 08/03/18 14:11:34
        homeoffice159#        
        homeoffice159#show device status flash

        volume descriptor ptr (pVolDesc):	0x43e8860
        cache block I/O descriptor ptr (cbio):	0x43e5e20
        auto disk check on mount:		NOT ENABLED
        max # of simultaneously open files:	22
        file descriptors in use:		1
        # of different files in use:		1
        Currently opened files :
        password
        # of descriptors for deleted files:	0
        # of obsolete descriptors:		0

        current volume configuration:
        - &devHdr.node:    0x043E8860
        - devHdr.drvNum:   3
        - devHdr.name:     flash:
        - magic:           0xDFAC9723
        - mounted:         0x00000001
        - pCbio:           0x043E5E20
        - pDirDesc:        0x043AEF00
        - pFatDesc:        0x043AEF60
        - devSem:          0x043E8910
        - shortSem:        0x043E8990
        - pFdList:         0x043E8A10
        - pFhdlList:       0x043E8FA0
        - pFsemList:       0x043E95E0
        - pDirDesc:        0x043AEF00
        - volume label:	NO LABEL ; (in boot sector:	           )
        - volume Id:		0x0
        - total number of sectors:	124,536
        - bytes per sector:		2,048
        - # of sectors per cluster:	4
        - # of reserved sectors:	1
        - FAT entry size:		FAT16
        - # of sectors per FAT copy:	31
        - # of FAT table copies:	2
        - # of hidden sectors:		8
        - first cluster is in sector #	93
        - Update last access date for open-read-close = FALSE
        - names style:			VxLong
        - root dir start sector:               63
        - # of sectors per root:		30
        - max # of entries in root:		960

        FAT handler information:
        ------------------------
        - allocation group size:	4 clusters
        - free space on volume:	222,011,392 bytes        
        """
        device_info = dict()

        device_info['network_os_vendor'] = 'ekinops'
        device_info['network_os_vendor_alt'] = 'oneaccess'
        device_info['network_os'] = 'OneOS'
        device_info['network_os_version'] = '5'
        device_info["network_os_software_location"] = "/BSA/binaries"

        reply = self.get('show running-config |hostname')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'\W*hostname\W+(\S+)\W*$', data, re.M)
        if match:
            device_info['network_os_hostname'] = match.group(1)


        reply = self.get('show product-info-area')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'\W*Product [Nn]ame\W+(\S+)\W+$', data, re.M)
        if match:
            device_info['network_os_platform'] = match.group(1)

        match = re.search(r'\W*Commercial [Nn]ame\W+(\S+)\W+$', data, re.M)
        if match:
            device_info['network_os_platform_commercial'] = match.group(1)

        match = re.search(r'\W*Serial [Nn]umber\W+(\S+)\W+$', data, re.M)
        if match:
            device_info['network_os_serial_number'] = match.group(1)


        reply = self.get('show system status')
        data1 = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'\W*Software [Vv]ersion\W+(\S+)\W*$', data1, re.M)
        if match:
            device_info['network_os_software_version'] = match.group(1)       
            match2 = re.search(r'.*\-V([0-9]+)', match.group(1))
            if match2:
                device_info['network_os_version'] = match2.group(1)

        match = re.search(r'\W*Boot [Vv]ersion\W+(\S+)\W*$', data1, re.M)
        if match:
            device_info['network_os_boot_version'] = match.group(1)

        match = re.search(r'\W*License token\W+(\S+)\W*$', data1, re.M)
        if match:
            device_info['network_os_license_token'] = match.group(1)

        match = re.search(r'\W*System started\W+(.*)$', data1, re.M)
        if match:
            device_info['network_os_system_started'] = match.group(1)

        match = re.search(r'\W*Sys Up time\W+(.*)$', data1, re.M)
        if match:
            device_info['network_os_system_uptime'] = match.group(1)

        match = re.search(r'\W*System clock ticks\W+(.*)$', data1, re.M)
        if match:
            device_info['network_os_system_uptime_secs'] = match.group(1)

        match = re.search(r'\W*Start caused by\W+(.*)$', data1, re.M)
        if match:
            device_info['network_os_system_restart_cause'] = match.group(1)

        match = re.search(r'\W*OneOS Ram size\W+(\d+)Mo', data1, re.M)
        if match:
            device_info['network_os_diskspace_total_bytes'] = int(match.group(1))*1000


        reply = self.get('ls /BSA/binaries')
        data2 = to_text(reply, errors='surrogate_or_strict').strip()

        matches = re.finditer(r'\W+(\S+)\s+([0-9]{2,})$', data2, re.M)
        if matches:
            boot_files = []
            for matchNum, match in enumerate(matches, start=1):
                boot_files.append({"file": match.group(1), "size": match.group(2)})
            device_info['network_os_boot_available_files'] = boot_files


        reply = self.get('cat /BSA/bsaBoot.inf')
        data3 = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'flash:(/BSA/binaries/\w+)$', data3, re.M)
        if match:
            device_info['network_os_boot_startup_image'] = match.group(1)

        match = re.search(r'flash:(/BSA/config/\S+)$', data3, re.M)
        if match:
            device_info['network_os_startup_config'] = match.group(1)


        reply = self.get('show device status flash')
        data4 = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'\Wfree space on volume:\W+(\S+)', data4, re.M)
        if match:
            device_info['network_os_diskspace_free_bytes'] = match.group(1).replace(",", "")


        return device_info


    def get_capabilities(self):
        result = super(Cliconf, self).get_capabilities()
        return json.dumps(result)        


    def get_capabilities(self):
        capabilities = super(Cliconf, self).get_capabilities()
        capabilities['device_operations'] = self.get_device_operations()
        capabilities['rpc'] += self.get_oneos_rpc()
        capabilities['device_info'] = self.get_device_info()
        capabilities['network_api'] = 'cliconf'
        capabilities.update(self.get_option_values())
        return json.dumps(capabilities)

    # def get_default_flag(self):
    #     return ['detail']

    # def is_classic_mode(self):
    #     reply = self.send_command('/show system information')
    #     data = to_text(reply, errors='surrogate_or_strict').strip()
    #     match = re.search(r'Configuration Mode Oper:\s+(.+)', data)
    #     return not match or match.group(1) == 'classic'

    def get_config(self, source='running', format='text', flags=None):
        if source != 'running':
            raise ValueError("fetching configuration from %s is not supported" % source)

        if format != 'text':
            raise ValueError("'format' value %s is invalid. Only format supported is 'text'" % format)

        if not flags:
            flags = []

        cmd = "show running-config "

        cmd += " ".join(to_list(flags))
        cmd = cmd.strip()

        return self.send_command(cmd)


    def edit_config(self, candidate=None, commit=False, replace=None, comment=None):
        """
        TODO: error when command fails
        """
        resp = {}
        results = []
        requests = []

        for cmd in ["end", "configure terminal"]:
            self.send_command(cmd)
        
        for cmd in to_list(candidate):
            if isinstance(cmd, dict):
                command = cmd['command']
                prompt = cmd['prompt']
                answer = cmd['answer']
                newline = cmd.get('newline', True)
            else:
                command = cmd
                prompt = None
                answer = None
                newline = True

            if cmd != 'end' and cmd[0] != '!':
                results.append(self.send_command(command, prompt, answer, False, newline))
                requests.append(cmd)

        self.send_command('end')

        resp['request'] = requests
        resp['response'] = results
        return resp


    def get(self, command, prompt=None, answer=None, sendonly=False, output=None, newline=True, check_all=False):
        if output:
            raise ValueError("'output' value %s is not supported for get" % output)

        return self.send_command(command=command, prompt=prompt, answer=answer, sendonly=sendonly, newline=newline, check_all=check_all)

    # def rollback(self, rollback_id, commit=True):
    #     if not self.is_classic_mode():
    #         raise ValueError("Nokia SROS node is not running in classic mode. Use ansible_network_os=nokia.sros.md")

    #     self.send_command('exit all')

    #     if str(rollback_id) == '0':
    #         rollback_id = 'latest-rb'

    #     rawdiffs = self.send_command('admin rollback compare {0} to active-cfg'.format(rollback_id))
    #     match = re.search(r'\r?\n-+\r?\n(.*)\r?\n-+\r?\n', rawdiffs, re.DOTALL)

    #     if match:
    #         if commit:
    #             self.send_command('admin rollback revert {0} now'.format(rollback_id))
    #         return {'diff': match.group(1).strip()}
    #     return {}


