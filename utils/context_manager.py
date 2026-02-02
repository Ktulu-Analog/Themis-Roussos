"""
Gestion du contexte des conversations pour éviter les dépassements
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def estimate_tokens(text: str) -> int:
    """
    Estimer le nombre de tokens dans un texte
    Approximation : 1 token ≈ 4 caractères pour le français

    Args:
        text: Texte à estimer

    Returns:
        Nombre approximatif de tokens
    """
    return len(text) // 4


def estimate_messages_tokens(messages: List[Dict]) -> int:
    """
    Estimer le nombre de tokens dans une liste de messages

    Args:
        messages: Liste de messages

    Returns:
        Nombre approximatif de tokens
    """
    total = 0
    for msg in messages:
        # Compter le contenu
        total += estimate_tokens(msg.get("content", ""))
        # Ajouter overhead pour role, etc. (~10 tokens par message)
        total += 10
    return total


def truncate_conversation(
    messages: List[Dict],
    max_tokens: int = 120000,
    keep_system: bool = True,
    keep_recent: int = 4
) -> List[Dict]:
    """
    Tronquer une conversation pour respecter la limite de tokens

    Args:
        messages: Liste complète des messages
        max_tokens: Limite maximale de tokens
        keep_system: Garder le message système (premier message)
        keep_recent: Nombre de messages récents à toujours garder

    Returns:
        Liste de messages tronquée
    """
    if not messages:
        return []

    # Estimer les tokens actuels
    current_tokens = estimate_messages_tokens(messages)

    if current_tokens <= max_tokens:
        logger.info(f"📊 Contexte OK : {current_tokens} tokens (limite: {max_tokens})")
        return messages

    logger.warning(f"⚠️ Contexte trop long : {current_tokens} tokens > {max_tokens}")

    # Séparer message système et conversation
    system_msg = messages[0] if keep_system and messages[0].get("role") == "system" else None
    conversation = messages[1:] if system_msg else messages

    # Garder les N derniers messages
    recent_messages = conversation[-keep_recent:] if len(conversation) > keep_recent else conversation

    # Construire la nouvelle liste
    truncated = []
    if system_msg:
        truncated.append(system_msg)

    # Ajouter un message indiquant la troncature
    if len(conversation) > keep_recent:
        truncated.append({
            "role": "system",
            "content": f"[Conversation tronquée - {len(conversation) - keep_recent} messages plus anciens omis pour respecter la limite de contexte]"
        })

    truncated.extend(recent_messages)

    new_tokens = estimate_messages_tokens(truncated)
    logger.info(f"✂️ Conversation tronquée : {current_tokens} → {new_tokens} tokens ({len(messages)} → {len(truncated)} messages)")

    return truncated


def smart_truncate_conversation(
    messages: List[Dict],
    max_tokens: int = 120000,
    system_prompt_tokens: int = 2000,
    response_buffer: int = 4000,
    keep_recent: int = 6
) -> List[Dict]:
    """
    Troncature intelligente de la conversation

    Stratégie :
    1. Réserver des tokens pour le prompt système
    2. Réserver des tokens pour la réponse
    3. Garder les N messages les plus récents
    4. Si encore trop long, résumer les messages du milieu

    Args:
        messages: Liste complète des messages
        max_tokens: Limite maximale du modèle
        system_prompt_tokens: Tokens réservés pour le prompt système
        response_buffer: Tokens réservés pour la réponse
        keep_recent: Nombre de messages récents à garder intacts

    Returns:
        Liste de messages optimisée
    """
    if not messages:
        return []

    # Budget disponible pour la conversation
    available_tokens = max_tokens - system_prompt_tokens - response_buffer

    # Estimer tokens actuels
    current_tokens = estimate_messages_tokens(messages)

    if current_tokens <= available_tokens:
        logger.info(f"📊 Contexte OK : {current_tokens}/{available_tokens} tokens disponibles")
        return messages

    logger.warning(f"⚠️ Contexte trop long : {current_tokens} > {available_tokens} tokens disponibles")

    # Séparer système et conversation
    system_msg = None
    start_idx = 0
    if messages and messages[0].get("role") == "system":
        system_msg = messages[0]
        start_idx = 1

    conversation = messages[start_idx:]

    # Garder les N messages les plus récents
    if len(conversation) <= keep_recent:
        # Pas assez de messages pour tronquer intelligemment
        return messages

    recent_messages = conversation[-keep_recent:]
    older_messages = conversation[:-keep_recent]

    # Construire la conversation tronquée
    truncated = []

    if system_msg:
        truncated.append(system_msg)

    # Ajouter un résumé des messages anciens
    if older_messages:
        summary = _create_conversation_summary(older_messages)
        truncated.append({
            "role": "system",
            "content": f"[Résumé des {len(older_messages)} messages précédents]\n\n{summary}"
        })

    # Ajouter les messages récents
    truncated.extend(recent_messages)

    new_tokens = estimate_messages_tokens(truncated)
    logger.info(f"✂️ Conversation optimisée : {current_tokens} → {new_tokens} tokens ({len(messages)} → {len(truncated)} messages)")

    return truncated


def _create_conversation_summary(messages: List[Dict]) -> str:
    """
    Créer un résumé concis des messages omis

    Args:
        messages: Messages à résumer

    Returns:
        Résumé textuel
    """
    if not messages:
        return ""

    # Compter les questions et réponses
    questions = sum(1 for m in messages if m.get("role") == "user")
    responses = sum(1 for m in messages if m.get("role") == "assistant")

    # Extraire quelques mots-clés des questions
    keywords = []
    for msg in messages:
        if msg.get("role") == "user":
            content = msg.get("content", "")[:100]  # Premiers 100 caractères
            keywords.append(content)

    summary = f"La conversation précédente contenait {questions} questions et {responses} réponses. "

    if keywords:
        summary += f"Sujets abordés : {', '.join(keywords[:3])}..."

    return summary


def check_context_before_call(
    messages: List[Dict],
    model_max_tokens: int = 128000,
    response_buffer: int = 4000
) -> tuple[bool, int, str]:
    """
    Vérifier si le contexte est OK avant un appel API

    Args:
        messages: Messages à envoyer
        model_max_tokens: Limite du modèle
        response_buffer: Tokens à réserver pour la réponse

    Returns:
        (is_ok, estimated_tokens, message)
    """
    estimated = estimate_messages_tokens(messages)
    available_for_response = model_max_tokens - estimated

    if available_for_response < 100:
        return False, estimated, f"❌ Contexte trop long : {estimated} tokens, impossible de répondre"
    elif available_for_response < response_buffer:
        return False, estimated, f"⚠️ Contexte limite : {estimated} tokens, seulement {available_for_response} tokens pour répondre"
    else:
        return True, estimated, f"✅ Contexte OK : {estimated} tokens, {available_for_response} tokens disponibles pour répondre"


def get_model_limits(model_name: str) -> dict:
    """
    Obtenir les limites de contexte pour un modèle

    Args:
        model_name: Nom du modèle

    Returns:
        Dict avec max_tokens et recommended_response_tokens
    """
    # Limites connues des modèles populaires
    limits = {
        "gpt-4": {"max_tokens": 8192, "response_buffer": 2000},
        "gpt-4-32k": {"max_tokens": 32768, "response_buffer": 4000},
        "gpt-4-turbo": {"max_tokens": 128000, "response_buffer": 4000},
        "gpt-4o": {"max_tokens": 128000, "response_buffer": 4000},
        "claude-opus-4": {"max_tokens": 200000, "response_buffer": 4000},
        "claude-sonnet-4": {"max_tokens": 200000, "response_buffer": 4000},
        "claude-haiku": {"max_tokens": 200000, "response_buffer": 4000},
        "meta-llama": {"max_tokens": 128000, "response_buffer": 4000},
    }

    # Chercher une correspondance partielle
    for key, value in limits.items():
        if key in model_name.lower():
            return value

    # Défaut conservateur
    return {"max_tokens": 8000, "response_buffer": 2000}


# Exemple d'utilisation dans app.py
"""
from utils.context_manager import smart_truncate_conversation, check_context_before_call

# Avant l'appel à chat_with_tools
messages_to_send = [{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.messages

# Vérifier et tronquer si nécessaire
messages_to_send = smart_truncate_conversation(
    messages_to_send,
    max_tokens=128000,  # Ajuster selon votre modèle
    keep_recent=8  # Garder les 8 derniers messages
)

# Vérification finale
is_ok, tokens, msg = check_context_before_call(messages_to_send)
if not is_ok:
    st.error(msg)
    st.stop()

# Appeler l'API
response = chat_with_tools(
    messages=messages_to_send,
    client=client,
    model=OPENAI_MODEL,
    max_iterations=max_iterations,
)
"""
