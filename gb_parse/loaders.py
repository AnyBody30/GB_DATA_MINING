from scrapy.loader import ItemLoader
from scrapy import Selector
from itemloaders.processors import TakeFirst, MapCompose, Join
from .items import GbAutoYoulaItem, GbHhItem


def get_characteristics(item):
    selector = Selector(text=item)
    data = {
        "name": selector.xpath(
            "//div[contains(@class, 'AdvertSpecs_label')]/text()"
        ).extract_first(),
        "value": selector.xpath(
            "//div[contains(@class, 'AdvertSpecs_data')]//text()"
        ).extract_first(),
    }
    return data

def get_price(item):
    selector = Selector(text=item)
    return float(selector.xpath("//div[@data-target='advert-price']/text()").get().replace("\u2009", ""))

def get_employer(item):
    return f'https://hh.ru{item}'

def get_field(item):
    return item.split(', ')


class AutoyoulaLoader(ItemLoader):
    default_item_class = dict
    url_out = TakeFirst()
    title_out = TakeFirst()
    author_out = TakeFirst()
    descriptions_out = TakeFirst()
    phone_out = TakeFirst()
    characteristics_in = MapCompose(get_characteristics)
    price_in = MapCompose(get_price)
    price_out = TakeFirst()

class HhLoader(ItemLoader):
    default_item_class = dict
    url_out = TakeFirst()
    title_out = TakeFirst()
    salary_out = Join()
    description_out = Join()
    employer_in = MapCompose(get_employer)
    employer_out = TakeFirst()
    title_employer_out = TakeFirst()
    site_employer_out = TakeFirst()
    field_employer_in = MapCompose(get_field)
    description_employer_out = Join()