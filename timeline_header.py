"""
Composant Timeline Horizontal Permanent
Timeline affichée en permanence en haut de l'écran

version : 0.3.1
date    : 31/01/2026

Améliorations v0.3.1 :
- Couleurs par type d'événement corrigées (loi, decret, etc.)
- Labels simplifiés (nom du texte uniquement)
- Informations complètes au survol
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
import re

logger = logging.getLogger(__name__)


# Configuration des couleurs par type d'événement juridique
EVENT_COLORS = {
    # Types principaux
    'loi': '#4A90E2',           # Bleu - Lois
    'decret': '#F5A623',        # Orange - Décrets
    'arrete': '#FFD700',        # Jaune doré - Arrêtés
    'ordonnance': '#9013FE',    # Violet - Ordonnances
    'jurisprudence': '#D0021B', # Rouge - Décisions de justice

    # Événements de cycle de vie
    'signature': '#50E3C2',     # Turquoise - Signature
    'publication': '#7ED321',   # Vert - Publication JO
    'application': '#FF6B6B',   # Rouge clair - Entrée en application
    'modification': '#A78BFA',  # Violet clair - Modification
    'abrogation': '#EF4444',    # Rouge vif - Abrogation
    'vigueur': '#10B981',       # Vert émeraude - En vigueur

    # Types génériques
    'texte': '#6B7280',         # Gris - Texte générique
    'reforme': '#EC4899',       # Rose - Réforme
    'codification': '#8B5CF6',  # Violet foncé - Codification

    # Fallback
    'default': '#999999'        # Gris neutre
}

EVENT_LABELS = {
    'loi': 'Loi',
    'decret': 'Décret',
    'arrete': 'Arrêté',
    'ordonnance': 'Ordonnance',
    'jurisprudence': 'Jurisprudence',
    'signature': 'Signature',
    'publication': 'Publication',
    'application': 'Application',
    'modification': 'Modification',
    'abrogation': 'Abrogation',
    'vigueur': 'En vigueur',
    'texte': 'Texte',
    'reforme': 'Réforme',
    'codification': 'Codification'
}


class TimelineEvent:
    """Événement sur la timeline"""
    def __init__(
        self,
        date: datetime,
        title: str,
        event_type: str,
        description: str = "",
        details: str = ""
    ):
        self.date = date
        self.title = title
        self.event_type = event_type
        self.description = description
        self.details = details


def _extract_short_title(full_title: str) -> str:
    """
    Extrait un titre court pour l'affichage statique

    Exemples :
    "Loi n° 2016-1088 du 8 août 2016 relative au travail"
    → "Loi n° 2016-1088 du 8 août 2016"

    "Décret n° 2016-151 du 11 février 2016"
    → "Décret n° 2016-151 du 11 février 2016"

    "Ordonnances Macron - Réforme du Code du travail"
    → "Ordonnances Macron"
    """

    # Pattern 1 : Texte avec numéro et date (le plus spécifique)
    # Ex: "Loi n° 2016-1088 du 8 août 2016 relative au..."
    pattern1 = r'^((?:Loi|Décret|Arrêté|Ordonnance)[^,]*?(?:n°|nº)\s*[\d\-]+\s+du\s+\d{1,2}\s+\w+\s+\d{4})'
    match = re.search(pattern1, full_title, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Pattern 2 : Texte avec numéro seulement
    # Ex: "Décret n° 2020-1310"
    pattern2 = r'^((?:Loi|Décret|Arrêté|Ordonnance)[^,]*?(?:n°|nº)\s*[\d\-]+)'
    match = re.search(pattern2, full_title, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Pattern 3 : Avant le premier tiret ou la première virgule
    # Ex: "Ordonnances Macron - Réforme..." → "Ordonnances Macron"
    if ' - ' in full_title:
        return full_title.split(' - ')[0].strip()
    if ',' in full_title:
        return full_title.split(',')[0].strip()

    # Pattern 4 : Première phrase (jusqu'à 50 caractères)
    if len(full_title) > 50:
        return full_title[:47] + "..."

    return full_title


def create_horizontal_timeline(events: List[TimelineEvent]) -> go.Figure:
    """
    Crée une timeline horizontale style Légifrance avec couleurs

    Affichage statique : Nom court du texte uniquement
    Au survol : Informations complètes

    Args:
        events: Liste d'événements à afficher

    Returns:
        Figure Plotly interactive
    """
    if not events:
        return None

    # Trier les événements par date
    sorted_events = sorted(events, key=lambda e: e.date)

    # Créer la figure
    fig = go.Figure()

    # Ajouter la ligne de base (axe temporel)
    min_date = min(e.date for e in sorted_events)
    max_date = max(e.date for e in sorted_events)

    # Ajouter une marge de 5% de chaque côté
    date_range = (max_date - min_date).days
    margin = date_range * 0.05 if date_range > 0 else 30

    from datetime import timedelta
    plot_min = min_date - timedelta(days=margin)
    plot_max = max_date + timedelta(days=margin)

    # Ligne horizontale principale
    fig.add_trace(go.Scatter(
        x=[plot_min, plot_max],
        y=[0, 0],
        mode='lines',
        line=dict(color='#E0E0E0', width=3),
        showlegend=False,
        hoverinfo='skip'
    ))

    # Ajouter les événements
    for i, event in enumerate(sorted_events):
        # Récupérer la couleur selon le type
        event_type_lower = event.event_type.lower()
        color = EVENT_COLORS.get(event_type_lower, EVENT_COLORS.get('default'))

        # Extraire le titre court pour l'affichage statique
        short_title = _extract_short_title(event.title)

        # Point sur la timeline
        fig.add_trace(go.Scatter(
            x=[event.date],
            y=[0],
            mode='markers',
            marker=dict(
                size=16,
                color=color,
                symbol='circle',
                line=dict(width=3, color='white')
            ),
            name=EVENT_LABELS.get(event_type_lower, event.event_type.capitalize()),
            showlegend=False,
            hovertemplate=(
                f"<b>{event.title}</b><br>"
                f"<b>📅 {event.date.strftime('%d/%m/%Y')}</b><br>"
                f"<b>📋 {EVENT_LABELS.get(event_type_lower, event.event_type.capitalize())}</b><br>"
                f"{event.description}<br>"
                f"<i>{event.details}</i>"
                "<extra></extra>"
            )
        ))

        # Ligne verticale vers le label
        y_offset = 0.3 if i % 2 == 0 else -0.3
        fig.add_trace(go.Scatter(
            x=[event.date, event.date],
            y=[0, y_offset],
            mode='lines',
            line=dict(color=color, width=2, dash='dot'),
            showlegend=False,
            hoverinfo='skip'
        ))

        # Label statique (titre court uniquement)
        label_y = y_offset + (0.1 if i % 2 == 0 else -0.1)
        fig.add_annotation(
            x=event.date,
            y=label_y,
            text=f"<b>{short_title}</b>",
            showarrow=False,
            font=dict(size=9, color='#333333'),
            bgcolor='white',
            bordercolor=color,
            borderwidth=2,
            borderpad=4,
            align='center',
            # Ajouter un tooltip au survol de l'annotation
            hovertext=event.title
        )

    # Configuration du layout
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            showgrid=False,
            showticklabels=True,
            zeroline=False,
            tickformat='%Y',
            tickmode='linear',
            dtick='M12'  # Tick tous les 12 mois
        ),
        yaxis=dict(
            showgrid=False,
            showticklabels=False,
            zeroline=False,
            range=[-0.6, 0.6]
        ),
        hovermode='closest',
        showlegend=False
    )

    return fig


def display_timeline_header(events: List[TimelineEvent]) -> None:
    """
    Affiche la timeline en en-tête permanent

    Args:
        events: Liste d'événements à afficher
    """
    if not events:
        # Timeline vide avec message
        st.info("La chronologie s'affichera automatiquement lorsque des dates seront détectées dans les réponses.")
        return

    # Titre avec badge
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### 📅 Chronologie des événements")
    with col2:
        # Badge avec le nombre d'événements
        st.markdown(
            f"<div style='text-align: right; padding-top: 8px;'>"
            f"<span style='background-color: #4A90E2; color: white; padding: 4px 12px; "
            f"border-radius: 12px; font-size: 0.9em; font-weight: bold;'>"
            f"{len(events)} événement{'s' if len(events) > 1 else ''}</span>"
            f"</div>",
            unsafe_allow_html=True
        )

    # Afficher la timeline
    fig = create_horizontal_timeline(events)
    if fig:
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # Légende compacte avec couleurs
    with st.expander("📖 Légende", expanded=False):
        # Regrouper par colonnes
        types_used = set(e.event_type.lower() for e in events)
        types_to_show = [t for t in EVENT_COLORS.keys() if t in types_used or t == 'default']

        # Limiter à 6 colonnes maximum
        num_cols = min(6, len(types_to_show))
        if num_cols > 0:
            cols = st.columns(num_cols)
            for i, event_type in enumerate(types_to_show[:num_cols]):
                color = EVENT_COLORS[event_type]
                label = EVENT_LABELS.get(event_type, event_type.capitalize())
                with cols[i % num_cols]:
                    st.markdown(
                        f"<div style='display: flex; align-items: center; margin-bottom: 4px;'>"
                        f"<div style='width: 16px; height: 16px; background-color: {color}; "
                        f"border-radius: 50%; margin-right: 6px; border: 2px solid white;'></div>"
                        f"<span style='font-size: 0.85em;'>{label}</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

    st.divider()


def create_compact_timeline_badge(events: List[TimelineEvent]) -> str:
    """
    Crée un badge compact pour afficher le nombre d'événements

    Args:
        events: Liste d'événements

    Returns:
        HTML du badge
    """
    if not events:
        return ""

    # Compter par type
    type_counts = {}
    for event in events:
        event_type = event.event_type.lower()
        type_counts[event_type] = type_counts.get(event_type, 0) + 1

    # Créer le badge
    badges_html = ""
    for event_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        color = EVENT_COLORS.get(event_type, EVENT_COLORS['default'])
        label = EVENT_LABELS.get(event_type, event_type.capitalize())
        badges_html += (
            f"<span style='background-color: {color}; color: white; "
            f"padding: 2px 8px; border-radius: 10px; font-size: 0.8em; "
            f"margin-right: 4px; font-weight: bold;'>"
            f"{label}: {count}</span>"
        )

    return badges_html


def extract_events_from_last_response(messages):
    """
    Extracteur robuste multi-format :
    - JSON (prioritaire)
    - Tableaux Markdown
    - Tableaux HTML
    - Listes avec dates
    - Dates isolées
    """

    import re
    import json

    # =====================================================
    # Récupérer la dernière réponse
    # =====================================================
    last_assistant_message = None
    for msg in reversed(messages):
        if msg.get("role") == "assistant":
            last_assistant_message = msg.get("content", "")
            break

    if not last_assistant_message:
        return []

    text = last_assistant_message
    events = []

    # =====================================================
    # Priorité à une sortie JSON
    # =====================================================

    json_pattern = r'\[\s*\{.*?\}\s*\]'
    json_match = re.search(json_pattern, text, re.DOTALL)

    if json_match:
        try:
            data = json.loads(json_match.group())

            for item in data:
                date = _parse_date_french(item.get("date"))
                if not date:
                    continue

                events.append(TimelineEvent(
                    date=date,
                    title=item.get("title", "Événement"),
                    event_type=item.get("type", "modification"),
                    description=item.get("description", ""),
                    details=item.get("details", "")
                ))

            logger.info(f"Timeline JSON détectée: {len(events)} événements")
            return sorted(events, key=lambda e: e.date)

        except Exception:
            pass

    # =====================================================
    # Tableaux Markdown
    # =====================================================

    md_pattern = r'^\s*(\d{4})\s*\|\s*([^\|]+)\|\s*([^\n]+)'
    matches = re.finditer(md_pattern, text, re.MULTILINE)

    for m in matches:
        date = _parse_date_french(m.group(1))
        if not date:
            continue

        events.append(TimelineEvent(
            date=date,
            title=m.group(2).strip()[:60],
            event_type='modification',
            description=m.group(3).strip()[:120]
        ))

    # =====================================================
    # Tableaux HTML
    # =====================================================

    html_pattern = r'<td[^>]*>\s*(\d{4})\s*</td>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>'
    matches = re.finditer(html_pattern, text, re.DOTALL | re.IGNORECASE)

    for m in matches:
        date = _parse_date_french(m.group(1))
        if not date:
            continue

        title = re.sub('<[^<]+?>', '', m.group(2)).strip()
        desc = re.sub('<[^<]+?>', '', m.group(3)).strip()

        events.append(TimelineEvent(
            date=date,
            title=title[:60],
            event_type='modification',
            description=desc[:120]
        ))

    # =====================================================
    # Listes avec dates complètes
    # Exemple :
    # - Loi du 6 août 2019
    # =====================================================

    full_date_pattern = r'(\d{1,2}\s+\w+\s+\d{4})'
    matches = re.finditer(full_date_pattern, text)

    for m in matches:
        date = _parse_date_french(m.group(1))
        if not date:
            continue

        snippet_start = max(0, m.start() - 40)
        snippet_end = min(len(text), m.end() + 80)

        snippet = text[snippet_start:snippet_end].replace("\n", " ")

        events.append(TimelineEvent(
            date=date,
            title="Texte juridique",
            event_type='publication',
            description=snippet[:120]
        ))

    # =====================================================
    # Années isolées  avec fallback
    # =====================================================

    years = re.findall(r'\b(19|20)\d{2}\b', text)

    for year in set(years):
        date = _parse_date_french(year)

        if date:
            events.append(TimelineEvent(
                date=date,
                title=f"Année {year}",
                event_type='modification',
                description="Événement détecté automatiquement"
            ))

    # =====================================================
    # Déduplication
    # =====================================================

    unique = {}
    for e in events:
        key = e.date.strftime('%Y-%m-%d')
        if key not in unique:
            unique[key] = e

    final_events = list(unique.values())

    logger.info(f"Timeline extraite (mode PRO): {len(final_events)} événements")

    return sorted(final_events, key=lambda e: e.date)


def _parse_date_french(date_str: str) -> Optional[datetime]:
    """
    Parse une date en format français

    Args:
        date_str: "2 juillet 2014", "23 mars 2023", "2020", etc.

    Returns:
        datetime ou None
    """
    if not date_str:
        return None

    # Nettoyer
    date_str = str(date_str).strip()

    # Pattern 1: Année seule ex : 2020
    if re.match(r'^\d{4}$', date_str):
        try:
            return datetime(int(date_str), 1, 1)
        except ValueError:
            pass

    # Mapping des mois : complets, courts, sans accents
    mois_fr = {
        'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4,
        'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8,
        'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12,
        'janv': 1, 'févr': 2, 'avr': 4, 'juill': 7, 'sept': 9, 'oct': 10,
        'nov': 11, 'déc': 12,
        'fev': 2, 'aout': 8, 'dec': 12
    }

    # Pattern 2: "2 juillet 2014"
    pattern = r'(\d{1,2})\s+(\w+)\s+(\d{4})'
    match = re.search(pattern, date_str.lower())

    if match:
        day, month_name, year = match.groups()
        month = mois_fr.get(month_name)
        if month:
            try:
                return datetime(int(year), month, int(day))
            except ValueError:
                pass

    # Pattern 3: DD/MM/YYYY
    pattern2 = r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
    match2 = re.search(pattern2, date_str)
    if match2:
        day, month, year = match2.groups()
        try:
            return datetime(int(year), int(month), int(day))
        except ValueError:
            pass

    # Pattern 4: Extraire l'année si c'est tout ce que l'on a
    year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
    if year_match:
        try:
            return datetime(int(year_match.group(0)), 1, 1)
        except ValueError:
            pass

    return None
