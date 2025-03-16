import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# Базовый URL поиска на ЕИС
BASE_URL = "https://zakupki.gov.ru/epz/order/extendedsearch/results.html"

# Список ключевых слов для поиска
PRODUCTS = [
    "Модульные здания", "Контейнеры", "Жилые вагончики", "Торговые павильоны",
    "Мобильные офисы", "Бытовки"
]


# Список городов и регионов для фильтрации
REGIONS = [
    "Саратов", "Самара", "Пенза", "Энгельс", "Балаково", "Вольск", "Маркс", "Волгоград", "Москва"
]

# Параметры поиска (будем изменять ключевое слово для каждого поиска)
SEARCH_PARAMS = {
    "searchString": "",  # Пустое, будем менять на ключевое слово
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

    for item in soup.select(".search-registry-entry-block"):  # Класс элементов тендеров (пример)
        title = item.select_one(".registry-entry__header-mid__number a").text.strip()
        link = "https://zakupki.gov.ru" + item.select_one(".registry-entry__header-mid__number a")['href']
        price = item.select_one(".price-block__value").text.strip()
        customer = item.select_one(".registry-entry__body-href").text.strip()
        deadline = item.select_one(".data-block__value").text.strip()
        tenders.append([title, link, price, customer, deadline])

    return tenders


def filter_by_region(tenders, regions):
    filtered_tenders = []
    for tender in tenders:
        for region in regions:
            if region.lower() in tender[1].lower():  # Если название региона найдено в ссылке тендера
                filtered_tenders.append(tender)
                break
    return filtered_tenders


def save_to_excel(tenders, keyword):
    if tenders:
        filename = f"tenders_{keyword}.xlsx"
        df = pd.DataFrame(tenders, columns=["Название", "Ссылка", "Цена", "Заказчик", "Сроки"])
        df.to_excel(filename, index=False)
        print(f"Данные сохранены в {filename}")
    else:
        print(f"По ключевому слову '{keyword}' не найдено тендеров.")


if __name__ == "__main__":
    for keyword in PRODUCTS:
        print(f"Получаем тендеры по ключевому слову: {keyword}...")
        try:
            tenders = get_tenders(keyword)
            if tenders:
                filtered_tenders = filter_by_region(tenders, REGIONS)
                save_to_excel(filtered_tenders, keyword)
            else:
                print(f"По ключевому слову '{keyword}' ничего не найдено.")
        except requests.exceptions.HTTPError as e:
            print(f"Ошибка HTTP: {e}")
