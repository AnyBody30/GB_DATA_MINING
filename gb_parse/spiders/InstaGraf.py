import scrapy
import json
from ..items import GbInstaGrafItem
from urllib.parse import urlencode
from ..loaders import GrafLoader


class InstagrafSpider(scrapy.Spider):
    name = 'InstaGraf'
    allowed_domains = ['www.instagram.com']
    start_urls = ['http://www.instagram.com/']
    api_url = "/graphql/query/"
    login_url = 'https://www.instagram.com/accounts/login/ajax/'


    def __init__(self, login, password, user_list, *args, **kwargs):
        self.login = login
        self.password = password
        self.user_list = user_list
        self.start_user_id = ''

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
            yield response.follow(f'{self.start_urls[0]}{self.user_list[0]}',
                                  callback=self.user_page_parse
                                  )

    def user_page_parse(self, response, **kwargs):
        js_data = self.js_data_extract(response)
        insta_user_data = js_data["entry_data"]["ProfilePage"][0]["graphql"]["user"]
        insta_user = InstagramUser(insta_user_data)
        # надо сохранить id стартового юзера - потом обход будет по user_id, а не user_name
        if insta_user.user_name == self.user_list[0]:
            self.start_user_id = insta_user_data["id"]
        yield response.follow(f"{self.api_url}?{urlencode(insta_user.first_following_params())}",
                              callback=self._api_following_parse,
                              cb_kwargs={"insta_user": insta_user,
                                         "start_user_id": self.start_user_id
                                         }
                              )
        yield response.follow(f"{self.api_url}?{urlencode(insta_user.first_followers_params())}",
                              callback=self._api_followers_parse,
                              cb_kwargs={"insta_user": insta_user,
                                         "start_user_id": self.start_user_id
                                         }
                              )



    def _api_followers_parse(self, response, **kwargs):
        data = response.json()
        edges = data["data"]["user"]["edge_followed_by"]["edges"]
        page_info = data["data"]["user"]["edge_followed_by"]["page_info"]
        # идем по фолловерам первой страницы
        for u in edges:
            container = {"user_name": kwargs["insta_user"].user_name,
                         "user_id": kwargs["insta_user"].variables["id"],
                         "list_user": self.user_list,
                         "start_user_id": kwargs["start_user_id"],
                         "follower": {"user_id": u["node"]["id"],
                                      "user_name": u["node"]["username"]
                                      }
                        }
            loader = GrafLoader(response=response)
            loader.add_value("container", container)
            yield loader.load_item()
            #идем на разбор фолловера
            yield response.follow(f'{self.start_urls[0]}{container["follower"]["user_name"]}',
                                      callback=self.user_page_parse
                                      )
            # если еще есть страница фолловеров идем запрашивать следующих фолловеров
        if page_info["has_next_page"]:
            url_query = kwargs['insta_user'].next_followers_params(page_info['end_cursor'])
            yield response.follow(f"{self.api_url}?{urlencode(url_query)}",
                                      callback=self._api_followers_parse,
                                      cb_kwargs=kwargs
                                      )


    def _api_following_parse(self, response, **kwargs):
        data = response.json()
        edges = data["data"]["user"]["edge_follow"]["edges"]
        page_info = data["data"]["user"]["edge_follow"]["page_info"]
        # идем по фолловингам первой страницы
        for u in edges:
            container = {"user_name": kwargs["insta_user"].user_name,
                         "user_id": kwargs["insta_user"].variables["id"],
                         "list_user": self.user_list,
                         "start_user_id": kwargs["start_user_id"],
                         "following": {"user_id": u["node"]["id"],
                                      "user_name": u["node"]["username"]
                                      }
                        }
            loader = GrafLoader(response=response)
            loader.add_value("container", container)
            yield loader.load_item()
            # идем на разбор фолловинга
            yield response.follow(f'{self.start_urls[0]}{container["following"]["user_name"]}',
                                      callback=self.user_page_parse
                                      )
        # если еще есть страница фолловингов идем запрашивать следующих фолловингов
        if page_info["has_next_page"]:
            url_query = kwargs['insta_user'].next_following_params(page_info['end_cursor'])
            yield response.follow(f"{self.api_url}?{urlencode(url_query)}",
                                      callback=self._api_following_parse,
                                      cb_kwargs=kwargs
                                      )

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