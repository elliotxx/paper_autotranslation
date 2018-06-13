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
import execjs

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
MAX_PROCESS_NUM = 10



# 谷歌翻译免费 api 接口
# 该类为网友封装的第三方免费翻译接口，我在此基础上做了一些修改
# 参考自：https://github.com/Chinese-boy/Many-Translaters
class Google():
    proxies = None
    timeout = 10
    max_try_cnt = 10

    def __init__(self):
        self.ctx = execjs.compile(""" 
        function TL(a) { 
        var k = ""; 
        var b = 406644; 
        var b1 = 3293161072; 

        var jd = "."; 
        var $b = "+-a^+6"; 
        var Zb = "+-3^+b+-f"; 

        for (var e = [], f = 0, g = 0; g < a.length; g++) { 
            var m = a.charCodeAt(g); 
            128 > m ? e[f++] = m : (2048 > m ? e[f++] = m >> 6 | 192 : (55296 == (m & 64512) && g + 1 < a.length && 56320 == (a.charCodeAt(g + 1) & 64512) ? (m = 65536 + ((m & 1023) << 10) + (a.charCodeAt(++g) & 1023), 
            e[f++] = m >> 18 | 240, 
            e[f++] = m >> 12 & 63 | 128) : e[f++] = m >> 12 | 224, 
            e[f++] = m >> 6 & 63 | 128), 
            e[f++] = m & 63 | 128) 
        } 
        a = b; 
        for (f = 0; f < e.length; f++) a += e[f], 
        a = RL(a, $b); 
        a = RL(a, Zb); 
        a ^= b1 || 0; 
        0 > a && (a = (a & 2147483647) + 2147483648); 
        a %= 1E6; 
        return a.toString() + jd + (a ^ b) 
    }; 

    function RL(a, b) { 
        var t = "a"; 
        var Yb = "+"; 
        for (var c = 0; c < b.length - 2; c += 3) { 
            var d = b.charAt(c + 2), 
            d = d >= t ? d.charCodeAt(0) - 87 : Number(d), 
            d = b.charAt(c + 1) == Yb ? a >>> d: a << d; 
            a = b.charAt(c) == Yb ? a + d & 4294967295 : a ^ d 
        } 
        return a 
    } 
    """)

    def getTk(self, text):
        return self.ctx.call("TL", text)

    def translate(self, paragraph_no, content):
        if len(content) > 4891:
            print("Text length exceed!")
            return

        # get tk
        tk = self.getTk(content)
        # content = urllib.parse.quote(content)

        # url & params
        url = "http://translate.google.cn/translate_a/single"
        params = {
            'client' : 't',
            'sl' : 'en',
            'tl' : 'zh-CN',
            'hl' : 'zh-CN',
            'dt' : 'bd',
            'dt' : 'ex',
            'dt' : 'ld',
            'dt' : 'md',
            'dt' : 'qca',
            'dt' : 'rw',
            'dt' : 'rm',
            'dt' : 'ss',
            'dt' : 't',
            'ie' : 'UTF-8',
            'oe' : 'UTF-8',
            'clearbtn' : '1',
            'otf' : '1',
            'pc' : '1',
            'srcrom' : '0',
            'ssel' : '0',
            'tsel' : '0',
            'kc' : '2',
            'tk' : tk,
            'q' : content
        }
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}

        # url = "http://translate.google.cn/translate_a/single?client=t" \
        #       "&sl=en&tl=zh-CN&hl=zh-CN&dt=at&dt=bd&dt=ex&dt=ld&dt=md&dt=qca" \
        #       "&dt=rw&dt=rm&dt=ss&dt=t&ie=UTF-8&oe=UTF-8&clearbtn=1&otf=1&pc=1" \
        #       "&srcrom=0&ssel=0&tsel=0&kc=2&tk=%s&q=%s" % (tk, content)

        # 设置代理
        result = ''
        cur_try_cnt = 0
        while True:
            try:
                # 发送请求
                if self.proxies == None:
                    response = requests.get(url=url, params=params, headers=headers, timeout=self.timeout)
                else:
                    response = requests.get(url=url, params=params, headers=headers, proxies=self.proxies, timeout=self.timeout)

                # 获取翻译结果
                result = response.content.decode('utf-8')

                # 处理译结果
                result = eval(result.replace('null','None'))
                result = map(lambda x: x[0], result[0])
                result = ''.join(result)
                result = result.decode('utf8')

                break
            except Exception, e:
                if log_level > 1:
                    print e
                    print 'Retry!'

                cur_try_cnt += 1
                if cur_try_cnt < self.max_try_cnt:
                    time.sleep(3)
                    ip = ProxyIP().get()
                    self.proxies = {'http':'%s:%d'%(ip[0],ip[1])}
                else:
                    print '%d Exceed max try cnt! Abandon!'%paragraph_no
                    return ''
        return result


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
        self.timeout = 20

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
                time.sleep(3)
                ip = ProxyIP().get()
                self.proxies = {'http':'%s:%d'%(ip[0],ip[1])}
        return result

def translate_per_paragraph(paragraph_no, paragraph):
    '''翻译每个段落'''
    # trans_paragraph = Youdao(paragraph).get_result()
    trans_paragraph = Google().translate(paragraph_no, paragraph)
    print '[Paragraph %d translate successfully.]'%(paragraph_no+1)
    time.sleep(2 + random.random()*3)
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
            print '[Get content of page %d ...]'%(page_no+1)
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
    paragraph_len = len(paragraph_list)
    print '[Start translate all pdf paragraphs(%d)...]'%paragraph_len
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
    print '[Create empyt file...]'
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

            if trans_paragraph == None:
                continue
            f.write(trans_paragraph.encode('utf8'))
            f.write('\n\n')
    print '[The translated document has been written to local.]'





if __name__ == '__main__':
    filename = sys.argv[1]

    paragraph_list = Pdf2Txt(filename)
    translate(paragraph_list, '%s.txt'%filename)

