#coding:utf-8
#-----------私有地址段-----------
#0.0.0.0-0.255.255.255是保留地址 0-16777215
#127.0.0.0到127.255.255.255是保留地址，用做循环测试用的 2130706432-2147483647
#10.0.0.0到10.255.255.255是私有地址 167772160-184549375
#169.254.0.0到169.254.255.255是保留地址 2851995648-2852061183
#172.16.0.0到172.31.255.255是私有地址   2886729728-2887778303
#192.168.0.0到192.168.255.255是私有地址 3232235520-3232301055

import urllib2
import io
import os
import time
import json
import argparse
import re
import socket
import struct
from multiprocessing import Pool



RECENT_IP = None

FILTER_IPS = [(0,16777215),(2130706432,2147483647),(167772160,184549375),(2851995648,2852061183),\
                         (2886729728,2887778303),(3232235520,3232301055)]

#--------IP转换----
def filter_ip(s,e,begin,end):
    res = s
    if s>=begin and s<=end:
            if e >end:
                    res = end +1
            else:
                    res = e
    return res

def ipaddr_to_binary(ipaddr):
    q = ipaddr.split('.')
    return reduce(lambda a,b: long(a)*256 + long(b), q)

def binary_to_ipaddr(ipbinary):
    return socket.inet_ntoa(struct.pack('!I', ipbinary))

def cycle_to_ip(ip_begin,ip_end):
    s = ipaddr_to_binary(ip_begin)
    e = ipaddr_to_binary(ip_end)
    if s>e:
        raise ('起始的ip,应小于结束的ip')
    while (s <= e):
        for m,n in FILTER_IPS:
                s = filter_ip(s,e,m,n)
        yield binary_to_ipaddr(s)
        s = s + 1

def add_ip(iprange):
    pattern = re.compile(r'''(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s*-\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})''', re.VERBOSE)
    result = pattern.match(iprange)
    if result:
        ip_begin = result.group(1)
        ip_end = result.group(2)
        return cycle_to_ip(ip_begin,ip_end)
#-----------IP转换 -end

def get_recent_ip():
    rece_ip = None
    file_path = os.path.abspath(os.path.dirname(__file__))+'recent_ip.txt'
    if os.path.isfile(file_path):
        with io.open(file_path,'r',encoding='utf-8') as f:
            rece_ip = f.read()
        os.remove(file_path)
    return rece_ip

def init():
    parser = argparse.ArgumentParser()
    parser.add_argument("iprange", help="""The string of IP range, such as: "1.1.1.0-1.1.1.255"   : begin_ip-end_ip""")
    args = parser.parse_args()
    return args.iprange

def fetch_ip(ip):
    d={}
    while True:
        try:
            url = 'http://ip.taobao.com/service/getIpInfo.php?ip=' + ip
            response = urllib2.urlopen(url,timeout=3)
            if response.getcode() == 200:
                datas = response.read()
                try :
                    jsondata = json.loads(datas)
                    break
                except:
                    time.sleep(3)
                    continue
            time.sleep(5)#避免淘宝返回502等错误
        except :
            time.sleep(5)#避免socket挂掉
    data = jsondata['data']
    if jsondata['code'] == 0:
        info = data['country_id']+'\t'+data['country']+'\t'+data['region']+'\t'+\
                                    data['city']+'\t'+data['isp']+'\n'
        d={
            "ip":data['ip'],
            "res":info
        }
    return d


def merge_ip(iter_items,iprange):
    global RECENT_IP
    begin_ip,end_ip,current_ip = None,None,None
    with io.open('ip('+iprange+').txt','a+',encoding='utf-8') as outputfile:
        for current_ip in iter_items:
            if not begin_ip:
                begin_ip = current_ip
            else:
                b_res = begin_ip['res']
                c_res = current_ip['res']
                if not (set([b_res])&set([c_res])):
                    res =begin_ip['ip']+'\t'+end_ip['ip']+'\t'+b_res
                    begin_ip = current_ip
                    RECENT_IP = begin_ip['ip']#记录服务器断开的时候出错的ip
                    outputfile.write(res)
                    outputfile.flush()
            end_ip = current_ip
        res = begin_ip['ip']+'\t'+end_ip['ip']+'\t'+begin_ip['res']
        outputfile.write(res)

def switch_ips(iprange,rec_ip):
    iprange = iprange.split('-')
    iprange[0] = rec_ip
    iprange = '-'.join(iprange)
    return iprange

def main():

    iprange = init()
    old_iprange = iprange
    rec_ip = get_recent_ip()
    if rec_ip:
        iprange = switch_ips(iprange,rec_ip)#中断之后，从上次开始进行查询
    pool = Pool()
    try:
        iter_items = pool.imap(fetch_ip,add_ip(iprange))
        merge_ip(iter_items,old_iprange)
    except :
        with io.open('recent_ip.txt','w',encoding='utf-8') as f:
            f.write(RECENT_IP)


if __name__ == '__main__':
    s = time.time()
    main()
    print(time.time()-s)