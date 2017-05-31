from datetime import datetime
import re
import scrapy

from  ..items import OpengazettesSlItem

class GazettesSpider(scrapy.Spider):
    name = "sl_gazettes"
    allowed_domains = ["dropbox.com"]

    def start_requests(self):
        url = 'https://www.dropbox.com/sh/mmf7rbcwaz1v1ta/' \
              'AAB9zdJUMaEzbU7HjpaSX1ura?dl=0'

        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        # Get the year to be crawled from the arguments
        # The year is passed like this: scrapy crawl gazettes -a year=2017
        # Default to current year if year not passed in
        try:
            year = self.year
        except AttributeError:
            year = datetime.now().strftime('%Y')

        year_links = len(response.xpath(
            "//li[@class='sl-grid-cell']").extract()) + 1
        year_link = self.get_year_link(response, year_links, year)

        # access the year_link
        if year_link:
            request = scrapy.Request(year_link, callback=self.get_year_gazettes)
            yield request

    def get_year_link(self, response, year_links, year):
        for year_num in range(1, year_links):
            year_name = response.xpath(
                "//li[@class='sl-grid-cell'][{}]/a/div[2]/text()"
            .format(year_num)).extract_first().lower()

            if year_name.startswith(str(year)):
                year_link = response.xpath(
                    "//li[@class='sl-grid-cell'][{}]/a/@href"
                        .format(year_num)
                ).extract_first()

                return year_link

        return False


    def get_year_gazettes(self, response):
        gazette_links = response.xpath(
                "//ol/li")
        for link in gazette_links:
            item = OpengazettesSlItem()
            item['gazette_link'] = link.xpath('a/@href').extract_first()
            item['filename'] = link.xpath(
                'a/div/img/@alt').extract_first()

            if not item['filename'].endswith('.pdf'):
                continue
            item = self.create_meta(item)
            yield item

    def create_meta(self, item):
        opts = re.findall(r'\b[A-Za-z]+\b', item['filename'])
        num_opts = re.findall(r'\d+', item['filename'])
        item['gazette_volume'] = opts[0].upper()
        item['special_issue'] = True if 'special' in opts else False
        item['publication_date'] = datetime.strptime('{}-{}-{}'.format(
            num_opts[-2], num_opts[-3],num_opts[-4]),'%Y-%m-%d')

        item['gazette_number'] = num_opts[-1]
        item['filename'] = 'opengazettes-sl-vol-%s-no-%s-dated-%s-%s-%s' % \
                           (item['gazette_volume'], item['gazette_number'],
                            item['publication_date'].strftime("%d"),
                            item['publication_date'].strftime("%B"),
                            item['publication_date'].strftime("%Y"))

        item['gazette_title'] = 'Sierra Leone Government ' \
                                'Gazette Vol.%s No.%s Dated %s %s %s' % \
                                (item['gazette_volume'], item['gazette_number'],
                                 item['publication_date'].strftime("%d"),
                                 item['publication_date'].strftime("%B"),
                                 item['publication_date'].strftime("%Y"))
        item['file_urls'] = [item['gazette_link'].replace('?dl=0', '?dl=1')]

        return item











