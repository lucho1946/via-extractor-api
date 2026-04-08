import re
from normalizer.spec_normalizer import normalize_technical_specs, normalize_bullets


# ==========================================================
# NORMALIZADOR UNIVERSAL TEXTO AMAZON
# elimina caracteres invisibles
# ==========================================================
def normalize_amazon_text(text):

    if not text:
        return text

    text = str(text)

    text = text.replace("‎", "")
    text = text.replace("\u200e", "")
    text = text.replace("\u200f", "")

    text = text.strip()

    return text


# ==========================================================
# LIMPIAR TEXTO GENERAL
# ==========================================================
def clean_text(value):

    if not value:
        return value

    value = normalize_amazon_text(value)

    value = re.sub(r"\s+", " ", value)

    return value


# ==========================================================
# LIMPIAR MARCA
# ==========================================================
def clean_brand(brand):

    if not brand:
        return None

    brand = normalize_amazon_text(brand)

    brand = brand.replace("Marca:", "")
    brand = brand.replace("Brand:", "")
    brand = brand.replace("Visita la tienda de", "")
    brand = brand.replace("Visit the", "")
    brand = brand.replace("Store", "")

    return brand.strip()


# ==========================================================
# PARSEAR PRECIO
# ==========================================================
def parse_price(price_text):

    if not price_text:
        return None, None

    price_text = normalize_amazon_text(price_text)

    price_text = price_text.replace(",", "")

    currency = None

    if "COP" in price_text:
        currency = "COP"

    if "$" in price_text:
        currency = "USD"

    if "€" in price_text or "EUR" in price_text:
        currency = "EUR"

    numbers = re.findall(r"\d+\.?\d*", price_text)

    if numbers:
        price = float(numbers[0])
    else:
        price = None

    return price, currency


# ==========================================================
# DETECTAR REFERENCIA / MODELO
# ==========================================================
def detect_reference(title, technical_details, product_information, bullets, description, url):

    keywords = [
        "model",
        "modelo",
        "model number",
        "item model number",
        "item model",
        "product model",
        "part number",
        "item number",
        "sku",
        "referencia",
        "Número de modelo del producto"
    ]

    # normalizar texto
    title = normalize_amazon_text(title)
    description = normalize_amazon_text(description)

    # ======================================================
    # 1 BUSCAR EN TABLAS TECNICAS
    # ======================================================
    if technical_details:

        for key, value in technical_details.items():

            key = normalize_amazon_text(key)
            value = normalize_amazon_text(value)

            key_lower = key.lower()

            if any(word in key_lower for word in keywords):

                ref = str(value).strip()

                if len(ref) >= 3:
                    return ref


    # ======================================================
    # 2 BUSCAR EN PRODUCT INFORMATION
    # ======================================================
    if product_information:

        for key, value in product_information.items():

            key = normalize_amazon_text(key)
            value = normalize_amazon_text(value)

            key_lower = key.lower()

            if any(word in key_lower for word in keywords):

                ref = str(value).strip()

                if len(ref) >= 3:
                    return ref


    # ======================================================
    # 3 BUSCAR MODELOS EN TITULO
    # ======================================================
    if title:

        patterns = [

            r"\b[A-Z0-9]{2,}-[A-Z0-9\-]{2,}\b",
            r"\b[A-Z]{1,2}[0-9]{3,4}\b",
            r"\b[A-Z]{2,}[0-9]{2,}\b"

        ]

        for pattern in patterns:

            matches = re.findall(pattern, title)

            if matches:
                return matches[0]


    # ======================================================
    # 4 BUSCAR MODELOS EN BULLETS
    # ======================================================
    if bullets:

        clean_bullets = [normalize_amazon_text(b) for b in bullets]

        text = " ".join(clean_bullets)

        matches = re.findall(r"\b[A-Z]{1,2}[0-9]{3,4}\b", text)

        if matches:
            return matches[0]


    # ======================================================
    # 5 BUSCAR MODELOS EN DESCRIPCION
    # ======================================================
    if description:

        matches = re.findall(r"\b[A-Z]{1,2}[0-9]{3,4}\b", description)

        if matches:
            return matches[0]


    # ======================================================
    # 6 FALLBACK → ASIN AMAZON
    # ======================================================
    if url:

        asin_match = re.search(r"/dp/([A-Z0-9]{10})", url)

        if asin_match:
            return asin_match.group(1)

    return None


# ==========================================================
# ELIMINAR MARCA DE REFERENCIA
# ==========================================================
def remove_brand_from_reference(referencia, marca):

    if not referencia:
        return referencia

    referencia = normalize_amazon_text(referencia)

    referencia = referencia.replace("_", "-")
    referencia = referencia.replace(" ", "-")

    referencia = re.sub(r"-+", "-", referencia)
    referencia = referencia.strip()

    if marca:

        marca_upper = marca.upper()
        ref_upper = referencia.upper()

        if ref_upper.startswith(marca_upper):
            referencia = referencia[len(marca):]

    referencia = referencia.strip("-")
    referencia = re.sub(r"-+", "-", referencia)

    return referencia


