from urllib.parse import urljoin
import requests
import bs4
import pymongo
import time
from datetime import date


class MagnitParse:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0"}

    def __init__(self, start_url, db_client):
        self.start_url = start_url
        self.db = db_client["lesson_2_db"]
        self.collection = self.db["lesson_2_collection"]

    def _get_response(self, url):
        while True:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response
            time.sleep(0.5)
        return response

    def _get_soup(self, url):
        response = self._get_response(url)
        return bs4.BeautifulSoup(response.text, "lxml")

    def run(self):
        soup = self._get_soup(self.start_url)
        catalog = soup.find("div", attrs={"class": "сatalogue__main"})
        for prod_a in catalog.find_all("a", recursive=False):
            product_data = self._parse(prod_a)
            self._save(product_data)


    def _parse_price(self, *a):
        # первом аргументе продукт, во втором часть названия аттрибута class по которой определяем новую и старую цену
        # контроль исключения для отлавливания отсутствия цены, если цены нет, то пустая строка
        try:
            price_int_str = a[0].find("div", attrs={"class": f"label__price label__{a[1]}"}).\
                            find("span", attrs={"class": "label__price-integer"}).get_text()
        except AttributeError:
            price_int_str = ''

        try:
            price_dec_str = a[0].find("div", attrs={"class": f"label__price label__{a[1]}"}).\
                            find("span", attrs={"class": "label__price-decimal"}).get_text()
        except AttributeError:
            price_dec_str = ''
        # для случая когда в цене не абсолютная цена, а относительная скидка
        if not (price_int_str.isdigit() and price_dec_str.isdigit()):
            return f'{price_int_str}{price_dec_str}'

        return int(price_int_str) + int(price_dec_str) / 100


    def _parse_date(self, *a):
        # словарь для определения номера месяца из имени месяца в родительном падеже
        month = {'января': 1,
                 'февраля': 2,
                 'марта': 3,
                 'апреля': 4,
                 'мая': 5,
                 'июня': 6,
                 'июля': 7,
                 'августа': 8,
                 'сентября': 9,
                 'октября': 10,
                 'ноября': 11,
                 'декабря': 12
                 }
        # выбираем супы с датами
        dates = a[0].find("div", attrs={"class": "card-sale__date"}).find_all("p")
        # разбиваем тексты с датой из супов по пробелам в списки
        dates_p = list(map(lambda d: d.get_text().split(' '), dates))
        # для случаев когда две даты
        if len(dates_p) == 2:
            # по переданному ключу определяем это дата старта или окончания
            if a[1] == "date_from":
                return date(2021, month[dates_p[0][2]], int(dates_p[0][1])).isoformat()
            else:
                return date(2021, month[dates_p[1][2]], int(dates_p[1][1])).isoformat()
        # для случая когда дата одна, это будет и дата старта и окончания
        else:
            return date(2021, month[dates_p[0][2]], int(dates_p[0][1])).isoformat()


    def get_template(self):
        return {
            "url": lambda *a: urljoin(self.start_url, a[0].attrs.get("href", "")),
            "promo_name": lambda *a: a[0].find("div", attrs={"class": "card-sale__header"}).get_text(),
            "product_name": lambda *a: a[0].find("div", attrs={"class": "card-sale__title"}).get_text(),
            "price_old": self._parse_price,
            "price_new": self._parse_price,
            "image_url": lambda *a: urljoin(self.start_url, a[0].find("img").attrs.get("data-src", "")),
            "date_from": self._parse_date,
            "date_to": self._parse_date
        }

    def _parse(self, product_a) -> dict:
        data = {}
        for key, funk in self.get_template().items():
            try:
                data[key] = funk(product_a, key)
            except AttributeError:
                pass
        return data

    def _save(self, data: dict):
        self.collection.insert_one(data)




if __name__ == "__main__":
    url = "https://magnit.ru/promo/?geo=moskva"
    db_client = pymongo.MongoClient("mongodb://localhost:27017")
    parser = MagnitParse(url, db_client)
    parser.run()