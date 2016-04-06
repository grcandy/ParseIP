#coding:utf-8

import io


IP_KU = 'ip.txt'

def ipaddr_to_binary(ip):
    q = ip.split('.')
    return reduce(lambda a,b: long(a)*256 + long(b), q)

def valid_ip(query_ip):
    q = query_ip.split('.')
    return len(q) == 4 and len(filter(lambda x: x >= 0 and x <= 255, \
        map(int, filter(lambda x: x.isdigit(), q)))) == 4

class IP(object):
    def __init__(self,query_ip):
        self.query_ip = ipaddr_to_binary(query_ip)
        assert  valid_ip(query_ip) is True,"the ip is invalid,please check!"
        self.begin_ip = None
        self.end_ip = None

    def find(self):
        '''
        :return:isp的信息
        '''
        with io.open(IP_KU,'r',encoding='utf-8') as inputfile:
            for line in inputfile:
                element = line.split('\t')
                self.begin_ip = ipaddr_to_binary(element[0])
                self.end_ip = ipaddr_to_binary(element[1])
                if self.begin_ip<=self.query_ip and self.query_ip<=self.end_ip:
                    d ={'success':1,
                        'data':{
                            "country_id":element[2],
                            "isp":element[6].strip('\n'),
                            "country":element[3],
                            "region":element[4],
                            "city":element[5]
                            }
                        }
                    return d
            return {'success':0,'data':'error'}

def get_isp_info(ipaddre):
    return IP(ipaddre).find()


if __name__ == "__main__":
    import time
    a=time.time()
    print(get_isp_info('1.45.0.0'))
    print(time.time()-a)
