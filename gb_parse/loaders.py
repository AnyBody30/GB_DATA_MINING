from scrapy.loader import ItemLoader
from scrapy import Selector
from itemloaders.processors import TakeFirst, MapCompose, Join
from .items import GbAutoYoulaItem, GbHhItem, GbInstagramItem, GbInstaGrafItem
import datetime
import sys

class Neighbors():
    def __init__(self):
        self.follower = set()
        self.following = set()

    def add_follower(self, follower):
        self.follower.add(follower)

    def add_following(self, following):
        self.following.add(following)

    def __str__(self):
        return str(self.follower & self.following)

# инициализируем граф, который будет дополняться при каждой попытке load(item) через препроцессинг MapCompose
# т.к. scrapy однопоточный, то считаем, что в единицу времени не будет попыток конкурентного доступа разными задачами
# по поиску и вставке в словарь. Структура словаря:{user_id: [username, [followers], [followings]]} в качестве ключа
# используем user_id т.к. в user_name допускаются литеры, недопускаемые в ключах словарей
graf = {}

# функция, вызываемая MapCompose
def graf_process(Item):
    # если такого юзера еще нет в графе, то добавлем его
    if not Item["user_id"] in graf:
        graf[Item["user_id"]] = [Item["user_name"], [], []]
    # если пришел follower, то дополняем список followers (уславливаемся, что элемент 1 списка это followers)
    # для этого юзера в графе
    if Item.get("follower", False):
        graf[Item["user_id"]][1].append(Item["follower"].copy())
    else:
        # иначе считаем, что пришел following (уславливаемся, что элемент 2 списка это followings)
        # и дополняем список followings для этого юзера в графе
        graf[Item["user_id"]][2].append(Item["following"].copy())
    # после обновления графа делаем его обход ширину для поиска целевого пользователя
    # очередь обхода
    print('Граф: ')
    for key, data in graf.items():
        print(f'User: {key} {data[0]}; Followers cnty: {len(data[1])}; Followings cnty: {len(data[2])}; \
        Neighbors: {len([n for n in data[1] if n["user_id"] in [nn["user_id"] for nn in data[2]]])}.')
    queue = [Item["start_user_id"]]
    # список посещенных
    visited = [Item["start_user_id"]]
    # словарь предков для восстановления пути
    parents = {Item["start_user_id"]: ''}
    while queue:
        # берем очередного для посещения
        v = queue.pop(0)
        # если в графе еще нет информации о этом юзере, т.е. еще не распарсили ничего и не добавили в граф
        # то считаем, что у него нет рукопожатных соседей
        if not graf.get(v, False):
            neighbors = []
        # иначе для вычисления рукопожатных генерируем пересечение followed и following
        else:
            neighbors = [n for n in graf[v][1] if n["user_id"] in [nn["user_id"] for nn in graf[v][2]]]
        # идем по взаимноподписанным, рукопожатным юзерам-соседям
        for neighbor in neighbors:
            # если еще не были по графу у этого юзера
            if not neighbor["user_id"] in visited:
                # добавляем в очередь обхода
                queue.append(neighbor["user_id"])
                # добавляем в список посещённых
                visited.append(neighbor["user_id"])
                # отмечаем от какого юзера пришли к этому
                parents[neighbor["user_id"]] = v
                # если этот neighbor целевой пользователь, то печатаем путь и завершаем программу
                if neighbor["user_name"] == Item["list_user"][1]:
                    print('Нашли цепочку рукопожатий:')
                    print(neighbor)
                    parent = parents[neighbor["user_id"]]
                    while parent:
                        print(graf[parent])
                        parent = parents[parent]
                    sys.exit()

    return Item





def get_characteristics(item):
    selector = Selector(text=item)
    data = {
        "name": selector.xpath(
            "//div[contains(@class, 'AdvertSpecs_label')]/text()"
        ).extract_first(),
        "value": selector.xpath(
            "//div[contains(@class, 'AdvertSpecs_data')]//text()"
        ).extract_first(),
    }
    return data

def get_price(item):
    selector = Selector(text=item)
    return float(selector.xpath("//div[@data-target='advert-price']/text()").get().replace("\u2009", ""))

def get_employer(item):
    return f'https://hh.ru{item}'

def get_field(item):
    return item.split(', ')

def get_datestr(item):
    return datetime.date.fromtimestamp(item).isoformat()

class AutoyoulaLoader(ItemLoader):
    default_item_class = dict
    url_out = TakeFirst()
    title_out = TakeFirst()
    author_out = TakeFirst()
    descriptions_out = TakeFirst()
    phone_out = TakeFirst()
    characteristics_in = MapCompose(get_characteristics)
    price_in = MapCompose(get_price)
    price_out = TakeFirst()

class HhLoader(ItemLoader):
    default_item_class = dict
    url_out = TakeFirst()
    title_out = TakeFirst()
    salary_out = Join()
    description_out = Join()
    employer_in = MapCompose(get_employer)
    employer_out = TakeFirst()
    title_employer_out = TakeFirst()
    site_employer_out = TakeFirst()
    field_employer_in = MapCompose(get_field)
    description_employer_out = Join()

class GrafLoader(ItemLoader):
    default_item_class = dict
    container_in = MapCompose(graf_process)



