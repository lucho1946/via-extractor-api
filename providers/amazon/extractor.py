# ==========================================================
# EXTRACTOR AMAZON V2 (ROBUSTO - PRODUCCIÓN)
# ==========================================================

import os
import re
import time
import random
import requests
from bs4 import BeautifulSoup

from core.logger_config import logger


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

# 🔥 CORRECCIÓN CLAVE
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY")

SCRAPER_URL = "http://api.scraperapi.com"

HEADERS_LIST = [
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X) Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Firefox/115.0"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/121.0 Safari/537.36"},
]


# ==========================================================
# UTILIDADES
# ==========================================================

def clean_text(text):
    if not text:
        return None

    text = re.sub('<.*?>', '', text)
    text = text.replace("\n", " ")
    text = text.replace("\t", " ")
    return text.strip()


def get_text_safe(soup, selector):
    el = soup.select_one(selector)
    return el.get_text(strip=True) if el else None


def is_blocked(html):
    if not html:
        return True

    html_lower = html.lower()

    return (
        "captcha" in html_lower or
        "robot check" in html_lower or
        len(html) < 5000
    )


def is_valid_data(data):
    return data.get("title_raw") is not None


# ==========================================================
# SCRAPERAPI
# ==========================================================

def fetch_with_scraperapi(url, render=True):

    # 🔥 VALIDACIÓN SEGURA
    if not SCRAPER_API_KEY:
        raise RuntimeError("SCRAPER_API_KEY no configurada")

    for intento in range(3):

        try:
            headers = random.choice(HEADERS_LIST)

            response = requests.get(
                SCRAPER_URL,
                params={
                    "api_key": SCRAPER_API_KEY,
                    "url": url,
                    "render": "true" if render else "false",
                    "country_code": "us"
                },
                headers=headers,
                timeout=30
            )

            logger.info(f"Intento {intento+1} → Status: {response.status_code}")

            if response.status_code == 200:
                html = response.text

                if not is_blocked(html):
                    return html

                logger.warning("HTML bloqueado o incompleto detectado")

        except Exception as e:
            logger.warning(f"Error intento {intento+1}: {e}")

        time.sleep(2 ** intento)

    return None


# ==========================================================
# PARSEO
# ==========================================================

def parse_amazon_html(html, url):

    soup = BeautifulSoup(html, "html.parser")

    title = get_text_safe(soup, "#productTitle")

    brand = get_text_safe(soup, "#bylineInfo")

    if brand:
        brand = brand.replace("Marca:", "").replace("Visit the", "")
        brand = brand.replace("Store", "").strip()

    price_whole = get_text_safe(soup, ".a-price-whole")
    price_fraction = get_text_safe(soup, ".a-price-fraction")

    price_value = None
    currency = None

    if price_whole:
        try:
            price_str = price_whole.replace(",", "")
            if price_fraction:
                price_str += "." + price_fraction

            price_value = float(price_str)
            currency = "USD"
        except:
            pass

    bullets = []

    bullet_elements = soup.select("#feature-bullets .a-list-item")

    for el in bullet_elements:
        text = el.get_text(strip=True)
        if text and len(text) > 10:
            bullets.append(text)

    technical_details = {}

    rows = soup.select("table tr")

    for row in rows:
        th = row.find("th")
        td = row.find("td")

        if th and td:
            key = clean_text(th.get_text())
            value = clean_text(td.get_text())

            if key and value:
                technical_details[key] = value

    referencia = None

    for key, value in technical_details.items():
        key_lower = key.lower()

        if "model" in key_lower or "modelo" in key_lower:
            referencia = value
            break

    if not referencia:
        asin_match = re.search(r"/dp/([A-Z0-9]{10})", url)
        referencia = asin_match.group(1) if asin_match else None

    if not title:
        return None

    return {
        "title_raw": title,
        "reference_raw": referencia,
        "brand_raw": brand,
        "price_text": None,
        "price_value": price_value,
        "currency": currency,
        "technical_details": technical_details,
        "bullets": bullets,
        "product_description": "",
        "product_information": {},
        "aplus_content": "",
        "url_origen": url
    }


# ==========================================================
# FUNCIÓN PRINCIPAL
# ==========================================================

def extract_product(url: str):

    logger.info("Iniciando extracción Amazon")

    html = fetch_with_scraperapi(url, render=True)

    if html:
        data = parse_amazon_html(html, url)

        if is_valid_data(data):
            logger.info("Estrategia render exitosa")
            return data

    html = fetch_with_scraperapi(url, render=False)

    if html:
        data = parse_amazon_html(html, url)

        if is_valid_data(data):
            logger.info("Estrategia sin render exitosa")
            return data

    logger.error("No se pudo extraer el producto")

    return {
        "title_raw": None,
        "reference_raw": None,
        "brand_raw": None,
        "price_text": None,
        "price_value": None,
        "currency": None,
        "technical_details": {},
        "bullets": [],
        "product_description": "",
        "product_information": {},
        "aplus_content": "",
        "url_origen": url,
        "error": "Extracción fallida"
    }