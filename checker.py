#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import sshConnect
from multiprocessing import Pool
import re

"""Запуск Параллельных процессов для разных хостов"""
def start(connect):
    print("connect to " + connect['name'] + "...")
    try:
        esxi = sshConnect.sshConnect(connect)
    except:
       pass
    else:
        vms = parse_vmx(esxi.get_cmd('esxcli vm process list'))
        for vm in vms:
            check(vms[vm], esxi)
        del esxi

"""Проверка виртуальных машин на наличие условий
больше 2х снепшотов, и больше 50% занимаемого 
снепшотами места"""
def check(vmx, esxi):
    path = '/'.join(vmx.split('/')[:-1]) + '/'
    work_path = esxi.get_cmd('cat ' + vmx + "| grep workingDir")
    if work_path:
        work_path = work_path.split('\n')[0]
    num_snap = esxi.get_cmd('cat ' + path + """*.vmsd | 
				grep 'snapshot.numSnapshots = ' | awk '{print $3}'""")
    if num_snap:
        if int(num_snap.split('\n')[0].split('"')[1]) > 1:
            disks = esxi.get_cmd('cat ' + path + """*.vmsd | 
				egrep "snapshot0\.disk[0-9]*\.fileName = " | 
				grep '.vmdk\"$'""").split('\n')
            print(disks)
            if sum_snap(disks, esxi, path, work_path) / sum_disk(disks, esxi, path) > 0.5:
                print(disks)
                print(sum_disk(disks, esxi, path))
                print(sum_snap(disks, esxi, path, work_path))
    
"""Сумма снепшотов"""
def sum_snap(disks, esxi, path, work_path):
    res = 0
    for disk in disks:
        try:
            name = disk[re.match('snapshot0.disk[0-9]+.fileName = "', disk).end():-1]
            if work_path and re.match('/vmfs/', name):
                name = work_path + name.split('/')[-1]
            elif work_path:
                name = work_path + name
            elif not re.match('/vmfs/', name):
                name = path + name
            name = re.sub('\.vmdk$', '-*-delta.vmdk', name)
            for size in esxi.get_cmd('ls -l ' + name + "| awk '{print $5}'").split('\n'):
                res = res + int(size)
        except:
            pass
    return res
    
"""Сумма жестких дисков"""
def sum_disk(disks, esxi, path):
    res = 0
    for disk in disks:
        try:
#            name = disk[re.match('.*fileName = "', disk).end():-1]
            name = disk[re.match('snapshot0.disk[0-9]+.fileName = "', disk).end():-1]
#            if not re.search('-[0-9]{6}.vmdk$', name):
            if not re.match('/vmfs/', name):
                name = path + name
            name = re.sub('\.vmdk$', '-flat.vmdk', name)
            res = res + int(esxi.get_cmd('ls -l ' + name + "| awk '{print $5}'"))
        except:
            pass
    return res

"""Парсим виртуальные машины на хосте
получаем имя машины и путь к файлу настроек"""
def parse_vmx(conf):
    vms = dict()
    arr = conf.split('\n')
    for line in arr:
        res = re.match('\s+Display Name:\s+', line)
        if res:
            name = line[res.end():]
        else:
            res = re.match('\s+Config File:\s+', line)
            if res:
                conf_file = line[res.end():]
                vms.update({name: conf_file})
    return vms

"""Парсим файл настроек"""
def get_settings(config):
    settings = []
    for section in config.sections():
        value = {'name': section}
        for setting in config[section]:
            value.update({setting: config.get(section, setting)})
        settings.append(value)
    return settings

def main():
    parser = configparser.ConfigParser()
    parser.read('conn.conf')
    settings = get_settings(parser)
    if len(settings) > 0:
        p = Pool(len(settings))
        res = p.map(start, settings)
#        p.join()
        p.close()
    else:
        print("Conf file is empty!")

if __name__ == "__main__":
    main()
