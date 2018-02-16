import os
import re


class HubMetaData(object):

    os_info_path = '/etc/os-release'
    connected_wifi_info_path = 'etc/NetworkManager/system-connections/bluenet'
    cpu_info_path = '/proc/cpuinfo'

    @classmethod
    def _read_from_file(cls, file_path):

        if not os.path.isfile(file_path):
            return ''

        with open(file_path) as data_file:
            return data_file.readlines()

    @classmethod
    def os_version(cls):
        os_info = cls._read_from_file(cls.os_info_path)

        for line in os_info:
            if 'VERSION=' in line:
                version = re.split('VERSION=', line)[1]
                return version.strip().replace('"', '')

        return ''

    @classmethod
    def wifi(cls):
        network_info = cls._read_from_file(cls.connected_wifi_info_path)

        for line in network_info:
            if 'ssid=' in line:
                ssid = re.split('ssid=', line)[1]
                return ssid.strip()

        return ''

    @classmethod
    def hardware_identifier(cls):
        cpu_info = cls._read_from_file(cls.cpu_info_path)

        for line in cpu_info:
            if 'Serial' in line:
                serial = re.split(':\s*', line)[1]
                return serial.strip().replace('02c00081', '')

        return ''
