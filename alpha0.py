import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

# Базовый URL поиска на ЕИС
BASE_URL = "https://zakupki.gov.ru/epz/order/extendedsearch/results.html"

# Города и области, граничащие с Саратовской областью
NEARBY_REGIONS = [
    "Саратов", "Самара", "Пенза", "Волгоград", "Оренбург", "Ульяновск", "Челябинск", "Тамбов"
]

# Продукция
PRODUCTS = [
    "Бытовки", "Дачные домики", "Вагончики садовые", "Блок-контейнеры", "Мобильные офисы",
    "Модульные здания", "Посты охраны", "Проходные санитарные контейнеры", "Технические блоки",
    "Торговые павильоны", "Киоски", "Лаборатории"
]

# Создаем ключевые слова
KEYWORDS = [f"{product} в {city}" for product in PRODUCTS for city in NEARBY_REGIONS] + PRODUCTS

# Параметры поиска
SEARCH_PARAMS = {
    "morphology": "on",
    "search-filter": "Дате размещения",
    "pageNumber": 1,
    "sortDirection": "false",
    "recordsPerPage": "_10",
    "fz223": "on",  # 223-ФЗ
    "af": "on",  # Только актуальные
    "currencyIdGeneral": "-1",
}

# Заголовки для имитации реального пользователя
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def get_tenders(keyword):
    SEARCH_PARAMS["searchString"] = keyword
    response = requests.get(BASE_URL, params=SEARCH_PARAMS, headers=HEADERS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    tenders = []

    for item in soup.select(".search-registry-entry-block"):
        title = item.select_one(".registry-entry__header-mid__number a").text.strip()
        link = "https://zakupki.gov.ru" + item.select_one(".registry-entry__header-mid__number a")['href']
        price = item.select_one(".price-block__value").text.strip()
        customer = item.select_one(".registry-entry__body-href").text.strip()
        deadline = item.select_one(".data-block__value").text.strip()
        tenders.append([title, link, price, customer, deadline])

    return tenders


def filter_tenders_by_city(tenders, cities):
    filtered_tenders = []
    for tender in tenders:
        if any(city in tender[0] for city in cities):  # Проверяем, встречается ли город в названии тендера
            filtered_tenders.append(tender)
    return filtered_tenders


def save_to_excel(tenders, keyword):
    # Уникализируем имя файла по времени, чтобы избежать перезаписи
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"tenders_{keyword}_{timestamp}.xlsx"

    df = pd.DataFrame(tenders, columns=["Название", "Ссылка", "Цена", "Заказчик", "Сроки"])
    df.to_excel(filename, index=False)
    print(f"Данные для '{keyword}' сохранены в {filename}")


if __name__ == "__main__":
    for keyword in KEYWORDS:
        print(f"Получаем тендеры по ключевому слову: {keyword}...")
        try:
            tenders = get_tenders(keyword)
            if tenders:
                # Фильтруем тендеры по городам
                filtered_tenders = filter_tenders_by_city(tenders, NEARBY_REGIONS)
                if filtered_tenders:
                    save_to_excel(filtered_tenders, keyword)
                else:
                    print(f"По ключевому слову '{keyword}' ничего не найдено.")
            else:
                print(f"По ключевому слову '{keyword}' ничего не найдено.")
        except requests.exceptions.HTTPError as e:
            print(f"Ошибка HTTP: {e}")
        except PermissionError as e:
            print(f"Ошибка записи файла: {e}. Проверьте, не открыт ли файл.")
