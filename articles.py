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
 
#Defining variable for spiders and pipeline
full_url_acs = ''
full_url_spr = ''
doi_acs = ''
doi_spr = ''
nameacs = ''
namespr = ''
doiacs_name = ''
doispr_name = ''
acs_lst = []
spr_lst = []
full_url_acs_lst = []
full_url_spr_lst = []

#Sort DOIs, under each if statement the corresponding spider for each publisher
dois = open('doi_list.txt')
doi_lst = dois.readlines()
fixed_doi = []
for x in doi_lst:
    fixed_doi.append(re.sub('\n','', x))
doi_lst = fixed_doi

for d in doi_lst:
    test_url = 'http://dx.doi.org/{0}'.format(d)
    
    headers = {'Accept': 'application/citeproc+json'}
    bib_info = json.loads(requests.get(test_url, headers=headers).content)
    if bib_info['publisher'] == 'American Chemical Society (ACS)':
        
        doi_acs = bib_info.get('DOI')
        full_url_acs = 'http://pubs.acs.org/doi/full/{0}'.format(doi_acs)
        response_acs = urlopen(full_url_acs)
        content_acs = response_acs.read()

        acs_lst.append(doi_acs)
        full_url_acs_lst.append(full_url_acs)

    elif bib_info['publisher'] == 'Springer Nature':
        
        doi_spr = bib_info.get('DOI')
        full_url_spr = 'http://link.springer.com/article/{0}'.format(doi_spr)
        response_spr = urlopen(full_url_spr)
        content_spr = response_spr.read()

        spr_lst.append(doi_spr)
        full_url_spr_lst.append(full_url_spr)

    else:
        print('wrong publisher')

#Code for Spiders
class ArticleSpider(scrapy.Spider):
     name = 'ArticleSpider'
     allowed_domains = ["http://pubs.acs.org/"]
     start_urls = full_url_acs_lst
            
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
    allowed_domains = ["https://link.springer.com"]
    start_urls = full_url_spr_lst
            
    custom_settings = {
        'ITEM_PIPELINES': {'__main__.JsonWriterPipelineSpr': 1,}
    }

    def parse(self, response):
        item = ArticleItem()
        item['title'] = response.xpath('//h1[@class="ArticleTitle"]/text()').extract()
        item['authors'] = response.xpath('//span[@class="authors__name"]/text()').extract()
        item['doi'] = response.xpath('//span[@id="doi-url"]/text()').extract()
#        item['abstract'] = response.xpath('//p[@class="SimplePara"]/text()').extract()
        item['text'] = response.xpath('//div[@id="body"]/descendant::text()').extract()
        item['figures'] = response.xpath('//div[@class="MediaObject"]').extract()
        yield item

#New names for each file ACS
acs_final = []
for y in acs_lst:
    doiacs_name = re.sub('/', '', y)
    nameacs = 'doiacs-%s.jl' %(doiacs_name)
    acs_final.append(nameacs)

#Pipeline to turn data into JSON file for ACS
for y in acs_final:
    class JsonWriterPipeline(object):

        def open_spider(self, spider):
            self.file = open(y, 'w')

        def close_spider(self, spider):
            self.file.close()

        def process_item(self, item, spider):
            line = json.dumps(dict(item)) + "\n"
            self.file.write(line)
            return item

#New names for each file Springer
spr_final = []
for x in spr_lst:
    doispr_name = re.sub('/', '', x)
    namespr = 'doispr-%s.json' %(doispr_name)
    spr_final.append(namespr)
        
#Pipeline for Springer
for x in spr_final:
    class JsonWriterPipelineSpr(object):

        def open_spider(self, spider):
            self.file = open(x, 'w')

        def close_spider(self, spider):
            self.file.close()

        def process_item(self, item, spider):
            line = json.dumps(dict(item)) + "\n"
            self.file.write(line)
            return item

#Runs both Spiders
process = CrawlerProcess({'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'})
process.crawl(ArticleSpider)
process.crawl(ArticleSpiderSpr)
process.start()

##Opens data scraped into many lists, edits file to concatenate lists
#def concatenate_list(input):
#    output = ''
#    for item in input:
#        output = output+item
#        return output

#for d in doi_list:
    
#    resultACS = json.load(open(nameacs,mode='r'))
#    resultACS['abstract'] = concatenate_list(resultACS['abstract'])
#    resultACS['text'] = concatenate_list(resultACS['text'])

#    with open(nameacs, 'w') as jsonFile:
#        json.dump(resultACS, jsonFile)


#    resultSpr = json.load(open(namespr, mode='r'))
#    resultSpr['text'] = concatenate_list(resultSpr['text'])

#    fixed_authors = []
#    for x in resultSpr['authors']:
#        fixed_authors.append(re.sub('\xa0', ' ', x))
#    resultSpr['authors'] = fixed_authors
#    with open(namespr, 'w') as jsonFile:
#        json.dump(resultSpr, jsonFile)



#Problem going back in to concatenate texts and remove tags
#more than one file opening at a time doesn't work



print(acs_lst)
print(spr_lst)
print(spr_final)
print(acs_final)
print(full_url_acs_lst)
print(full_url_spr_lst)
