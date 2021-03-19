# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import pymongo
from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline
from scrapy import Request


class GbParsePipeline:
    def process_item(self, item, spider):
        return item


class GbParseMongoPipeline:
    def __init__(self):
        client = pymongo.MongoClient()
        self.db = client["gb_parse_x_path"]

    def process_item(self, item, spider):
        self.db[type(item).__name__].insert_one(item)
        return item


class GbImagePipeLine(ImagesPipeline):

    def get_media_requests(self, item, info):
        for url in item.get("photos", []):
            yield Request(url)

    def item_completed(self, results, item, info):
        if results:
            item['photos'] = [itm[1] for itm in results]
        return item


class GbImageInstagramPipeLine(ImagesPipeline):

    def get_media_requests(self, item, info):
        for url in item.get("images", []):
            yield Request(url)

    def item_completed(self, results, item, info):
        if results:
            item['images'] = [itm[1] for itm in results]
        return item
