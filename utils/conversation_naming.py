"""
Génération automatique de noms de conversations par LLM
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def generate_conversation_name(client, model: str, messages: List[Dict]) -> str:
    """
    Générer un nom de conversation à partir des premiers messages

    Args:
        client: Client OpenAI
        model: Modèle léger (ex: meta-llama/Llama-3.1-8B-Instruct)
        messages: Liste des messages de la conversation

    Returns:
        Nom de la conversation (max 60 caractères)
    """

    # Prendre les 3-5 premiers messages
    first_messages = messages[:5]

    if not first_messages:
        return "Nouvelle conversation"

    # Construire le contexte
    context = "\n".join([
        f"{msg['role']}: {msg['content'][:300]}"
        for msg in first_messages
    ])

    NAMING_PROMPT = """Génère un titre court et descriptif pour cette conversation juridique.

Le titre doit :
- Être en français
- Faire maximum 60 caractères
- Résumer le sujet juridique principal
- Être spécifique et informatif
- Ne PAS contenir de guillemets

Exemples de bons titres :
- Réforme du droit du travail 2015-2020
- Évolution statut fonction publique
- Loi El Khomri et ordonnances Macron
- Procédure licenciement économique
- Rupture conventionnelle CDI
- Congés payés et RTT

Réponds UNIQUEMENT avec le titre, sans guillemets ni explication.

CONVERSATION :
"""

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0.3,
            max_tokens=50,
            messages=[
                {"role": "system", "content": NAMING_PROMPT},
                {"role": "user", "content": context}
            ]
        )

        name = response.choices[0].message.content.strip()

        # Nettoyer
        name = name.strip('"\'')
        name = name[:60]  # Limiter à 60 caractères

        # Si vide ou trop court, fallback
        if len(name) < 5:
            name = "Nouvelle conversation"

        logger.info(f"✅ Nom généré: {name}")
        return name

    except Exception as e:
        logger.error(f"Erreur génération nom: {e}")
        return "Nouvelle conversation"


def should_generate_name(messages: List[Dict], current_name: str) -> bool:
    """
    Déterminer si on doit générer un nom pour la conversation

    Args:
        messages: Liste des messages
        current_name: Nom actuel de la conversation

    Returns:
        True si on doit générer un nom
    """
    # Ne générer que si :
    # - Le nom est encore "Nouvelle conversation"
    # - On a au moins 3 messages (user + assistant + user)
    # - On n'a pas déjà généré (éviter de régénérer à chaque fois)

    return (
        current_name == "Nouvelle conversation" and
        len(messages) >= 3
    )
