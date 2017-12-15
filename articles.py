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

#Defining variable for spiders and pipeline
full_url_acs = ''
full_url_spr = ''
doi_acs = ''
doi_spr = ''

#Sort DOIs, under each if statement the corresponding spider for each publisher
dois = open('doi_list.txt')
doi_list = dois.readlines()
fixed_doi = []
for x in doi_list:
    fixed_doi.append(re.sub('\n','', x))
doi_list = fixed_doi

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

#New names for each file ACS
    doiacs_name = re.sub('/', '', doi_acs)
    nameacs = 'doiacs-%s.jl' %(doiacs_name)

#New names for each file ACS
    doispr_name = re.sub('/', '', doi_spr)
    namespr = 'doispr-' + doispr_name + '.jl'

#Pipeline to turn data into JSON file for ACS
    class JsonWriterPipeline(object):

        def open_spider(self, spider):
            self.file = open(nameacs, 'w')

        def close_spider(self, spider):
            self.file.close()

        def process_item(self, item, spider):
            line = json.dumps(dict(item)) + "\n"
            self.file.write(line)
            return item

#Pipeline for Springer
    class JsonWriterPipelineSpr(object):

        def open_spider(self, spider):
            self.file = open(namespr, 'w')

        def close_spider(self, spider):
            self.file.close()

        def process_item(self, item, spider):
            line = json.dumps(dict(item)) + "\n"
            self.file.write(line)
            return item

#Defines the items Scrapy is looking for
class ArticleItem(Item):
    title = Field()
    authors = Field()
    doi = Field()
    abstract = Field()
    text = Field()
    figures = Field()    

#Pipeline for Springer
class JsonWriterPipelineSpr(object):

    def open_spider(self, spider):
        self.file = open(namespr, 'w')

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        line = json.dumps(dict(item)) + "\n"
        self.file.write(line)
        return item	

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
#        item['abstract'] = response.xpath('//section[@class="Abstract", @id="Abs1", @tabindex="-1", @lang="en"]/descendant::text()').extract
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

#Opens data scraped into many lists, edits file to concatenate lists
#resultACS = json.load(open('testarticles.jl',mode='r'))
#resultACS['abstract'] = concatenate_list(resultACS['abstract'])
#resultACS['text'] = concatenate_list(resultACS['text'])

#with open('testarticles.jl', 'w') as jsonFile:
#    json.dump(resultACS, jsonFile)


#resultSpr = json.load(open('testarticlesSpr.jl', mode='r'))
#resultSpr['text'] = concatenate_list(resultSpr['text'])

#fixed_authors = []
#for x in resultSpr['authors']:
#    fixed_authors.append(re.sub('\xa0', ' ', x))
#resultSpr['authors'] = fixed_authors
#with open('testarticlesSpr.jl', 'w') as jsonFile:
#    json.dump(resultSpr, jsonFile)

print(doi_acs)
print(nameacs)
