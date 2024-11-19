import asyncio
import json
import logging
import random

import aiohttp

logger = logging.getLogger(__name__)


class ProductParser:
    def __init__(self, proxies, output_file, base_url, headers):
        self.proxies = proxies
        self.output_file = output_file
        self.base_url = base_url
        self.headers = headers
        self.saved_ids = set()

    async def run(self, categories):
        """
        Фильтруем прокси, открываем jsonl, запускаем сбор данных
        """
        await self.filter_working_proxies()

        with open(self.output_file, "w", encoding="utf-8") as f:
            pass

        async with aiohttp.ClientSession(headers=self.headers) as session:
            tasks = [
                self.process_category(
                    session=session,
                    category_id=category_id,
                    category_name=category_name,
                )
                for category_id, category_name in categories
            ]
            await asyncio.gather(*tasks)

    def get_next_proxy(self):
        """Случайный выбор прокси"""
        if len(self.proxies) == 0:
            logger.error(
                "Нет доступных прокси для выполнения запроса. Завершаем работу."
            )
            raise RuntimeError("Нет доступных прокси.")
        proxy = random.choice(self.proxies)
        return proxy

    async def fetch_products(
        self,
        session,
        category_id,
        category_name,
        city_id="0c5b2444-70a0-4932-980c-b4dc0d3f02b5",
        page_number=1,
    ):
        """
        Выполняет запрос к API для получения данных о продуктах и обрабатываем ошибки.
        """
        try:
            proxy = self.get_next_proxy()
        except RuntimeError:
            logger.error(
                f"Завершаем выполнение для категории '{category_name}' из-за отсутствия прокси."
            )
            return None

        params = {
            "categoryId": category_id,
            "cityId": city_id,
            "pageNumber": page_number,
            "z": "16-46",
        }

        logger.info(
            f"Запрос: категория {params.get('categoryId')}, страница {params.get('pageNumber')}, прокси {proxy}"
        )
        try:
            async with session.get(
                self.base_url, params=params, proxy=proxy
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    logger.warning(
                        "Ошибка 429: Слишком много запросов. Повтор запроса."
                    )
                    return await self.fetch_products(
                        session=session,
                        category_id=category_id,
                        category_name=category_name,
                        city_id=city_id,
                        page_number=page_number,
                    )
                elif response.status == 403:
                    logger.error(
                        f"Ошибка 403: доступ запрещён для прокси {proxy}. Удаляем прокси."
                    )
                    self.proxies.remove(proxy)
                    return await self.fetch_products(
                        session=session,
                        category_id=category_id,
                        category_name=category_name,
                        city_id=city_id,
                        page_number=page_number,
                    )
                else:
                    logger.error(
                        f"Ошибка {response.status} для страницы {page_number} категории {category_id}"
                    )
                    return await self.fetch_products(
                        session=session,
                        category_id=category_id,
                        category_name=category_name,
                        city_id=city_id,
                        page_number=page_number,
                    )
        except aiohttp.ClientConnectionError as e:
            logger.error(
                f"Ошибка соединения: категория {category_name}, страница {page_number}. Прокси: {proxy}. Ошибка: {e}"
            )
            return await self.fetch_products(
                session=session,
                category_id=category_id,
                category_name=category_name,
                city_id=city_id,
                page_number=page_number,
            )

        except asyncio.TimeoutError:
            logger.error(
                f"Таймаут: категория {category_name}, страница {page_number}. Прокси: {proxy} Ошибка: {e}"
            )
            return await self.fetch_products(
                session=session,
                category_id=category_id,
                category_name=category_name,
                city_id=city_id,
                page_number=page_number,
            )
        except Exception as e:
            logger.error(
                f"Непредвиденная ошибка для категории {category_name}, Прокси: {proxy}, страницы {page_number}: {e}"
            )
            return await self.fetch_products(
                session=session,
                category_id=category_id,
                category_name=category_name,
                city_id=city_id,
                page_number=page_number,
            )
        return None

    async def is_proxy_working(self, proxy, max_retries=5):
        """
        Проверяет, работает ли указанный прокси, с 5 попытками подключения.
        """
        city_id = "0c5b2444-70a0-4932-980c-b4dc0d3f02b5"
        params = {
            "categoryId": 1000000003,
            "cityId": city_id,
            "pageNumber": 1,
            "z": "16-46",
        }
        for attempt in range(1, max_retries + 1):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        self.base_url, params=params, proxy=proxy, timeout=5
                    ) as response:
                        if response.status == 200:
                            logger.info(
                                f"Прокси {proxy} работает (попытка {attempt}/{max_retries})."
                            )
                            return True
            except Exception as e:
                logger.info(
                    f"Попытка {attempt}/{max_retries}: Прокси {proxy} недоступен: {e}"
                )
        return False

    async def filter_working_proxies(self):
        """
        Оставляет только работающие прокси в списке.
        """
        tasks = [self.is_proxy_working(proxy) for proxy in self.proxies]
        results = await asyncio.gather(*tasks)
        self.proxies = [
            proxy
            for proxy, is_working in zip(self.proxies, results)
            if is_working
        ]
        logger.info(f"Рабочие прокси: {self.proxies}")

    @staticmethod
    def parse_product(product):
        """
        Извлекает данные о продукте в нужном формате.
        """
        return {
            "id": product.get("itemId"),
            "name": product.get("name"),
            "brand": product.get("brand"),
            "type": product.get("productType"),
            "photos": [
                img["url"].replace("${screen}.${format}", "fullhd.jpg")
                for img in product.get("imageUrls", [])
            ],
            "in_stock": product.get("inStock", False),
            "price": (
                product["price"]["actual"]["amount"]
                if "price" in product and "actual" in product["price"]
                else None
            ),
        }

    async def save_to_jsonl(self, data):
        """
        Сохраняет данные в формате JSON Lines, исключая дубликаты по ID.
        """
        with open(self.output_file, "a", encoding="utf-8") as f:
            for item in data:
                item_id = item["id"]
                if item_id not in self.saved_ids:
                    self.saved_ids.add(item_id)
                    json_line = json.dumps(item, ensure_ascii=False)
                    f.write(json_line + "\n")
                else:
                    logger.info(f"Пропущен дубликат ID: {item_id}")

    async def process_category(self, session, category_id, category_name):
        """
        Обрабатывает одну категорию: собирает все товары и сохраняет в файл.
        """
        page_number = 1
        while True:
            data = await self.fetch_products(
                session=session,
                category_id=category_id,
                category_name=category_name,
                page_number=page_number,
            )
            if (
                not data
                or "products" not in data["data"]
                or not data["data"]["products"]
            ):
                logger.info(f"Категория '{category_name}' завершена.")
                break
            products = [
                self.parse_product(product)
                for product in data["data"]["products"]
            ]
            await self.save_to_jsonl(products)
            logger.info(
                f"Категория '{category_name}', страница {page_number} обработана."
            )
            page_number += 1