# ==========================================================
# FILTRAR SPECS BASURA AMAZON
# ==========================================================
def filter_irrelevant_specs(technical_details):

    ignore_keywords = [

        "asin",
        "fabricante",
        "manufacturer",
        "pais",
        "country",
        "date",
        "available",
        "first",
        "origen",
        "ranking",
        "seller",
        "brand",
        "customer",
        "review",
        "opinión",
        "rating",
        "amazon",
        "best sellers",
        "clasificación",
        "opinión media",
        "usuarios sugeridos",
        "estilo",
        "color",
        "tamaño",
        "size",
        "upc"

    ]

    clean_specs = {}

    for key, value in technical_details.items():

        if value is None:
            continue

        key_lower = key.lower()

        if not any(word in key_lower for word in ignore_keywords):
            clean_specs[key] = value

    return clean_specs


# ==========================================================
# EXTRAER SPECS AUTOMATICAS
# ==========================================================
def extract_specs_from_text(text):

    specs = {}
 
    patterns = {

        "Potencia": r"\b\d+\s?W\b",
        "Voltaje": r"\b\d+\s?V\b",
        "Corriente": r"\b\d+\s?A\b",
        "Frecuencia": r"\b\d+\s?Hz\b",
        "Peso": r"\b\d+(\.\d+)?\s?(kg|lb)\b",
        "Dimensión": r"\b\d+\s?mm\b",
        "Capacidad": r"\b\d+\s?(GB|L|litros)\b",
        "Temperatura": r"\b\d+\s?°C\b",
        "Alcance": r"\b\d+\s?m\b"

    }

    for field, pattern in patterns.items():

        match = re.search(pattern, text)

        if match:
            specs[field] = match.group(0)

    return specs


# ==========================================================
# FUNCIÓN PRINCIPAL
# ==========================================================
def clean_raw_product(raw_data: dict):

    title_raw = raw_data.get("title_raw")
    brand_raw = raw_data.get("brand_raw")

    bullets = raw_data.get("bullets", [])
    technical_details = raw_data.get("technical_details", {})
    product_information = raw_data.get("product_information", {})

    price_text = raw_data.get("price_text")
    url_origen = raw_data.get("url_origen")

    product_description = raw_data.get("product_description")

    # LIMPIEZA BASICA
    marca = clean_brand(brand_raw)
    
    # ======================================================
    # FIX PRECIO (COMPATIBLE CON NUEVO EXTRACTOR)
    # ======================================================

    price_value = raw_data.get("price_value")
    currency_raw = raw_data.get("currency")

    # 1. PRIORIDAD: usar precio ya procesado por el extractor
    if price_value:
        costo = price_value
        moneda = currency_raw or "USD"

    # 2. FALLBACK: usar lógica antigua (parse_price)
    else:
        costo, moneda = parse_price(price_text)

    title_raw = clean_text(title_raw)
    product_description = clean_text(product_description)

    # NORMALIZACION
    bullets = normalize_bullets(bullets)
    technical_details = normalize_technical_specs(technical_details)

    # FILTRAR SPECS BASURA
    technical_details = filter_irrelevant_specs(technical_details)

    # DETECTAR REFERENCIA
    referencia = detect_reference(
        title_raw,
        technical_details,
        product_information,
        bullets,
        product_description,
        url_origen
    )

    referencia = remove_brand_from_reference(referencia, marca)

    # evitar referencia igual a marca
    if referencia and marca:

        if referencia.upper() == marca.upper():
            referencia = None

    # fallback asin
    if not referencia and url_origen:

        asin_match = re.search(r"/dp/([A-Z0-9]{10})", url_origen)

        if asin_match:
            referencia = asin_match.group(1)

    if referencia and len(referencia) > 40:
        referencia = referencia[:40]

    # DETECTAR SPECS
    text_blob = " ".join(bullets)

    if product_description:
        text_blob += " " + product_description

    auto_specs = extract_specs_from_text(text_blob)

    for k, v in auto_specs.items():

        if k not in technical_details:
            technical_details[k] = v

    cleaned_data = {

        "title_raw": title_raw,
        "marca": marca,
        "referencia": referencia,
        "bullets": bullets,
        "technical_details": technical_details,
        "product_description": product_description,
        "product_information": product_information,
        "costo": costo,
        "moneda": moneda,
        "peso": None,
        "url_origen": url_origen,
        "metadata": raw_data.get("metadata", {})

    }

    return cleaned_data