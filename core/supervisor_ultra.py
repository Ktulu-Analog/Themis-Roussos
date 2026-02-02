###############################################################
# Superviseur pour mix LLM/RAG (pas fonctionnel, posé là
# comme post-it.
# v0.1
###############################################################

from openai import OpenAI


SUPERVISOR_PROMPT = """
Tu es un superviseur juridique expert.

Ton rôle est de décider COMMENT répondre,
pas de répondre.

Analyse la question et produis un PLAN D'OUTILS.

Réponds UNIQUEMENT en JSON :

{
 "strategy": "single_tool | multi_tool | chrono | definition | deep_search",
 "priority_tools": [],
 "reasoning_depth": "low | medium | high",
 "need_timeline": true/false
}

Règles :

- chrono → si évolution du droit
- definition → si concept juridique
- deep_search → si incertitude
- multi_tool → si plusieurs codes probables
- single_tool → si article évident
"""


def build_supervisor(client: OpenAI, model: str):

    def supervisor_decide(user_query: str):

        response = client.chat.completions.create(
            model=model,
            temperature=0,
            messages=[
                {"role": "system", "content": SUPERVISOR_PROMPT},
                {"role": "user", "content": user_query},
            ],
        )

        return response.choices[0].message.content

    return supervisor_decide
