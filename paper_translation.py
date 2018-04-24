#coding=utf8
# 注意：程序基于 python 2.7
# 依赖：
# requests
# pdfminer
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
from multiprocessing import Pool

# 输出日志等级
# 0: 输出最简单，无段落信息，无错误信息
# 1: 输出段落信息，无错误信息
# 2: 输出段落信息，输出错误信息
log_level = 0

# 编码信息
input_encoding = sys.stdin.encoding
output_encoding = sys.stdout.encoding
file_encoding = 'utf8'

# 最大进程数
MAX_PROCESS_NUM = 50


# 有道翻译免费 api 接口
# 该类为网友封装的第三方免费翻译接口，我在此基础上做了一些修改
# 参考自：https://github.com/Chinese-boy/Many-Translaters
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

def translate_per_paragraph(paragraph_no, paragraph):
    '''翻译每个段落'''
    trans_paragraph = Youdao(paragraph).get_result()
    print '[Paragraph %d translate successfully.]'%(paragraph_no+1)
    return trans_paragraph

def Pdf2Txt(path):
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
                            content = xx.get_text().strip()
                            if paragraph != '' and paragraph[-1] == '-':
                                paragraph = paragraph[:-1] + content
                            else:
                                paragraph += ' ' + content
                        paragraph = paragraph.strip()

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
    fp.close()
    return paragraph_list

def translate(paragraph_list, Save_path):
    # 开始翻译
    print '[Start translate all pdf paragraph...]'
    paragraph_len = len(paragraph_list)
    # 清除空白元素
    paragraph_list = filter(lambda x:False if x.strip == '' else True, paragraph_list)
    
    # 创建进程池
    pool = Pool(processes = MAX_PROCESS_NUM)

    # 把所有抓取任务放到进程池中
    print '[Push all translate process in pool...]'
    start_time = time.clock()
    results = []
    for i, paragraph in enumerate(paragraph_list):
        # print 'Push process %d/%d in pool...'%(i+1, paragraph_len)
        results.append( pool.apply_async(translate_per_paragraph,(i, paragraph) ) )
    # print ''
    
    # 关闭进程池，使其不再接受请求
    pool.close()
    
    # 等待所有进程请求执行完毕
    print '[Start multiprocessing translate...]'
    pool.join()

    # 评估翻译速度
    end_time = time.clock()
    print '[All translation complete.]'
    total_time = float(end_time - start_time)
    print '[Total time : %f s]'%(total_time)
    print '[Average time of per process : %f s]'%(total_time/paragraph_len)
    print ''
    
    # 获取翻译结果
    print '[Get translation result...]'
    trans_paragraph_list = []
    for result in results:
        trans_paragraph_list.append( result.get() )

    # 创建空文件
    with open('%s'%(Save_path),'w') as f:
        pass
    # 写入文件
    print '[Writing all paragraph...]'
    with open('%s'%(Save_path),'a') as f:
        for i, paragraph in enumerate(paragraph_list):
            print '[Writing paragraph %d/%d...]'%(i+1, paragraph_len)
            
            # 写入英文段落
            f.write(paragraph.encode('utf8'))
            f.write('\n\n')

            # 写入翻译段落
            if log_level > 0:
                print paragraph.encode(output_encoding, 'ignore')
            trans_paragraph = trans_paragraph_list[i]
            
            if log_level > 0:
                print trans_paragraph.encode(output_encoding, 'ignore')
                print ''
            f.write(trans_paragraph.encode('utf8'))
            f.write('\n\n')
    print '[The translated document has been written to local.]'





if __name__ == '__main__':
    filename = sys.argv[1]

    paragraph_list = Pdf2Txt(filename)
    translate(paragraph_list, '%s.txt'%filename)

