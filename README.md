# Парсер каталога Золотого Яблока 
Программа собирает информацию о всех товарах из каталога и сохраняет в jsonl, например:  
{"id": "12345", "name": "Товар", "brand": "Бренд", "type": "Тушь для ресниц", "photos": ["https://example.com/photo1.jpg"], "in_stock": true, "price": 2299}


## Запуск

Клонируем репозиторий 
```
https://github.com/Petro2561/GoldenAppleParser.git
```
Создаем виртуальное окружение, активируем его и устанавливаем зависимости:
 ```
 pip install -r requirements.txt
```
Запускаем парсер командой:
```
python main.py 
```

## Алгоритм работы программы

1. Отфильтровываем работающие прокси. Прокси брал с сайта https://best-proxies.ru/
2. Делаем запросы к каждой из основных категорий, список категорий в файле settings.py  
Обращаемся к эндпоинту https://goldapple.ru/front/api/catalog/products?categoryId=&cityId=&pageNumber=&z=
3. Продукты могут дублироваться, поэтому в файл сохраняются только товары с оригинальным ID
4. В случае возникновения ошибки 429 делаем повторный запрос с новым прокси
5. В случае возникновения ошибки 403 удаляем прокси из списка
6. Результат сохраняется в файле products.jsonl  


Примерное время работы около 5 минут. Чем больше прокси, тем быстрее результат.  
Результат парсинга можно посмотреть в файле products_example.jsonl.    
Логи после запуска можно посмотреть в файле parser.log.  

## Tecnhologies:
- aiofiles
- aiohttp
