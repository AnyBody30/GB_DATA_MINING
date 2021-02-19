
import time
import json
from pathlib import Path
import requests


class Parse5ka:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0"}

    def __init__(self, start_url: str, save_path: Path):
        self.start_url = start_url
        self.save_path = save_path

    def _get_response(self, url):
        while True:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response
            time.sleep(0.5)

    def run(self):
        for product in self._parse(self.start_url):
            product_path = self.save_path.joinpath(f"{product['id']}.json")
            self._save(product, product_path)

    def _parse(self, url: str):
        while url:
            response = self._get_response(url)
            data: dict = response.json()
            url = data['next']
            for product in data["results"]:
                yield product

    def _save(self, data: dict, file_path: Path):
        file_path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')


class CatParse5ka(Parse5ka):

    def __init__(self, cat_url: str, product_url: str, save_path: Path):
        self.cat_url = cat_url
        super().__init__(product_url, save_path)

    def _cat_parse(self):
        response = self._get_response(self.cat_url)
        data = response.json()
        return data

    def run(self):
        for category in self._cat_parse():
            cat_struct = {'name': category["parent_group_name"],
                          'code': category["parent_group_code"],
                          'products': []
                          }
            url = f'{self.start_url}?categories={cat_struct["code"]}'
            for product in self._parse(url):
                cat_struct['products'].append(product)
            c_path = self.save_path.joinpath(f"{cat_struct['name']}_{cat_struct['code']}.json")
            self._save(cat_struct, c_path)
            cat_struct.clear()




if __name__ == '__main__':
    p_url = 'https://5ka.ru/api/v2/special_offers/'
    c_url = 'https://5ka.ru/api/v2/categories/'
    save_path = Path(__file__).parent.joinpath('categories')
    if not save_path.exists():
        save_path.mkdir()
    c_parser = CatParse5ka(c_url, p_url, save_path)
    c_parser.run()

