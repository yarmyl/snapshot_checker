#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import sshConnect
from multiprocessing import Pool

def start(connect):
    print("connect to " + connect['name'] + "...")
    try:
        esxi = sshConnect.sshConnect(connect)
        print(esxi.get_cmd('ls -l'))
        del esxi
    except:
        pass

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
        res = p.map(start, settings,)
#        p.join()
        p.close()
    else:
        print("Conf file is empty!")

if __name__ == "__main__":
    main()
