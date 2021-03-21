import scrapy
import json
from ..items import GbInstagramUserItem
from urllib.parse import urlencode
import time


class InstagramfollowersSpider(scrapy.Spider):
    name = 'InstagramFollowers'
    allowed_domains = ['www.instagram.com']
    start_urls = ['http://www.instagram.com/']
    api_url = "/graphql/query/"
    login_url = 'https://www.instagram.com/accounts/login/ajax/'

    def __init__(self, login, password, user_list, *args, **kwargs):
        self.login = login
        self.password = password
        self.user_list = user_list


    def parse(self, response):
        try:
            # извлекаем json из js, содержащего нужный X-CSRFToken для POST формы аутентификации
            js_data = self.js_data_extract(response)
            # вызываем форму аутентификации
            yield scrapy.FormRequest(
                self.login_url,
                method="POST",
                callback=self.parse,
                formdata={
                    'username': self.login,
                    'enc_password': self.password
                },
                headers={
                    "X-CSRFToken": js_data['config']['csrf_token']
                }
            )
        # если не удалось из js_data извлечь нужные ключи, значит считаем, что прошли аутентификацию
        # и уже на другой странице, и вызываем callback парсинга страницы постов для каждого тэга
        except AttributeError as e:
            for user in self.user_list:
                yield response.follow(f'{self.start_urls[0]}{user}',
                                      callback=self.user_page_parse
                                      )

    def user_page_parse(self, response):
        js_data = self.js_data_extract(response)
        insta_user_data = js_data["entry_data"]["ProfilePage"][0]["graphql"]["user"]
        insta_user = InstagramUser(insta_user_data)
        insta_user_item = GbInstagramUserItem()
        insta_user_item["user_id"] = insta_user.variables["id"]
        insta_user_item["user_name"] = insta_user.user_name
        insta_user_item["followers"] = {}
        insta_user_item["following"] = {}
        followers_cnt = int(insta_user_data["edge_followed_by"]["count"])
        following_cnt = int(insta_user_data["edge_follow"]["count"])
        yield response.follow(f"{self.api_url}?{urlencode(insta_user.first_followers_params())}",
                              callback=self._api_followers_parse,
                              cb_kwargs={"insta_user": insta_user,
                                         "insta_user_item": insta_user_item,
                                         "followers_cnt": followers_cnt,
                                         "following_cnt": following_cnt
                                         }
                              )
        yield response.follow(f"{self.api_url}?{urlencode(insta_user.first_following_params())}",
                              callback=self._api_following_parse,
                              cb_kwargs={"insta_user": insta_user,
                                         "insta_user_item": insta_user_item,
                                         "followers_cnt": followers_cnt,
                                         "following_cnt": following_cnt
                                         }
                              )

    def _api_followers_parse(self, response, **kwargs):
        data = response.json()
        edges = data["data"]["user"]["edge_followed_by"]["edges"]
        page_info = data["data"]["user"]["edge_followed_by"]["page_info"]
        udata = {}
        for u in edges:
            udata[u["node"]["id"]] = u["node"]["username"]
        kwargs["insta_user_item"]["followers"].update(udata)
        if page_info["has_next_page"]:
            url_query = kwargs['insta_user'].next_followers_params(page_info['end_cursor'])
            yield response.follow(f"{self.api_url}?{urlencode(url_query)}",
                                  callback=self._api_followers_parse,
                                  cb_kwargs={"insta_user": kwargs['insta_user'],
                                             "insta_user_item": kwargs["insta_user_item"],
                                             "followers_cnt": kwargs["followers_cnt"],
                                             "following_cnt": kwargs["following_cnt"]
                                             }
                                  )
        if len(kwargs["insta_user_item"]["followers"]) >= kwargs["followers_cnt"] and \
                len(kwargs["insta_user_item"]["following"]) >= kwargs["following_cnt"]:
            yield kwargs["insta_user_item"]

    #    yield insta_user_item

    def _api_following_parse(self, response, **kwargs):
        data = response.json()
        edges = data["data"]["user"]["edge_follow"]["edges"]
        page_info = data["data"]["user"]["edge_follow"]["page_info"]
        udata = {}
        for u in edges:
            udata[u["node"]["id"]] = u["node"]["username"]
        kwargs["insta_user_item"]["following"].update(udata)
        if page_info["has_next_page"]:
            url_query = kwargs['insta_user'].next_following_params(page_info['end_cursor'])
            yield response.follow(f"{self.api_url}?{urlencode(url_query)}",
                                  callback=self._api_following_parse,
                                  cb_kwargs={"insta_user": kwargs['insta_user'],
                                             "insta_user_item": kwargs["insta_user_item"],
                                             "followers_cnt": kwargs["followers_cnt"],
                                             "following_cnt": kwargs["following_cnt"]
                                             }
                                  )
        if len(kwargs["insta_user_item"]["followers"]) >= kwargs["followers_cnt"] and \
                len(kwargs["insta_user_item"]["following"]) >= kwargs["following_cnt"]:
            yield kwargs["insta_user_item"]


    def js_data_extract(self, response):
        script = response.xpath(
            "//script[contains(text(), 'window._sharedData = ')]/text()"
        ).extract_first()
        return json.loads(script.replace("window._sharedData = ", "")[:-1])




class InstagramUser:
    followers_query_hash = '5aefa9893005572d237da5068082d8d5'
    following_query_hash = '3dec7e2c57367ef3da3d987d89f9dbc8'

    def __init__(self, user_data: dict):
        self.variables = {
            "id": user_data["id"],
            "include_reel":True,
            "fetch_mutual": True,
            "first": 24
        }
        self.user_name = user_data["username"]

    def first_followers_params(self):
        url_query = {"query_hash": self.followers_query_hash, "variables": json.dumps(self.variables)}
        return url_query

    def next_followers_params(self, end_cursor):
        dt = self.variables.copy()
        dt["after"] = end_cursor
        url_query = {"query_hash": self.followers_query_hash, "variables": json.dumps(dt)}
        return url_query

    def first_following_params(self):
        url_query = {"query_hash": self.following_query_hash, "variables": json.dumps(self.variables)}
        return url_query

    def next_following_params(self, end_cursor):
        dt = self.variables.copy()
        dt["after"] = end_cursor
        url_query = {"query_hash": self.following_query_hash, "variables": json.dumps(dt)}
        return url_query