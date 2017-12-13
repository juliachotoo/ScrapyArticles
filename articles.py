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

from scrapy.utils.markup import remove_tags #to remove html tags

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

#Pipeline to remove tags and extra letters in text and authors respectively
#class TagPipeline(object):
#    def process_item(self, item, spider):
#        item['abstract'] = concatenate_list(item['abstract'])    
#        return item['abstract']

#Pipeline to turn data into JSON file for ACS
class JsonWriterPipeline(object):

    def open_spider(self, spider):
        self.file = open('testarticles.jl', 'w')

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        line = json.dumps(dict(item)) + "\n"
        self.file.write(line)
        return item

#Pipeline for Springer
class JsonWriterPipelineSpr(object):

    def open_spider(self, spider):
        self.file = open('testarticlesSpr.jl', 'w')

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        line = json.dumps(dict(item)) + "\n"
        self.file.write(line)
        return item

#Defining variable for spiders
full_url_acs = ''
full_url_spr = ''

#Sort DOIs, under each if statement the corresponding spider for each publisher
doi_list = ["10.1021/ja302991b", "10.1016/j.micromeso.2012.01.033", "10.1007/s10450-012-9423-1", "10.1002/aic.690470520", "10.1007/s10450-013-9527-2"]
#doi_list = [ "10.1007/s10450-012-9423-1" ]
#doi_list = ["10.1021/ja302991b"]
for d in doi_list:
    test_url = 'http://dx.doi.org/{0}'.format(d)
    
    headers = {'Accept': 'application/citeproc+json'}
    bib_info = json.loads(requests.get(test_url, headers=headers).content)
    if bib_info['publisher'] == 'American Chemical Society (ACS)':
        
        doi_acs = bib_info.get('DOI')
        full_url_acs = 'http://pubs.acs.org/doi/full/{0}'.format(doi_acs)
        response_acs = urlopen(full_url_acs)
        content_acs = response_acs.read()    

    elif bib_info['publisher'] == 'Springer Nature':
        
        doi_spr = bib_info.get('DOI')
        full_url_spr = 'http://link.springer.com/article/{0}'.format(doi_spr)
        response_spr = urlopen(full_url_spr)
        content_spr = response_spr.read()

    else:
        print('wrong publisher')	

#Code for Spiders
class ArticleSpider(scrapy.Spider):
     name = 'ArticleSpider'
     allowed_domains = ["http://pubs.acs.org/"]
     start_urls = [full_url_acs]
            
     custom_settings = {
         'ITEM_PIPELINES': {'__main__.JsonWriterPipeline': 2,}
     }
            
     def parse(self, response):
         item = ArticleItem()
         item['title'] = response.xpath('//span[@class="hlFld-Title"]/text()').extract()
         item['authors'] = response.xpath('//a[@id="authors"]/text()').extract()
         item['doi'] = response.xpath('//div[@id="doi"]/text()').extract()
         item['abstract'] = response.xpath('//p[@class="articleBody_abstractText"]/text()').extract()
         item['text'] = response.xpath('//div[@class="hlFld-Fulltext"]/descendant::text()').extract()
         item['figures'] = response.xpath('//img[@alt="figure"]').extract()
         yield item

class ArticleSpiderSpr(scrapy.Spider):
    name = 'ArticleSpiderSpr'
    allowed_domains = ["https://link.springer.com/journal/10450"]
    start_urls = [full_url_spr]
            
    custom_settings = {
        'ITEM_PIPELINES': {'__main__.JsonWriterPipelineSpr': 3,}
    }

    def parse(self, response):
        item = ArticleItem()
        item['title'] = response.xpath('//h1[@class="ArticleTitle"]/text()').extract()
        item['authors'] = response.xpath('//span[@class="authors__name"]/text()').extract()
        item['doi'] = response.xpath('//span[@id="doi-url"]/text()').extract()
 #       item['abstract'] = response.xpath('//section[@class="Abstract"]/descendant::text()').extract
        item['text'] = response.xpath('//div[@id="body"]/descendant::text()').extract()
        item['figures'] = response.xpath('//div[@class="MediaObject"]').extract()
        yield item
                
#Runs both Spiders
process = CrawlerProcess({'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'})
process.crawl(ArticleSpider)
process.crawl(ArticleSpiderSpr)
process.start()


def concatenate_list(input):
    output = ''
    for item in input:
        output = output+item
    return output

resultACS = json.load(open('testarticles.jl',mode='r'))
resultACS['abstract'] = concatenate_list(resultACS['abstract'])
resultACS['text'] = concatenate_list(resultACS['text'])
print(resultACS['abstract'])
print(resultACS['authors'])

resultSpr = json.load(open('testarticlesSpr.jl', mode='r'))
print(resultSpr['title'])
resultSpr['text'] = concatenate_list(resultSpr['text'])
print(resultSpr['text'])
