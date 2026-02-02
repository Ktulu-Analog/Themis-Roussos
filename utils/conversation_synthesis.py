"""
Génération automatique de synthèses de conversations juridiques
"""

import logging
import yaml
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


def load_synthesis_prompt() -> str:
    """
    Charger le prompt de synthèse depuis prompt.yml

    Returns:
        Prompt de synthèse
    """
    with open("prompt.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        return config["synthesis_prompt"]


def generate_conversation_synthesis(
    client,
    model: str,
    messages: List[Dict],
    conversation_name: str = "Conversation juridique"
) -> str:
    """
    Générer une synthèse complète d'une conversation juridique

    Args:
        client: Client OpenAI/LLM
        model: Modèle à utiliser (défini dans .env comme SYNTHESIS_MODEL)
        messages: Liste des messages de la conversation
        conversation_name: Nom de la conversation

    Returns:
        Synthèse au format Markdown
    """

    if not messages or len(messages) < 2:
        return "⚠️ Conversation trop courte pour générer une synthèse significative."

    # Construire le contexte complet de la conversation
    conversation_text = _format_conversation_for_synthesis(messages)

    # Charger le prompt de synthèse
    synthesis_prompt = load_synthesis_prompt()

    # Préparer le message pour le LLM
    user_message = f"""**Titre de la conversation** : {conversation_name}

**Conversation à synthétiser** :

{conversation_text}

---

Produis une synthèse structurée et professionnelle de cette conversation juridique en suivant les instructions du prompt système.
"""

    try:
        logger.info(f"🔍 Génération synthèse avec {model}...")

        response = client.chat.completions.create(
            model=model,
            temperature=0.3,
            messages=[
                {"role": "system", "content": synthesis_prompt},
                {"role": "user", "content": user_message}
            ]
        )

        synthesis = response.choices[0].message.content.strip()

        # Ajouter métadonnées en en-tête
        header = _create_synthesis_header(conversation_name)
        full_synthesis = f"{header}\n\n{synthesis}"

        logger.info(f"✅ Synthèse générée ({len(synthesis)} caractères)")
        return full_synthesis

    except Exception as e:
        logger.error(f"❌ Erreur génération synthèse: {e}")
        return f"❌ Erreur lors de la génération de la synthèse : {str(e)}"


def _format_conversation_for_synthesis(messages: List[Dict]) -> str:
    """
    Formater la conversation pour l'envoi au LLM

    Args:
        messages: Liste des messages

    Returns:
        Conversation formatée en texte
    """
    formatted = []

    for i, msg in enumerate(messages, 1):
        role = "👤 Utilisateur" if msg["role"] == "user" else "⚖️ Assistant Juridique"
        content = msg["content"]

        # Limiter la longueur si nécessaire (pour rester dans les limites du contexte)
        if len(content) > 4000:
            content = content[:4000] + "\n[...tronqué...]"

        formatted.append(f"**Message {i} - {role}**\n\n{content}\n")

    return "\n".join(formatted)


def _create_synthesis_header(conversation_name: str) -> str:
    """
    Créer l'en-tête de la synthèse avec métadonnées

    Args:
        conversation_name: Nom de la conversation

    Returns:
        En-tête formaté en Markdown
    """
    now = datetime.now()

    header = f"""# Synthèse de Conversation Juridique

**Sujet** : {conversation_name}

**Date de génération** : {now.strftime("%d/%m/%Y à %H:%M")}

**Système** : Thémis Roussos - Assistant juridique alimenté par Légifrance

---
"""

    return header


def estimate_synthesis_length(messages: List[Dict]) -> str:
    """
    Estimer le temps et la longueur de la synthèse

    Args:
        messages: Liste des messages

    Returns:
        Description de l'estimation
    """
    total_chars = sum(len(msg.get("content", "")) for msg in messages)
    message_count = len(messages)

    if message_count < 5:
        return "Synthèse courte (~1 page)"
    elif message_count < 15:
        return "Synthèse moyenne (~2 pages)"
    else:
        return "Synthèse détaillée (~3 pages)"
