import re
import base64
import scrapy
from ..loaders import AutoyoulaLoader


class AutoyoulaSpider(scrapy.Spider):
    name = "autoyoula"
    allowed_domains = ["auto.youla.ru"]
    start_urls = ["https://auto.youla.ru/"]


    _xpath_selectors = {
        "brands": "//div[@data-target='transport-main-filters']/"
        "div[contains(@class, 'TransportMainFilters_brandsList')]//"
        "a[@data-target='brand']/@href",
        "pagination": "//div[contains(@class, 'Paginator_block')]//a[contains(@class, 'Paginator_button')]/@href",
        "cars": "//span/article[@data-target='serp-snippet']/div[contains(@class, 'SerpSnippet_snippetContent')]/"
        "div[contains(@class, 'SerpSnippet_colLeft')]/a[@data-target='serp-snippet-photo']/@href"

    }
    _car_xpaths = {
        "title": "//div[@data-target='advert-title']/text()",
        "photos": "//figure/picture/img/@src",
        "characteristics": "//h3[contains(text(), 'Характеристики')]/..//"
        "div[contains(@class, 'AdvertSpecs_row')]",
        "descriptions": "//div[contains(@class, 'AdvertCard_descriptionInner')]/text()",
        "price": "//div[@data-target='advert-price']"
    }



    @staticmethod
    def get_author_id(response):
        js_selectors = response.xpath("//script[contains(text(), 'window.transitState = decodeURIComponent')]")
        for selector in js_selectors:
            try:
                    re_pattern = re.compile(r"youlaId%22%2C%22(\w+)%22%2C%22avatar")
                    result = re.findall(re_pattern, selector.get())
                    if result:
                        return f"https://youla.ru/user/{result[0]}"
            except TypeError:
                pass
        return

    @staticmethod
    def get_phone(response):
        js_selectors = response.xpath("//script[contains(text(), 'window.transitState = decodeURIComponent')]")
        for selector in js_selectors:
            try:
                re_pattern = re.compile(r"phone%22%2C%22([\w|\+|/]+)%3D%3D%22%2C")
                result = re.findall(re_pattern, selector.get())
                if result:
                    return base64.b64decode(base64.b64decode(f'{result[0]}=='.encode("UTF-8"))).decode("UTF-8")
            except TypeError:
                pass
        return


    def _get_follow_xpath(self, response, select_str, callback, **kwargs):
        for link in response.xpath(select_str):
            yield response.follow(link, callback=callback, cb_kwargs=kwargs)

    def parse(self, response, *args, **kwargs):

        yield from self._get_follow_xpath(
            response, self._xpath_selectors["brands"], self.brand_parse
        )

    def brand_parse(self, response, **kwargs):
        yield from self._get_follow_xpath(
            response, self._xpath_selectors["pagination"], self.brand_parse,
        )
        yield from self._get_follow_xpath(response, self._xpath_selectors["cars"], self.car_parse)

    def car_parse(self, response):
        loader = AutoyoulaLoader(response=response)
        loader.add_value("url", "")
        loader.add_value("url", response.url)
        loader.add_value("author", self.get_author_id(response))
        loader.add_value("phone", self.get_phone(response))
        for key, xpath in self._car_xpaths.items():
            loader.add_xpath(key, xpath)
        yield loader.load_item()