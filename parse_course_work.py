import os
import dotenv
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from gb_parse.spiders.InstaGraf import InstagrafSpider


if __name__ == "__main__":
    dot_env_path = dotenv.load_dotenv('.env')
    crawler_settings = Settings()
    user_list = ['_maha._.perets_', 'alexey_perov']
    crawler_settings.setmodule("gb_parse.settings")
    crawler_proc = CrawlerProcess(settings=crawler_settings)
    crawler_proc.crawl(InstagrafSpider,
                       login=os.getenv("INST_LOGIN"),
                       password=os.getenv("INST_PASSWORD"),
                       user_list=user_list
                      )
    crawler_proc.start()