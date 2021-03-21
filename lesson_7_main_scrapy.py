import os
import dotenv
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from gb_parse.spiders.autoyoula import AutoyoulaSpider
from gb_parse.spiders.hh import HhSpider
from gb_parse.spiders.instagram import InstagramSpider
from gb_parse.spiders.InstagramFollowers import InstagramfollowersSpider


if __name__ == "__main__":
    dot_env_path = dotenv.load_dotenv('.env')
    crawler_settings = Settings()
    tags = ['python', 'java']
    user_list = ['utkinadasa715']
    crawler_settings.setmodule("gb_parse.settings")
    crawler_proc = CrawlerProcess(settings=crawler_settings)
    #crawler_proc.crawl(AutoyoulaSpider)
    #crawler_proc.crawl(HhSpider)
    #crawler_proc.crawl(InstagramSpider,
    #                   login=os.getenv("INST_LOGIN"),
    #                   password = os.getenv("INST_PASSWORD"),
    #                   tags=tags
    #                  )
    crawler_proc.crawl(InstagramfollowersSpider,
                       login=os.getenv("INST_LOGIN"),
                       password=os.getenv("INST_PASSWORD"),
                       user_list=user_list
                      )
    crawler_proc.start()