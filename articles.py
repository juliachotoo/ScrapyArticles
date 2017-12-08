#Import Statements
import scrapy
from urllib.request import urlopen #to open the urls that the dois are put into
import json
import requests
import pprint
import logging

#for the ArticleItem section
from scrapy.item import Item, Field
from scrapy.selector import Selector
from scrapy.spiders import Spider

#for the spiders
from scrapy import Spider
from scrapy.http import TextResponse #defines what response is in xpath

#to run spider in Jupytuer notebook, have to restart the kernel each time to run it
from scrapy.settings import Settings
from scrapy.crawler import CrawlerProcess

#for pipeline
import re

#Defines the items Scrapy is looking for
class ArticleItem(Item):
    title = Field()
    authors = Field()
    doi = Field()
    abstract = Field()
    text = Field()
    figures = Field()

#Sort DOIs, under each if statement the corresponding spider for each publisher
doi_list = ["10.1021/ja302991b", "10.1016/j.micromeso.2012.01.033", "10.1007/s10450-012-9423-1", "10.1002/aic.690470520", "10.1007/s10450-013-9527-2"]
for d in doi_list:
    test_url = 'http://dx.doi.org/{0}'.format(d)
    
    headers = {'Accept': 'application/citeproc+json'}
    bib_info = json.loads(requests.get(test_url, headers=headers).content)
    if bib_info['publisher'] == 'American Chemical Society (ACS)':
        
        doi_acs = bib_info.get('DOI')
        full_url_acs = 'http://pubs.acs.org/doi/full/{0}'.format(doi_acs)
        response_acs = urlopen(full_url_acs)
        content_acs = response_acs.read()
        
        class ArticleSpider(scrapy.Spider):
            name = 'ArticleSpider'
            allowed_domains = ["http://pubs.acs.org/"]
            start_urls = [full_url_acs]
            
            def parse(self, response):
                item = ArticleItem()
                item['title'] = response.xpath('//span[@class="hlFld-Title"]/text()').extract()
                item['authors'] = response.xpath('//a[@id="authors"]/text()').extract()
                item['doi'] = response.xpath('//div[@id="doi"]/text()').extract()
                item['abstract'] = response.xpath('//p[@class="articleBody_abstractText"]/text()').extract()
                item['text'] = response.xpath('//div[@class="hlFld-Fulltext"]/descendant::text()').extract()
                item['figures'] = response.xpath('//img[@alt="figure"]').extract()
                yield item

    elif bib_info['publisher'] == 'Springer Nature':
        
        doi_spr = bib_info.get('DOI')
        full_url_spr = 'http://link.springer.com/article/{0}'.format(doi_spr)
        print(full_url_spr)
        response_spr = urlopen(full_url_spr)
        content_spr = response_spr.read()
        
        class ArticleSpiderSpr(scrapy.Spider):
            name = 'ArticleSpiderSpr'
            allowed_domains = ["https://link.springer.com/journal/10450"]
            start_urls = [full_url_spr]
    
            def parse(self, response):
                item = ArticleItem()
                item['title'] = response.xpath('//h1[@class="ArticleTitle"]/text()').extract()
                item['authors'] = response.xpath('//span[@class="authors__name"]/text()').extract()
                item['doi'] = response.xpath('//span[@id="doi-url"]/text()').extract()
                item['abstract'] = response.xpath('//p[@class="Para"]/text()').extract
                item['text'] = response.xpath('//div[@id="body"]').extract()
                item['figures'] = response.xpath('//div[@class="MediaObject"]').extract()
                yield item

    else:
        print('wrong publisher')	

process = CrawlerProcess({'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'})
process.crawl(ArticleSpiderSpr)
process.start()
