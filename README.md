## 论文自动翻译
自动翻译论文的 pdf，生成带翻译段落的 txt 文档

## 介绍
PDF 解析成文本采用 pdfminer 库，主要参考：[解决pdfminer ImportError: cannot import name process_pdf](https://blog.csdn.net/MrLevo520/article/details/52136414) 和 [（7）PDFMiner提取PDF文本](https://blog.csdn.net/fighting_no1/article/details/51038942)

翻译部分调用了网友封装的有道翻译的免费 API，参考 github：[Chinese-boy/Many-Translaters](https://github.com/Chinese-boy/Many-Translaters)

ps：有道翻译API现在收费了，一篇4页的论文翻译一次就花了1元。


## 依赖
注意：基于 python 2.7
* pdfminer
* requests


## 用法
```
paper_translation.py 2017_ICSA_Bidirectional Mapping between Architecture Model and Code for Synchronization.pdf
```

## 参考资料
* PDFMiner 官方文档  
https://euske.github.io/pdfminer/

* PDFMiner Github  
https://github.com/euske/pdfminer

* pdfminer API介绍：pdf网页爬虫  
https://www.cnblogs.com/rongyux/p/5445723.html

* ~~有道智云（有道翻译官方API，收费）~~  
http://ai.youdao.com/gw.s

* ~~Python学习笔记(28)-Python读取word文本~~  
https://blog.csdn.net/woshisangsang/article/details/75221723

* ~~python 操作 office~~  
https://www.cnblogs.com/Jacklovely/p/5743868.html