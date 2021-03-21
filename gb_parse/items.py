# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class GbParseItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class GbAutoYoulaItem(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    price = scrapy.Field()
    photos = scrapy.Field()
    characteristics = scrapy.Field()
    descriptions = scrapy.Field()
    author = scrapy.Field()
    phone = scrapy.Field()
    price = scrapy.Field()

class GbHhItem(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    salary = scrapy.Field()
    description = scrapy.Field()
    key_skills = scrapy.Field()
    employer = scrapy.Field()
    title_employer = scrapy.Field()
    site_employer = scrapy.Field()
    field_employer = scrapy.Field()
    description_employer = scrapy.Field()

class GbInstagramItem(scrapy.Item):
    _id = scrapy.Field()
    tag_name = scrapy.Field()
    date_parse = scrapy.Field()
    data = scrapy.Field()
    images = scrapy.Field()

class GbTagItem(GbInstagramItem):
    pass

class GbTagPostsCollection(GbInstagramItem):
    pass

class GbtagPost(GbInstagramItem):
    pass


class GbInstagramUserItem(scrapy.Item):
    _id = scrapy.Field()
    user_id = scrapy.Field()
    user_name = scrapy.Field()
    followers = scrapy.Field()
    following = scrapy.Field()