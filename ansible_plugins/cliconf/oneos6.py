# (c) 2019 Nokia
#
# Licensed under the BSD 3 Clause license
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import (absolute_import, division, print_function)
from datetime import datetime

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
from ansible.plugins.cliconf import CliconfBase

try:
    from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import to_list

except ImportError:
    # if netcommon is not installed, fallback for Ansible 2.8 and 2.9
    from ansible.module_utils.network.common.utils import to_list


class Cliconf(CliconfBase):

    def get_device_operations(self):
        return {                                    # supported: ---------------
            'supports_commit': False,                # identify if commit is supported by device or not
            'supports_rollback': False,              # identify if rollback is supported or not
            'supports_defaults': True,              # identify if fetching running config with default is supported
            'supports_onbox_diff': False,            # identify if on box diff capability is supported or not
                                                    # unsupported: -------------
            'supports_replace': False,              # no replace candidate >> running
            'supports_admin': False,                # no admin-mode
            'supports_multiline_delimiter': False,  # no multiline delimiter
            'supports_commit_label': False,         # no commit-label
            'supports_commit_comment': False,       # no commit-comment
            'supports_generate_diff': False,        # not supported
            'supports_diff_replace': False,         # not supported
            'supports_diff_match': False,           # not supported
            'supports_diff_ignore_lines': False     # not supported
        }

    def get_oneos_rpc(self):
        return [
            'get_config',          # Retrieves the specified configuration from the device
            #'edit_config',         # Loads the specified commands into the remote device
            'get_capabilities',    # Retrieves device information and supported rpc methods
            'get',                 # Execute specified command on remote device
            #'get_default_flag'     # CLI option to include defaults for config dumps
        ]

    def get_option_values(self):
        return {
            'format': ['text'],
            'diff_match': [],
            'diff_replace': [],
            'output': ['text']
        }

    def get_device_info(self):
        """
        UNV-DE-NAMUR_03103096_PLUG401_VLAN2817#show system status
        System Information for device PBXPLUG_401 S/N T1936008207000751

        Software version    : OneOS-pCPE-PPC_pi2-6.2.2m2
        Software created on : 2019-06-26 13:09:08
        Boot version        : BOOT-PPC_hw2-2.1.2
        Boot created on     : 2018-12-10 10:37:31
        Recovery version    : OneOs-RCY-PPC_pi2-1.3.2
        Recovery created on : 2018-09-17 15:36:00

        Current system time : 2020-11-15 14:00:41+0100
        System started      : 2020-09-13 00:23:10+0200
        Start caused by     : Software requested / System defense - reboot after crash
        Sys Up time         : 63d 14h 37m 31s
        PSU                 : normal

        Temperatures:
                    CPU     normal   63.00 C (alarm level: 100.00 C)
        board sensor 1     normal   46.25 C (alarm level:  80.00 C)

        Core    Type     last sec  last min  last hour  last day  last 72 hours
        0     control     74.0 %    29.0 %     22.0 %    22.0 %     22.0 %
        1  forwarding      1.0 %     1.0 %      1.0 %     1.0 %      1.0 %
        2  forwarding      1.0 %     0.0 %      0.0 %     0.0 %      0.0 %
        3  forwarding      1.0 %     1.0 %      1.0 %     1.0 %      1.0 %
        UNV-DE-NAMUR_03103096_PLUG401_VLAN2817#



        UNV-DE-NAMUR_03103096_PLUG401_VLAN2817#show system hardware

        HARDWARE DESCRIPTION

        Device   : PBXPLUG_401
        CPU      : Freescale T1040E (1.1) - Security Engine - 8-port Ethernet switch

        Core Freq : 1400MHz   DDR Freq : 600MHz (1200 MT/s data rate)
        Core Complex Bus Freq : 600MHz   Platform Freq : 600MHz
        FMAN Freq : 600MHz   QMAN Freq : 300MHz
        CPLD Index : 1   CPLD Version : F0
        FPGA Index : 1B  FPGA Version : 0
        Physical Ram size :   2GiB
        Nand Flash size : 512MiB


        Secure Boot protection : yes


        Local   : x Uplink :      ISDN :      Radio :      Usb :

        Local   : 2 x GIGABIT ETHERNET
        M Ext   : FXS922
        FPGA Ext: Version 0xf0 Indice 0x00
        Dsp     : 4
        PRI     : (5/0, 5/1, 5/2, 5/3)
        FXS Ext : (5/4, 5/5, 5/6, 5/7)


        UNV-DE-NAMUR_03103096_PLUG401_VLAN2817#show product-info-area

        +----------------------------------------------------------------+
        |                       Product Info Area                        |
        +------------------------------+---------------------------------+
        | Key                          | Value                           |
        +------------------------------+---------------------------------+
        | mac0                         | 70:FC:8C:0D:AF:ED               |
        +------------------------------+---------------------------------+
        | mac1                         | 70:FC:8C:11:AF:ED               |
        +------------------------------+---------------------------------+
        | mac2                         | 70:FC:8C:15:AF:ED               |
        +------------------------------+---------------------------------+
        | mac3                         | 70:FC:8C:19:AF:ED               |
        +------------------------------+---------------------------------+
        | mac4                         | 70:FC:8C:1D:AF:ED               |
        +------------------------------+---------------------------------+
        | mac5                         | 70:FC:8C:21:AF:ED               |
        +------------------------------+---------------------------------+
        | mac6                         | 70:FC:8C:25:AF:ED               |
        +------------------------------+---------------------------------+
        | mac7                         | 70:FC:8C:29:AF:ED               |
        +------------------------------+---------------------------------+
        | mac8                         | 70:FC:8C:0D:AF:EE               |
        +------------------------------+---------------------------------+
        | mac9                         | 70:FC:8C:11:AF:EE               |
        +------------------------------+---------------------------------+
        | mac10                        | 70:FC:8C:15:AF:EE               |
        +------------------------------+---------------------------------+
        | mac11                        | 70:FC:8C:19:AF:EE               |
        +------------------------------+---------------------------------+
        | mac12                        | 70:FC:8C:1D:AF:EE               |
        +------------------------------+---------------------------------+
        | mac13                        | 70:FC:8C:21:AF:EE               |
        +------------------------------+---------------------------------+
        | mac14                        | 70:FC:8C:25:AF:EE               |
        +------------------------------+---------------------------------+
        | mac15                        | 70:FC:8C:29:AF:EE               |
        +------------------------------+---------------------------------+
        | Model revision               | 1.0                             |
        +------------------------------+---------------------------------+
        | Manufacturing File Reference | 48207                           |
        +------------------------------+---------------------------------+
        | Motherboard Type             | MB2515 L2P4S4Pr4uhRRBEC         |
        +------------------------------+---------------------------------+
        | PCB Revision                 | C                               |
        +------------------------------+---------------------------------+
        | HW Revision                  | A                               |
        +------------------------------+---------------------------------+
        | Manufacturing Location       | TOAB                            |
        +------------------------------+---------------------------------+
        | Manufacturing Date           | 2019-W36                        |
        +------------------------------+---------------------------------+
        | Last Testing Date            | 2019-09-30                      |
        +------------------------------+---------------------------------+
        | Serial Number                | T1936008207000751               |
        +------------------------------+---------------------------------+
        | Product Name                 | PBXPLUG_401                     |
        +------------------------------+---------------------------------+
        | Commercial Name              | PBXPLUG 401                     |
        +------------------------------+---------------------------------+
        | Sales Code                   | 81705                           |
        +------------------------------+---------------------------------+
        | Mib-2 system sysObjectID     | 2515                            |
        +------------------------------+---------------------------------+
        | Software compatibility code  | 0x7F                            |
        +------------------------------+---------------------------------+
        | SCAid                        | ALE_2515                        |
        +------------------------------+---------------------------------+
        UNV-DE-NAMUR_03103096_PLUG401_VLAN2817#


        UNV-DE-NAMUR_03103096_PLUG401_VLAN2817#show memory
        ================================================================================
        | Memory status report                         |  Total   |  Free    |  Use %  |
        ================================================================================
        | Memory Total                                 |   2.0GiB |          |         |
        |----------------------------------------------|----------|----------|---------|
        | Shared Partition                             |          |          |         |
        |   - Shared Pool                              | 255.9MiB | 142.8MiB |   44.2% |
        |                                              |          |          |         |
        | Control Partition                            |          |          |         |
        |   - Linux RAM (*)                            | 924.3MiB | 302.7MiB |   67.2% |
        |       - system free                          |          |  71.3MiB |         |
        |       - Linux cached                         | 219.2MiB |          |         |
        |       - Linux buffers                        |  43.4MiB |          |         |
        |       - Linux File Systems                   |          |          |         |
        |           - root                             | 462.2MiB | 461.9MiB |    0.1% |
        |           - tmp                              |    na    |used:32MiB|    4.0% |
        |                                              |          |          |         |
        | Forwarding Partition                         |          |          |         |
        |   - Shared Pool                              | 376.9MiB | 352.2MiB |    6.5% |
        |   - Core 0 Pool                              |  63.9MiB |  63.6MiB |    0.5% |
        |   - Core 1 Pool                              |  63.9MiB |  63.8MiB |    0.3% |
        |   - Core 2 Pool                              |  63.9MiB |  63.6MiB |    0.5% |
        |   - Binary                                   |   3.7MiB |          |         |
        |                                              |          |          |         |
        ================================================================================
        | Flash Total                                  | 512.0MiB |          |         |
        |----------------------------------------------|----------|----------|---------|
        | Boot Partition                               |  35.4MiB |          |         |
        |                                              |          |          |         |
        | File systems                                 | 476.6MiB |          |         |
        |   - user                                     | 415.3MiB | 345.7MiB |   16.8% |
        ================================================================================
        | Removable disks                              |          |          |         |
        |----------------------------------------------|----------|----------|---------|
        ================================================================================
        (*) "Free" and "Use %": estimated available memory after reclaiming page cache
        UNV-DE-NAMUR_03103096_PLUG401_VLAN2817# 
        UNV-DE-NAMUR_03103096_PLUG401_VLAN2817#show software-image
        --------------- Active bank ---------------
        Software version : OneOS-pCPE-PPC_pi2-6.2.2m2
        Creation date    : 2019-06-26 13:09:08
        Header checksum  : 0x1C5331CA

        -------------- Alternate bank -------------
        Installation status : NOT COMPLETE ! 
        """
        device_info = dict()

        device_info['network_os_vendor'] = 'ekinops'
        device_info['network_os_vendor_alt'] = 'oneaccess'
        device_info['network_os'] = 'OneOS'
        device_info['network_os_version'] = '6'
        device_info["network_os_software_location"] = "/BSA/binaries"

        reply = self.get('show running-config hostname')
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

        match = re.search(r'\W*Boot [Vv]ersion\W+(\S+)\W*$', data1, re.M)
        if match:
            device_info['network_os_boot_version'] = match.group(1)
            device_info['network_os_boot_startup_image'] = match.group(1)

        #match = re.search(r'\W*License token\W+(\S+)\W*$', data1, re.M)
        #if match:
        #    device_info['network_os_license_token'] = match.group(1)

        match = re.search(r'\W*System started\W+(.*)$', data1, re.M)
        if match:
            device_info['network_os_system_started'] = match.group(1)
            device_info['network_os_system_uptime_secs'] = datetime.strptime(match.group(1), \
                                                            "%Y-%m-%d %H:%M:%S%z").timestamp()

        match = re.search(r'\W*Sys Up time\W+(.*)$', data1, re.M)
        if match:
            device_info['network_os_system_uptime'] = match.group(1)

        match = re.search(r'\W*Start caused by\W+(.*)$', data1, re.M)
        if match:
            device_info['network_os_system_restart_cause'] = match.group(1)


        reply = self.get('show memory')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'.*- user\W+([0-9\.]+)MiB\W+([0-9\.]+)MiB', data, re.M)
        if match:
            device_info['network_os_diskspace_total_bytes'] = float(match.group(1))*1000*1000
            device_info['network_os_diskspace_free_bytes'] = float(match.group(2))*1000*1000



        reply = self.get('ls -l /BSA/binaries')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        matches = re.finditer(r'\S+ +\d+ +(\d+).* (.*)$', data, re.M)
        if matches:
            boot_files = []
            for matchNum, match in enumerate(matches, start=1):
                boot_files.append({"file": match.group(2), "size": match.group(1)})
            device_info['network_os_boot_available_files'] = boot_files


        reply = self.get('show software-image')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        device_info['network_os_software_bank_primary'] = "NOT SET"
        device_info['network_os_software_bank_alternate'] = "NOT SET"

        match = re.search(r'.*Software version\W+(\S*).*Alternate.*', data, re.DOTALL)
        if match:
            device_info['network_os_software_bank_primary'] = match.group(1)

        match = re.search(r'Alternate.*Software version\W+(\S*)', data, re.DOTALL)
        if match:
            device_info['network_os_software_bank_alternate'] = match.group(1)

        device_info['network_os_startup_config'] = "/BSA/config/bsaStart.cfg"

        reply = self.get('ls /BSA/bsaBoot.inf')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'bsaBoot.inf', data, re.M)
        if match:
            reply = self.get('cat /BSA/bsaBoot.inf')
            data = to_text(reply, errors='surrogate_or_strict').strip()
            
            match = re.search(r'flash:(/BSA/config/\S+)$', data, re.M)
            if match:
                device_info['network_os_startup_config'] = match.group(1)

        return device_info



    def get_capabilities(self):
        capabilities = super(Cliconf, self).get_capabilities()
        #capabilities['device_operations'] = self.get_device_operations()
        capabilities['rpc'] = self.get_oneos_rpc()
        capabilities['device_info'] = self.get_device_info()
        capabilities['network_api'] = 'cliconf'
        capabilities.update(self.get_option_values())
        return json.dumps(capabilities)

    def get_default_flag(self):
        return ['detail']

    def is_classic_mode(self):
        reply = self.send_command('/show system information')
        data = to_text(reply, errors='surrogate_or_strict').strip()
        match = re.search(r'Configuration Mode Oper:\s+(.+)', data)
        return not match or match.group(1) == 'classic'

    def get_config(self, source='running', format='text', flags="ordered"):
        if source != 'running':
            raise ValueError("fetching configuration from %s is not supported" % source)

        if format != 'text':
            raise ValueError("'format' value %s is invalid. Only format supported is 'text'" % format)

        cmd = 'show running-config %s' % ' '.join(flags)
        self.send_command('end')
        response = self.send_command(cmd.strip())

        return response

    def edit_config(self, candidate=None, commit=True, replace=None, comment=None):
        operations = self.get_device_operations()
        self.check_edit_config_capability(operations, candidate, commit, replace, comment)

        if not self.is_classic_mode():
            raise ValueError("Nokia SROS node is not running in classic mode. Use ansible_network_os=nokia.sros.md")

        requests = []
        responses = []

        try:
            self.send_command('exit all')
            self.send_command('admin rollback save')  # Save rollback to compare if changes occur. This rollback will be removed upon module completion.
            for cmd in to_list(candidate):
                if isinstance(cmd, Mapping):
                    requests.append(cmd['command'])
                    responses.append(self.send_command(**cmd))
                else:
                    requests.append(cmd)
                    responses.append(self.send_command(cmd))

        except AnsibleConnectionFailure as exc:
            self.send_command('exit all')
            self.send_command('admin rollback revert latest-rb')
            self.send_command('admin rollback delete latest-rb')
            raise exc

        self.send_command('exit all')
        rawdiffs = self.send_command('admin rollback compare')
        match = re.search(r'\r?\n-+\r?\n(.*)\r?\n-+\r?\n', rawdiffs, re.DOTALL)
        if match:
            if commit:
                pass
            else:
                # Special hack! We load the config to running and rollback
                # to just figure out the delta. this might be risky in
                # check-mode, because it causes the changes contained to
                # become temporary active.

                self.send_command('admin rollback revert latest-rb')
            # Remove latest rollback to leave rollback history intact.
            self.send_command('admin rollback delete latest-rb')
            return {'request': requests, 'response': responses, 'diff': match.group(1)}
        else:
            # Remove latest rollback to leave rollback history intact.
            self.send_command('admin rollback delete latest-rb')
            return {'request': requests, 'response': responses}

    def get(self, command, prompt=None, answer=None, sendonly=False, output=None, newline=True, check_all=False):
        if output:
            raise ValueError("'output' value %s is not supported for get" % output)

        return self.send_command(command=command, prompt=prompt, answer=answer, sendonly=sendonly, newline=newline, check_all=check_all)

    def rollback(self, rollback_id, commit=True):
        if not self.is_classic_mode():
            raise ValueError("Nokia SROS node is not running in classic mode. Use ansible_network_os=nokia.sros.md")

        self.send_command('exit all')

        if str(rollback_id) == '0':
            rollback_id = 'latest-rb'

        rawdiffs = self.send_command('admin rollback compare {0} to active-cfg'.format(rollback_id))
        match = re.search(r'\r?\n-+\r?\n(.*)\r?\n-+\r?\n', rawdiffs, re.DOTALL)

        if match:
            if commit:
                self.send_command('admin rollback revert {0} now'.format(rollback_id))
            return {'diff': match.group(1).strip()}
        return {}
