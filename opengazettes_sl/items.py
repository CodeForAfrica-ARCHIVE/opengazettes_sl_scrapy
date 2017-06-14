# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class OpengazettesSlItem(scrapy.Item):
    gazette_link = scrapy.Field()
    publication_date = scrapy.Field()
    gazette_number = scrapy.Field()
    gazette_volume = scrapy.Field()
    files = scrapy.Field()
    special_issue = scrapy.Field()
    file_urls = scrapy.Field()
    filename = scrapy.Field()
    gazette_title = scrapy.Field()
