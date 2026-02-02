"""
Utilitaire pour convertir le HTML de Légifrance en Markdown pour l'affichage dans le chat.
Traite les tableaux, les liens hypertextes, les sauts de ligne et le formatage.
"""

import re
from bs4 import BeautifulSoup
from typing import Optional


def clean_html_for_chat(html_content: str) -> str:
    """
    Convertit le HTML en Markdown pour l'affichage dans le chat.

    Args:
        html_content: Contenu HTML brut

    Returns:
        Contenu formaté en Markdown
    """
    if not html_content or not isinstance(html_content, str):
        return ""

    soup = BeautifulSoup(html_content, "html.parser")

    # 1. Traiter les liens hypertextes Legifrance
    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        text = link.get_text(strip=True)

        # Reconstruire les URLs relatives Legifrance
        if href.startswith("/"):
            href = f"https://www.legifrance.gouv.fr{href}"

        # Remplacer par un lien Markdown
        if text and href:
            link.replace_with(f"[{text}]({href})")
        elif href:
            link.replace_with(f"<{href}>")

    # 2. Traiter les tableaux
    for table in soup.find_all("table"):
        markdown_table = _convert_table_to_markdown(table)
        table.replace_with(f"\n\n{markdown_table}\n\n")

    # 3. Traiter les sauts de ligne <br>
    for br in soup.find_all("br"):
        br.replace_with("\n")

    # 4. Traiter les balises de formatage
    for tag in soup.find_all("strong"):
        text = tag.get_text(strip=True)
        tag.replace_with(f"**{text}**")

    for tag in soup.find_all("em"):
        text = tag.get_text(strip=True)
        tag.replace_with(f"*{text}*")

    for tag in soup.find_all("b"):
        text = tag.get_text(strip=True)
        tag.replace_with(f"**{text}**")

    for tag in soup.find_all("i"):
        text = tag.get_text(strip=True)
        tag.replace_with(f"*{text}*")

    # 5. Traiter les titres
    for level in range(1, 7):
        for tag in soup.find_all(f"h{level}"):
            text = tag.get_text(strip=True)
            tag.replace_with(f"\n\n{'#' * level} {text}\n\n")

    # 6. Traiter les paragraphes
    for p in soup.find_all("p"):
        text = p.get_text(separator="\n", strip=True)
        p.replace_with(f"\n\n{text}\n\n")

    # 7. Traiter les listes
    for ul in soup.find_all("ul"):
        items = []
        for li in ul.find_all("li", recursive=False):
            text = li.get_text(strip=True)
            items.append(f"- {text}")
        ul.replace_with("\n" + "\n".join(items) + "\n")

    for ol in soup.find_all("ol"):
        items = []
        for idx, li in enumerate(ol.find_all("li", recursive=False), 1):
            text = li.get_text(strip=True)
            items.append(f"{idx}. {text}")
        ol.replace_with("\n" + "\n".join(items) + "\n")

    # 8. Extraire le texte final
    text = soup.get_text(separator="\n")

    # 9. Nettoyer les espaces et sauts de ligne multiples
    lines = []
    for line in text.split("\n"):
        cleaned = line.strip()
        if cleaned:
            lines.append(cleaned)

    result = "\n".join(lines)

    # Réduire les sauts de ligne multiples à maximum 2
    result = re.sub(r'\n{3,}', '\n\n', result)

    return result.strip()


def _convert_table_to_markdown(table_tag) -> str:
    """
    Convertit un tableau HTML en tableau Markdown.

    Args:
        table_tag: Tag BeautifulSoup représentant un tableau

    Returns:
        Tableau formaté en Markdown
    """
    # Traiter les <br> dans les cellules
    for br in table_tag.find_all("br"):
        br.replace_with(" ")

    rows = []

    # Extraire les en-têtes
    headers = []
    thead = table_tag.find("thead")
    if thead:
        for th in thead.find_all(["th", "td"]):
            text = th.get_text(strip=True)
            text = _clean_cell_text(text)
            headers.append(text)

    # Si pas de thead, chercher les th dans la première ligne
    if not headers:
        first_row = table_tag.find("tr")
        if first_row:
            for th in first_row.find_all("th"):
                text = th.get_text(strip=True)
                text = _clean_cell_text(text)
                headers.append(text)

    # Ajouter les en-têtes si présents
    if headers:
        rows.append("| " + " | ".join(headers) + " |")
        rows.append("| " + " | ".join(["---"] * len(headers)) + " |")

    # Extraire les lignes de données
    tbody = table_tag.find("tbody") or table_tag
    for tr in tbody.find_all("tr"):
        # Ignorer la première ligne si elle contient les en-têtes déjà traités
        if headers and tr == table_tag.find("tr"):
            continue

        cells = []
        for td in tr.find_all(["td", "th"]):
            text = td.get_text(strip=True)
            text = _clean_cell_text(text)
            cells.append(text)

        if cells:
            rows.append("| " + " | ".join(cells) + " |")

    return "\n".join(rows) if rows else ""


def _clean_cell_text(text: str) -> str:
    """
    Nettoie le texte d'une cellule de tableau.

    Args:
        text: Texte brut de la cellule

    Returns:
        Texte nettoyé
    """
    # Remplacer les sauts de ligne par des espaces
    text = text.replace("\n", " ").replace("\r", " ")
    text = text.replace("\\n", " ").replace("\\t", " ")

    # Nettoyer les espaces multiples
    text = re.sub(r'\s+', ' ', text).strip()

    # Échapper les pipes pour Markdown
    text = text.replace("|", "\\|")

    return text


def extract_legifrance_links(html_content: str) -> list[dict]:
    """
    Extrait tous les liens Legifrance d'un contenu HTML.

    Args:
        html_content: Contenu HTML

    Returns:
        Liste de dictionnaires {text, url}
    """
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, "html.parser")
    links = []

    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        text = link.get_text(strip=True)

        if href.startswith("/"):
            href = f"https://www.legifrance.gouv.fr{href}"

        if "legifrance.gouv.fr" in href:
            links.append({"text": text, "url": href})

    return links
