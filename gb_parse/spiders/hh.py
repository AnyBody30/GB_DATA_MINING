import scrapy
from ..loaders import HhLoader

class HhSpider(scrapy.Spider):
    name = 'hh'
    allowed_domains = ['hh.ru']
    start_urls = ['https://hh.ru/search/vacancy?schedule=remote&L_profession_id=0&area=113']

    _xpath_selectors = {
        "vacancies": "//a[@class='bloko-link HH-LinkModifier HH-VacancyActivityAnalytics-Vacancy']/@href",
        "pagination": "//a[@class='bloko-button HH-Pager-Control']",
        "vacancies_e": "//div[@class='company-vacancy-indent']/div[@class = 'vacancy-list-item']/..//a/@href"
    }

    _vacancy_xpaths = {
        "title": "//h1[@data-qa='vacancy-title']/text()",
        "salary": "//p[@class='vacancy-salary']/span[@data-qa='bloko-header-2']/text()",
        "description": "//div[@data-qa='vacancy-description']/..//text()",
        "key_skills": "//div[@class='bloko-tag-list']/..//span[@data-qa='bloko-tag__text']/text()",
        "employer": "//a[@class='vacancy-company-name']/@href"
    }

    _employer_xpaths = {
        "title_employer": "//h1[@data-qa='bloko-header-1']/span[@class='company-header-title-name']/text()",
        "site_employer": "//a[@data-qa='sidebar-company-site']/@href",
        "field_employer": "//div[@class='employer-sidebar-block']/p/text()",
        "description_employer": "//div[@data-qa='company-description-text']/..//text()"
    }


    def _get_follow_xpath(self, response, select_str, callback, **kwargs):
        for link in response.xpath(select_str):
            yield response.follow(link, callback=callback, cb_kwargs=kwargs)


    def parse(self, response):
        yield from self._get_follow_xpath(
            response, self._xpath_selectors["pagination"], self.parse
        )
        yield from self._get_follow_xpath(
            response, self._xpath_selectors["vacancies"], self.vacancy_parse
        )


    def vacancy_parse(self, response):
        yield from self._get_follow_xpath(
            response, self._vacancy_xpaths["employer"], self.employer_parse
        )
        loader = HhLoader(response=response)
        loader.add_value("url", response.url)
        for key, xpath in self._vacancy_xpaths.items():
            loader.add_xpath(key, xpath)
        yield loader.load_item()


    def employer_parse (self, response):
        yield from self._get_follow_xpath(
            response, self._xpath_selectors["vacancies_e"], self.vacancy_parse
        )
        loader = HhLoader(response=response)
        loader.add_value("url", response.url)
        for key, xpath in self._employer_xpaths.items():
            loader.add_xpath(key, xpath)
        yield loader.load_item()