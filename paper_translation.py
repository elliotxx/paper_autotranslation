#coding=utf8
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.layout import *
from pdfminer.converter import PDFPageAggregator
import urllib2
from cStringIO import StringIO

import requests
import hashlib
import time
import random

import sys
import json

from ProxyIP import ProxyIP

# 输出日志等级
# 0: 输出最简单，无段落信息，无错误信息
# 1: 输出段落信息，无错误信息
# 2: 输出段落信息，输出错误信息
log_level = 1

# 编码信息
input_encoding = sys.stdin.encoding
output_encoding = sys.stdout.encoding
file_encoding = 'utf8'


# 有道翻译免费 api 接口
class Youdao(object):
    def __init__(self, msg):
        self.msg = msg
        self.url = 'http://fanyi.youdao.com/translate_o?smartresult=dict&smartresult=rule'
        self.D = "ebSeFb%=XZ%T[KZ)c(sy!"
        self.salt = self.get_salt()
        self.sign = self.get_sign()
        self.proxies = None
        self.timeout = 5

    def get_md(self, value):
        '''md5加密'''
        m = hashlib.md5()
        m.update(value.encode('utf-8','ignore'))
        return m.hexdigest()

    def get_salt(self):
        '''根据当前时间戳获取salt参数'''
        s = int(time.time() * 1000) + random.randint(0, 10)
        return str(s)

    def get_sign(self):
        '''使用md5函数和其他参数，得到sign参数'''
        s = "fanyideskweb" + self.msg + self.salt + self.D
        return self.get_md(s)

    def get_result(self):
        '''headers里面有一些参数是必须的，注释掉的可以不用带上'''
        headers = {
            # 'Accept': 'application/json, text/javascript, */*; q=0.01',
            # 'Accept-Encoding': 'gzip, deflate',
            # 'Accept-Language': 'zh-CN,zh;q=0.9,mt;q=0.8',
            # 'Connection': 'keep-alive',
            # 'Content-Length': '240',
            # 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Cookie': 'OUTFOX_SEARCH_USER_ID=-2022895048@10.168.8.76;',
            # 'Host': 'fanyi.youdao.com',
            # 'Origin': 'http://fanyi.youdao.com',
            'Referer': 'http://fanyi.youdao.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; rv:51.0) Gecko/20100101 Firefox/51.0',
            # 'X-Requested-With': 'XMLHttpRequest'
        }
        data = {
            'i': self.msg,
            'from': 'en',
            'to': 'zh-CHS',
            'smartresult': 'dict',
            'client': 'fanyideskweb',
            'salt': self.salt,
            'sign': self.sign,
            'doctype': 'json',
            'version': '2.1',
            'keyfrom': 'fanyi.web',
            'action': 'FY_BY_CL1CKBUTTON',
            'typoResult': 'true'
        }
        # 设置代理
        result = ''
        while True:
            try:
                # 发送请求
                if self.proxies == None:
                    html = requests.post(self.url, data=data, headers=headers).text
                else:
                    html = requests.post(self.url, data=data, proxies=self.proxies, headers=headers, timeout=self.timeout).text

                # 获取翻译结果
                infos = json.loads(html)
                if 'translateResult' in infos:
                    result = ''
                    for p in infos['translateResult'][0]:
                        result += p['tgt']
                else:
                    raise Exception, 'No translateResult'

                break
            except Exception, e:
                if log_level > 1:
                    print e
                    print 'Retry!'
                ip = ProxyIP().get()
                self.proxies = {'http':'%s:%d'%(ip[0],ip[1])}
        return result

                    

def Pdf2Txt(path,Save_path):
    # 打开文件
    fp = open(path, 'rb')
    #来创建一个pdf文档分析器
    parser = PDFParser(fp)
    #创建一个PDF文档对象存储文档结构
    document = PDFDocument(parser)
    # 检查文件是否允许文本提取
    if not document.is_extractable:
        raise PDFTextExtractionNotAllowed
    else:
        # 创建一个PDF资源管理器对象来存储共赏资源
        rsrcmgr=PDFResourceManager()
        # 设定参数进行分析
        laparams=LAParams()
        # 创建一个PDF设备对象
        # device=PDFDevice(rsrcmgr)
        device=PDFPageAggregator(rsrcmgr,laparams=laparams)
        # 创建一个PDF解释器对象
        interpreter=PDFPageInterpreter(rsrcmgr,device)
        # 处理每一页
        paragraph = ''
        paragraph_list = []
        print '[Start get all pdf pages content...]'
        for page_no, page in enumerate(PDFPage.create_pages(document)):
            print '[Get content of page %d ...]'%(page_no)
            interpreter.process_page(page)
            # 接受该页面的LTPage对象
            layout=device.get_result()
            layout_size = len(layout)
            for i,x in enumerate(layout):
                try:
                    if(isinstance(x,LTTextBox)):
                        for xx in x:
                            content = xx.get_text().strip('\n')
                            paragraph += content

                        # 去除带论文商标的段落
                        if paragraph.find('©'.decode('utf8')) != -1:
                            paragraph = ''
                            continue
                        # 去除纯数字的段落
                        if paragraph.isdigit():
                            paragraph = paragraph_list[-1] + ' '
                            del paragraph_list[-1]
                            continue
                        paragraph_list.append(paragraph)
                        paragraph = ''
                except Exception, e:
                    if log_level > 1:
                        print str(e)
                        print "Failed!"
        print ''

        # 开始翻译
        print '[Start translate all pdf paragraph...]'
        # 清楚空白元素
        paragraph_list = filter(lambda x:False if x.strip == '' else True, paragraph_list)
        paragraph_len = len(paragraph_list)
        # 创建空文件
        with open('%s'%(Save_path),'w') as f:
            pass
        # 写入文件
        with open('%s'%(Save_path),'a') as f:
            for i, paragraph in enumerate(paragraph_list):
                print '[Translating %d/%d...]'%(i+1, paragraph_len)
                
                # 写入英文段落
                f.write(paragraph.encode('utf8'))
                f.write('\n\n')

                # 写入翻译段落
                if log_level > 0:
                    print paragraph.encode(output_encoding, 'ignore')
                trans_paragraph = Youdao(paragraph).get_result()
                
                if log_level > 0:
                    print '[Translate success!]'
                    print trans_paragraph.encode(output_encoding, 'ignore')
                    print ''
                f.write(trans_paragraph.encode('utf8'))
                f.write('\n\n')

    fp.close()




if __name__ == '__main__':
    filename = sys.argv[1]

    Pdf2Txt(filename,'%s.txt'%filename)

