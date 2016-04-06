#coding:utf-8
#-----------私有地址段-----------
#0.0.0.0-0.255.255.255是保留地址 0-16777215
#127.0.0.0到127.255.255.255是保留地址，用做循环测试用的 2130706432-2147483647
#10.0.0.0到10.255.255.255是私有地址 167772160-184549375
#169.254.0.0到169.254.255.255是保留地址 2851995648-2852061183
#172.16.0.0到172.31.255.255是私有地址   2886729728-2887778303
#192.168.0.0到192.168.255.255是私有地址 3232235520-3232301055

import urllib
import multiprocessing
import threading
import Queue
import os
import time
import json
import argparse
import re
import socket
import struct



if os =='nt':
	PREENCODE = 'gbk'
else:
	PREENCODE = 'utf-8'

FILTER_IPS = [(0,16777215),(2130706432,2147483647),(167772160,184549375),(2851995648,2852061183),\
			 (2886729728,2887778303),(3232235520,3232301055)]
########################################################################
class RateTimesLimit:
	'''依据相应的接口是否启动，次数请求限制
	rate:次数
	interval：表示每秒
	'''
	def __init__(self, rate, interval):
		self.rate = rate
		self.interval = interval
		self.lastcheck = time.time()
		self.count = 0
		self.lock = threading.Condition()

	def ratecontrol(self):
		self.lock.acquire()
		while True:
			span = time.time() - self.lastcheck
			if span >= self.interval:
				self.count = 1
				self.lastcheck = time.time()
				break
			elif self.count <= self.rate:
				self.count += 1
				break
			else:
				self.lock.wait(self.interval - span)
		self.lock.release()

########################################################################

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


def init():
	parser = argparse.ArgumentParser()
	parser.add_argument("iprange", help="""The string of IP range, such as: "1.1.1.0-1.1.1.255"   : begin_ip-end_ip""")
	args = parser.parse_args()
	return args.iprange

def create_threads(ratelimit,works,results,threadcounts,file_cur):
	for _ in range(threadcounts):
		thread = threading.Thread(target=worker, args=(ratelimit, works, results))
		thread.daemon = True
		thread.start()
	output_thread = threading.Thread(target=output, args=(file_cur, results))
	output_thread.daemon = True
	output_thread.start()

def fetch_ip(ip):
	url = 'http://ip.taobao.com/service/getIpInfo.php?ip=' + ip
	response = urllib.urlopen(url).read()
	jsondata = json.loads(response)
	if jsondata[u'code'] == 0:
		data = jsondata[u'data']
		# info = '\n'+data['ip']+'  '+data['country'].encode('utf-8')+data['region'].encode('utf-8')+\
		# 			data['city'].encode('utf-8')+'   '+data['isp'].encode('utf-8')
		info = data['ip']+'\t'+data['country_id']+'\t'+data['country']+'\t'+data['region']+'\t'+\
					data['city']+'\t'+data['isp']+'\n'
	return info.encode(PREENCODE)

def make_ips(works,iprange):
	for ip in add_ip(iprange):
		works.put(ip)


def worker(ratelimit, works, results):
	while True:
		try:
			#ratelimit.ratecontrol()#控制请求次数
			ip = works.get()
			result = fetch_ip(ip)
			results.put(result)
			works.task_done()
		except Queue.Empty:
			pass

def output(file_cur, results):
	while True:
		try:
			line = results.get()
			if line is not None:
				file_cur.write(line)
			results.task_done()
		except Queue.Empty:
			pass


def main():
	iprange = init()
	file_cur = open('ip('+iprange+').txt','a+')
	works = Queue.Queue()#任务队列
	results = Queue.Queue()#结果集队列
	ratelimit = None#RateTimesLimit(10,1)#淘宝最多10次/秒请求，#测试了好像也没什么限制
	threadcounts = multiprocessing.cpu_count() * 10#启动的线程数

	create_threads(ratelimit,works,results,threadcounts,file_cur)
	make_ips(works,iprange)
	works.join()
	results.join()

if __name__ == '__main__':
    s = time.time()
    main()
    print(time.time()-s)
