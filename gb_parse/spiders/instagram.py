import scrapy
import json
from ..loaders import InstagramLoader
from ..items import GbInstagramItem, GbTagItem, GbTagPostsCollection, GbtagPost
import datetime as dt
from urllib.parse import urlencode

class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['www.instagram.com']
    start_urls = ['https://www.instagram.com/']
    login_url = 'https://www.instagram.com/accounts/login/ajax/'
    tags_path = '/explore/tags/'
    api_url = "/graphql/query/"


    def __init__(self, login, password, tags, *args, **kwargs):
        self.login = login
        self.password = password
        self.tags = tags


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
            for tag_name in self.tags:
                yield response.follow(f'{self.tags_path}{tag_name}/',
                                      callback=self.tag_posts_collection_page_parse
                                      )

    def tag_posts_collection_page_parse(self, response):
        data = self.js_data_extract(response)
        hashtag = data['entry_data']['TagPage'][0]['graphql']['hashtag']
        edges_data = data['entry_data']['TagPage'][0]['graphql']['hashtag']['edge_hashtag_to_top_posts']['edges']
        tag_name = data['entry_data']['TagPage'][0]['graphql']['hashtag']['name']
        # отдаем структуру, описывающую tag
        yield self.get_tag_item(data)
        # отдаем генератор структур постов
        yield from self.get_posts_collection_items(edges_data, tag_name)
        # идем по постам и генерируем задачи парсинга постов
        for post in edges_data:
            shortcode = post["node"]["shortcode"]
            yield response.follow(f'{self.start_urls[0]}p/{shortcode}/',
                                  callback=self.post_page_parse,
                                  cb_kwargs={'shortcode': shortcode}
                                  )
        # идем в API пагинации и генерируем задачу пагинации, задача отличается от первоначальной страницы
        # т.к. API пагинации отдает чистый json
        yield response.follow(
            f"{self.api_url}?{self.get_pagination_param(hashtag)}",
            callback=self.api_page_parse
        )

    def api_page_parse(self, response):
        pag_data = response.json()
        hashtag = pag_data['data']['hashtag']
        edges_data = pag_data['data']['hashtag']['edge_hashtag_to_top_posts']['edges']
        tag_name = pag_data['data']['hashtag']['name']
        # отдаем генератор items постов из полученной json структуры пагинации
        yield from self.get_posts_collection_items(edges_data, tag_name)
        # идем по постам и генерируем задачи парсинга постов
        for post in edges_data:
            shortcode = post["node"]["shortcode"]
            yield response.follow(f'{self.start_urls[0]}p/{shortcode}/',
                                  callback=self.post_page_parse,
                                  cb_kwargs={'shortcode': shortcode}
                                  )
        # идем парсить следующую пагинацию если есть следующая
        if hashtag:
            yield response.follow(
                f"{self.api_url}?{self.get_pagination_param(hashtag)}",
                callback=self.api_page_parse
            )

    def post_page_parse(self, response, **kwargs):
        post_data = self.js_data_extract_post(response, kwargs['shortcode'])
        yield self.get_post_item(post_data)




    def get_tag_item(self, tag_posts_collection_data):
        item = GbTagItem()
        tag_data = tag_posts_collection_data['entry_data']['TagPage'][0]['graphql']['hashtag']
        item["date_parse"] = dt.datetime.utcnow()
        item["tag_name"] = tag_data["name"]
        data = {}
        for key, value in tag_data.items():
            if not (isinstance(value, dict) or isinstance(value, list)):
                data[key] = value
        item["images"] = [tag_data["profile_pic_url"]]
        item["data"] = data
        return item

    def get_posts_collection_items(self, edges_data, tag_name):
        for post in edges_data:
            item = GbTagPostsCollection()
            item["date_parse"] = dt.datetime.utcnow()
            item["tag_name"] = tag_name
            item["images"] = [post["node"]["display_url"]]
            item["data"] = post["node"]
            yield item


    def get_post_item(self, post_data):
        item = GbtagPost()
        item["date_parse"] = dt.datetime.utcnow()
        images = []
        try:
            for image in post_data['graphql']['shortcode_media']['edge_sidecar_to_children']['edges']:
                images.append(image['node']['display_url'])
        except KeyError:
            images.append(post_data['graphql']['shortcode_media']['display_url'])
        item["images"] = images
        item["data"] = post_data['graphql']['shortcode_media']
        return item


    def js_data_extract(self, response):
        script = response.xpath("//script[contains(text(), 'window._sharedData =')]/text()").extract_first()
        return json.loads(script.replace('window._sharedData = ', '')[:-1])

    def js_data_extract_post(self, response, shortcode):
        script = response.xpath("//script[contains(text(), 'window.__additionalDataLoaded(')]/text()").extract_first()
        return json.loads(script.replace(f"window.__additionalDataLoaded(\'/p/{shortcode}/\',", '')[:-2])

    def get_pagination_param(self, hashtag):
        query_hash = "9b498c08113f1e09617a1703c22b2f32"
        variables = {
            "tag_name": hashtag["name"],
            "first": 3,
            "after": hashtag["edge_hashtag_to_media"]["page_info"]["end_cursor"]
        }
        url_query = urlencode({"query_hash": query_hash, "variables": json.dumps(variables)})
        return url_query