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

import httplib
import md5
import urllib
import random

import requests
import hashlib
import time

import sys
import json

# 有道翻译免费 api 接口
class Youdao(object):
    def __init__(self, msg):
        self.msg = msg
        self.url = 'http://fanyi.youdao.com/translate_o?smartresult=dict&smartresult=rule'
        self.D = "ebSeFb%=XZ%T[KZ)c(sy!"
        self.salt = self.get_salt()
        self.sign = self.get_sign()

    def get_md(self, value):
        '''md5加密'''
        m = hashlib.md5()
        # m.update(value)
        print value
        m.update(value.decode('utf8').encode('utf-8','ignore'))
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
        html = requests.post(self.url, data=data, headers=headers).text
        # print(html)
        infos = json.loads(html)
        if 'translateResult' in infos:
            try:
                # result = infos['translateResult'][0][0]['tgt']
                # print(result)
                result = ''
                for p in infos['translateResult'][0]:
                    result += p['tgt']
                return result
            except:
                return ''

# 有道翻译收费 api 接口
def translate(text):
    '''文本翻译'''
    httpClient = None
    myurl = '/api'
    # text = 'good'
    fromLang = 'EN'
    toLang = 'zh-CHS'
    salt = random.randint(1, 65536)

    sign = appKey+text+str(salt)+secretKey
    m1 = md5.new()
    m1.update(sign)
    sign = m1.hexdigest()
    myurl = myurl+'?appKey='+appKey+'&q='+urllib.quote(text)+'&from='+fromLang+'&to='+toLang+'&salt='+str(salt)+'&sign='+sign
     
    try:
        httpClient = httplib.HTTPConnection('openapi.youdao.com')
        httpClient.request('GET', myurl)
     
        #response是HTTPResponse对象
        response = httpClient.getresponse()
        res = json.loads(response.read())
        return res
    except Exception, e:
        print e
    finally:
        if httpClient:
            httpClient.close()
                    

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
        for page in PDFPage.create_pages(document):
            interpreter.process_page(page)
            # 接受该页面的LTPage对象
            layout=device.get_result()
            layout_size = len(layout)
            for i,x in enumerate(layout):
                try:
                    if(isinstance(x,LTTextBox)):
                        for xx in x:
                            paragraph += xx.get_text().strip('\n').encode('utf8')
                        # 去除带论文商标的段落
                        if paragraph.find('©') != -1:
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
                    print str(e)
                    print "Failed!"
        # 写入文件
        with open('%s'%(Save_path),'w') as f:
            for paragraph in paragraph_list:
                # 写入英文段落
                f.write(paragraph)
                f.write('\n\n')
                # 写入翻译段落
                # res = translate(paragraph)
                # trans_paragraph = res['translation'][0].encode('utf8')
                # print trans_paragraph
                trans_paragraph = Youdao(paragraph).get_result().encode('utf8')
                print trans_paragraph.decode('utf8')
                f.write(trans_paragraph)
                f.write('\n\n')

    fp.close()




if __name__ == '__main__':
    filename = sys.argv[1]

    Pdf2Txt(filename,'%s.txt'%filename)

