#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import sshConnect
from multiprocessing import Pool
import re
import time
import datetime
import argparse
import mySQLConnect

"""Разбор аргументов"""
def createParser ():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mysql', action='store_true') # запись в mysql
    parser.add_argument('--out', action='store_true') # вывод из mysql
    return parser

"""Запуск Параллельных процессов для разных хостов"""
def start(connect):
    print("connect to " + connect['name'] + "...")
    start_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ret = []
    result = dict()
    try:
        esxi = sshConnect.sshConnect(connect)
    except:
       pass
    else:
        vms = parse_vmx(esxi.get_cmd('esxcli vm process list'))
        for vm in vms:
#            print(str(start_time) + ' ' + vm)
            res = check(vms[vm], esxi)
            if res:
                res.update({'vm_name': vm, 'start_time': start_time})
                ret.append(res)
        result = {'ESXi_name': connect['name'], 'ESXi_vms': ret}
        del esxi
    return result

"""Проверка виртуальной машины на наличие условий
больше 2х снепшотов, и больше 50% занимаемого 
снепшотом места относительно суммы объемов дисков"""
def check(vmx, esxi):
    ret = dict()
    path = '/'.join(vmx.split('/')[:-1]) + '/'
#    print(path)
    work_path = esxi.get_cmd('cat ' + vmx + "| grep workingDir")
    if work_path:
        work_path = work_path.split('\n')[0]
    num_snap = esxi.get_cmd('cat ' + path + """*.vmsd | 
				grep 'snapshot.numSnapshots = ' | awk '{print $3}'""")
    if num_snap:
        if int(num_snap.split('\n')[0].split('"')[1]) >= esxi.count:
            disks = esxi.get_cmd('cat ' + path + """*.vmsd | 
				egrep "snapshot0\.disk[0-9]*\.fileName = " | 
				grep '.vmdk\"$'""").split('\n')
#            print(disks)
#            if sum_snap(disks, esxi, path, work_path) / sum_disk(disks, esxi, path) > 0.5:
#                print(disks)
#                print(sum_disk(disks, esxi, path))
#                print(sum_snap(disks, esxi, path, work_path))
            summ = sum_disk(disks, esxi, path)
            res = check_snap(disks, esxi, path, work_path, summ)
            if res:
                ret = {'disk_size': summ, 'snap_info': res}
    return ret

"""Сравниваем снепшот с объемом дисков"""
def check_snap(disks, esxi, path, work_path, summ):
    res = []
    size = 0
    snap = dict()
    for disk in disks:
        try:
            name = disk[re.match('snapshot0.disk[0-9]+.fileName = "', disk).end():-1]
        except:
            pass
        else:
            name = add_path(name, path, work_path)
            pname = re.sub('\.vmdk$', '-*-delta.vmdk', name)
            for file in esxi.get_cmd('ls -l ' + pname + "| awk '{print $5,$9}'").split('\n'):
                if file:
                    id = re.sub(re.sub('\.vmdk$', '', name), '', file.split(' ')[1])
                    if snap.get(id):
                        snap[id].update({'snap_size': snap[id]['snap_size'] + int(file.split(' ')[0])})
                    else:
                        snap[id] = {'snap_size': int(file.split(' ')[0]), 'file': file.split(' ')[1]}
    for id in snap:
        if snap[id]['snap_size'] / summ > esxi.percent / 100:
            conf = re.sub('-delta\.vmdk', '.vmdk', snap[id]['file'])
            snap_time = esxi.get_cmd('ls -le ' + conf + 
				" | awk '{print $7,$8,$9,$10}'").split('\n')[0].split(' ')
            snap_time = datetime.datetime(int(snap_time[3]), month[snap_time[0]], 
					int(snap_time[1]), hour=int(snap_time[2].split(':')[0]), 
					minute=int(snap_time[2].split(':')[1]), 
					second=int(snap_time[2].split(':')[2])).strftime('%Y-%m-%d %H:%M:%S')
					#.timestamp())
					#.strftime('%Y-%m-%d %H:%M:%S')
            snap[id].update({'snap_time': snap_time})
            parent = esxi.get_cmd('cat ' + conf + 
			""" | grep parentFileNameHint=\\" | sed 's/parentFileNameHint="//g; s/"//g'""").split('\n')[0]
            uid = esxi.get_cmd('cat ' + path + "*.vmsd | grep " + parent).split('\n')[0]
            uid = re.sub('\.disk[0-9]+\.fileName = ".*$', '', uid)
            snap_name = esxi.get_cmd('cat ' + path + "*.vmsd | grep " + 
				uid + ".displayName | sed 's/^.* = \"//g; s/\"$//g'").split('\n')[0]
            snap[id].update({'snap_name': snap_name})
            snap[id].pop('file')
            res.append(snap[id])
    return res

"""добаление пути"""
def add_path(name, path, work_path):
    if work_path and re.match('/vmfs/', name):
        name = work_path + name.split('/')[-1]
    elif work_path:
        name = work_path + name
    elif not re.match('/vmfs/', name):
        name = path + name
    return name

"""словарь месяцев"""
month = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7,
		'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}

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
    esxis = []
    settings = dict()
    for section in config.sections():
        value = dict()
        for setting in config[section]:
            value.update({setting: config.get(section, setting)})
        if section != 'MYSQL':
            value.update({'name': section})
            esxis.append(value)
        else:
            settings.update({section: value})	    
    settings.update({'esxis': esxis})
    return settings

def main():
    parser = createParser()
    namespace = parser.parse_args()
    parser = configparser.ConfigParser()
    parser.read('conn.conf')
    settings = get_settings(parser)
    if namespace.mysql and namespace.out:
        if settings.get('MYSQL'):
            mysql = settings.pop('MYSQL')
            DB = mySQLConnect.myConn(mysql)
            print(DB.execute("SELECT * FROM SNAPSHOTS"))
            del DB
        else:
            print("Error: Haven't mysql config")
    elif len(settings) > 0:
        mysql = 0
#        print(settings)
        if namespace.mysql and settings.get('MYSQL'):
            mysql = settings.pop('MYSQL')
        elif namespace.mysql:
            print("Error: Haven't mysql config")
            return 0
        elif settings.get('MYSQL'):
            settings.pop('MYSQL')
        if settings.get('esxis'):
            p = Pool(len(settings.get('esxis')))
            res = p.map(start, settings.get('esxis'))
            print(res)
            if mysql:
                DB = mySQLConnect.myConn(mysql)
                for esxi in res:
                    for vm in esxi['ESXi_vms']:
                        for snap in vm['snap_info']:
                            DB.execute("""INSERT INTO SNAPSHOTS (vm_name, snap_name, snap_size, snap_time, time)
					VALUES (%s, %s, %s, %s, %s)""", [vm['vm_name'], snap['snap_name'], 
					snap['snap_size'], snap['snap_time'], vm['start_time']])
                print("Inser data to DB...")
                DB.commit()
                print("Success!")
                del DB
            p.close()
    else:
        print("Conf file is empty!")

if __name__ == "__main__":
    main()
