import asyncio
import logging

from product_parser import ProductParser
from settings import BASE_URL, CATEGORIES, HEADERS, PROXIES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("parser.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def main():
    parser = ProductParser(
        proxies=PROXIES,
        output_file="products.jsonl",
        base_url=BASE_URL,
        headers=HEADERS,
    )
    # asyncio.run(parser.filter_working_proxies())
    asyncio.run(parser.run([category for category in CATEGORIES]))


if __name__ == "__main__":
    main()
