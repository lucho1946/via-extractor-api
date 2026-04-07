# ==========================================================
# SPEC POSTPROCESSOR
# ----------------------------------------------------------
# Limpia y mejora la descripción generada por la IA
# sin romper la estructura de la ficha técnica
# ==========================================================

import re


# ----------------------------------------------------------
# Limpia caracteres invisibles y espacios
# ----------------------------------------------------------

def clean_spec_line(line: str):

    if line is None:
        return ""

    line = line.replace("‎", "")  # caracter invisible amazon
    line = line.strip()

    return line


# ----------------------------------------------------------
# Detecta si la línea es un encabezado
# ----------------------------------------------------------

def is_section_header(line: str):

    headers = [
        "DESCRIPCIÓN GENERAL",
        "VENTAJAS PRINCIPALES",
        "APLICACIONES",
        "CARACTERÍSTICAS TÉCNICAS"
    ]

    for h in headers:
        if line.upper().startswith(h):
            return True

    return False


# ----------------------------------------------------------
# Elimina duplicados solo en especificaciones técnicas
# ----------------------------------------------------------

def remove_duplicates(lines):

    seen = set()
    result = []

    for line in lines:

        key = line.lower()

        if key not in seen:
            seen.add(key)
            result.append(line)

    return result


# ----------------------------------------------------------
# Combina voltajes repetidos
# ----------------------------------------------------------

def merge_voltage(lines):

    voltages = []
    new_lines = []

    for line in lines:

        if "Voltaje" in line:

            value = re.findall(r"\d+\s?V", line)

            if value:
                voltages.append(value[0])

        else:
            new_lines.append(line)

    if voltages:

        merged = "• Voltaje nominal: " + " / ".join(sorted(set(voltages)))

        new_lines.append(merged)

    return new_lines


# ----------------------------------------------------------
# FUNCIÓN PRINCIPAL
# ----------------------------------------------------------

def process_description(text):

    if not text:
        return text

    lines = text.split("\n")

    cleaned_lines = []

    for line in lines:

        line = clean_spec_line(line)

        # mantener líneas vacías para estructura
        if line == "":
            cleaned_lines.append("")
            continue

        cleaned_lines.append(line)

    # detectar bloque de características técnicas
    tech_section = False
    processed = []
    tech_lines = []

    for line in cleaned_lines:

        if is_section_header(line):
            tech_section = "CARACTERÍSTICAS TÉCNICAS" in line
            processed.append(line)
            continue

        if tech_section:
            tech_lines.append(line)
        else:
            processed.append(line)

    # limpiar duplicados en specs
    tech_lines = remove_duplicates(tech_lines)

    # combinar voltajes
    tech_lines = merge_voltage(tech_lines)

    processed.extend(tech_lines)

    return "\n".join(processed)