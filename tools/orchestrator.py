"""
Orchestration de la conversation avec outils
Gère la boucle d'interaction LLM + appels d'outils
"""

import json
import logging
from typing import Any, Dict, List, Union

from .definitions import TOOLS
from .executor import execute_tool

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Gère la conversation avec support des outils Légifrance
#
# Cette fonction implémente la boucle d'interaction entre le LLM et les outils:
# 1. Appelle le LLM avec les messages et les outils disponibles
# 2. Si le LLM demande d'utiliser un outil, l'exécute
# 3. Renvoie le résultat au LLM
# 4. Répète jusqu'à obtenir une réponse finale ou atteindre la limite
#
# Args:
#     messages: Liste des messages de la conversation
#     client: Client OpenAI
#     model: Nom du modèle à utiliser
#     max_iterations: Nombre maximum d'itérations pour les appels d'outils
#     verbose: Active les traces détaillées (défaut: False)
#     return_stats: Retourne (response, stats) au lieu de juste response
#
# Returns:
#     str ou tuple[str, dict]: Réponse finale (et stats si return_stats=True)
# -----------------------------------------------------------------------------
def chat_with_tools(
    messages: List[Dict[str, str]],
    client: Any,
    model: str,
    max_iterations: int = 5,
    verbose: bool = False,
    return_stats: bool = False,
) -> Union[str, tuple[str, Dict[str, Any]]]:

    current_messages = messages.copy()
    iteration = 0

    # Statistiques de traçage
    stats = {
        "iterations": 0,
        "max_iterations": max_iterations,
        "tool_calls": 0,
        "successful_calls": 0,
        "failed_calls": 0,
        "tools_used": {},
    }

    if verbose:
        logger.info("=" * 80)
        logger.info(f"🚀 Démarrage chat_with_tools (max: {max_iterations} itérations)")
        logger.info("=" * 80)

    while iteration < max_iterations:
        iteration += 1
        stats["iterations"] = iteration

        if verbose:
            logger.info(f"\n{'='*80}")
            logger.info(f"📍 Itération {iteration}/{max_iterations}")
            logger.info(f"{'='*80}")
            logger.info(f"   Messages dans le contexte: {len(current_messages)}")

        # Appel au modèle avec les outils disponibles
        if verbose:
            logger.info(f"   🤖 Appel au LLM ({model})...")

        response = client.chat.completions.create(
            model=model,
            messages=current_messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        message = response.choices[0].message
        current_messages.append(message.model_dump())

        # Si pas d'appel d'outil, retourner la réponse
        if not message.tool_calls:
            if verbose:
                logger.info(f"   ✅ Réponse finale du LLM (sans appel d'outil)")
                logger.info(f"   📝 Longueur de la réponse: {len(message.content or '')} caractères")
                _log_final_stats(stats, verbose)

            final_response = message.content or "Aucune réponse générée."
            return (final_response, stats) if return_stats else final_response

        # Traiter tous les appels d'outils
        if verbose:
            logger.info(f"   🔧 Appels d'outils: {', '.join([tc.function.name for tc in message.tool_calls])}")

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            stats["tool_calls"] += 1
            stats["tools_used"][tool_name] = stats["tools_used"].get(tool_name, 0) + 1

            if verbose:
                logger.info(f"   → Exécution: {tool_name} avec {arguments}")

            # Exécuter l'outil de manière synchrone
            result = execute_tool(tool_name, arguments)

            # Tracer le résultat
            if result.get("success"):
                stats["successful_calls"] += 1
                if verbose:
                    total = result.get("total_results", result.get("total_codes", "N/A"))
                    logger.info(f"   ✅ Succès - {total} résultat(s)")
            else:
                stats["failed_calls"] += 1
                if verbose:
                    error = result.get("error", "Erreur inconnue")
                    logger.info(f"   ❌ Échec - {error[:100]}...")

            # Ajouter le résultat aux messages
            current_messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": json.dumps(result, ensure_ascii=False, indent=2),
            })

    # Si on atteint le maximum d'itérations
    if verbose:
        logger.warning(f"\n{'='*80}")
        logger.warning(f"⚠️ Limite de {max_iterations} itérations atteinte")
        _log_final_stats(stats, verbose, warning=True)
        logger.info("🔄 Appel final sans outils pour obtenir une réponse")

    # Dernier appel sans outils pour forcer une réponse du LLM
    final_response = client.chat.completions.create(
        model=model,
        messages=current_messages,
    )

    final_content = final_response.choices[0].message.content or (
        "La limite d'itérations a été atteinte. "
        "Voici les dernières informations obtenues :\n\n"
        + json.dumps(current_messages[-1], ensure_ascii=False, indent=2)
    )

    return (final_content, stats) if return_stats else final_content

# Afficher les statistiques finales
def _log_final_stats(stats: Dict[str, Any], verbose: bool, warning: bool = False) -> None:

    if not verbose:
        return
        
    log_func = logger.warning if warning else logger.info
    
    log_func(f"\n{'='*80}")
    log_func("📊 STATISTIQUES DE FIN DE TRAITEMENT")
    log_func(f"{'='*80}")
    log_func(f"   Itérations utilisées: {stats['iterations']}/{stats['max_iterations']}")
    log_func(f"   Appels d'outils: {stats['tool_calls']}")
    log_func(f"   Succès: {stats['successful_calls']}")
    log_func(f"   Échecs: {stats['failed_calls']}")
    log_func(f"   Outils utilisés: {stats['tools_used']}")
    log_func(f"{'='*80}\n")
