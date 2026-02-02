###############################################################################
# Thémis Roussos - Interface de production
###############################################################################

import os
import streamlit as st
import yaml
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

from tools import chat_with_tools
from utils.docx_export import create_response_docx

# TIMELINE
from timeline_ultra import (
    TimelineUltra,
    render_timeline_ultra,
    extract_events_silently,
)

from conversation_manager import ConversationManager
from utils.conversation_naming import (
    generate_conversation_name,
    should_generate_name,
)

# SYNTHÈSE
from utils.conversation_synthesis import (
    generate_conversation_synthesis,
    estimate_synthesis_length,
)

# GESTION DU CONTEXTE
from utils.context_manager import (
    smart_truncate_conversation,
    check_context_before_call,
    get_model_limits,
)

# -----------------------------------------------------------------------------
# ENV
# -----------------------------------------------------------------------------

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
EXTRACTION_MODEL = os.getenv("EXTRACTION_MODEL")
SYNTHESIS_MODEL = os.getenv("SYNTHESIS_MODEL", OPENAI_MODEL)  # Fallback au modèle principal

if not all([OPENAI_API_KEY, OPENAI_BASE_URL]):
    st.error("Configuration incomplète - Vérifiez votre fichier .env")
    st.stop()

client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
)

# -----------------------------------------------------------------------------
# SYSTEM PROMPT
# -----------------------------------------------------------------------------

def load_system_prompt() -> str:
    try:
        with open("prompt.yml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f).get("system_prompt", "")
    except Exception:
        return ""

SYSTEM_PROMPT = load_system_prompt()

# -----------------------------------------------------------------------------
# PAGE
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="Thémis Roussos",
    page_icon="⚖️",
    layout="wide",
)

st.title("⚖️ Thémis Roussos")
st.caption("Assistant juridique alimenté par Légifrance")

# -----------------------------------------------------------------------------
# SESSION STATE INIT
# -----------------------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_manager" not in st.session_state:
    st.session_state.conversation_manager = ConversationManager()

if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = (
        st.session_state.conversation_manager.create_conversation()
    )

if "timeline_ultra" not in st.session_state:
    st.session_state.timeline_ultra = TimelineUltra(
        conversation_id=st.session_state.current_conversation_id
    )

# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------

with st.sidebar:

    # Configuration
    st.header("⚙️ Configuration")

    max_iterations = st.slider(
        "Limite d'itérations",
        min_value=10,
        max_value=40,
        value=15,
        help="Nombre maximum d'appels d'outils par question"
    )

    st.divider()

    # Conversations
    st.header("💬 Conversations")

    if st.button("➕ Nouvelle conversation", use_container_width=True):
        new_id = st.session_state.conversation_manager.create_conversation()
        st.session_state.current_conversation_id = new_id
        st.session_state.messages = []
        st.session_state.timeline_ultra = TimelineUltra(conversation_id=new_id)
        st.rerun()

    st.divider()

    conversations = st.session_state.conversation_manager.list_conversations()

    if conversations:
        st.caption(f"{len(conversations)} conversation(s)")

    for conv in conversations[:10]:
        is_active = conv["id"] == st.session_state.current_conversation_id

        with st.expander(
            f"{'🔵' if is_active else '⚪'} {conv['name'][:35]}...",
            expanded=is_active,
        ):
            st.caption(f"📅 {conv['updated_at'][:10]}")
            st.caption(
                f"💬 {conv['message_count']} msg • 📊 {conv['event_count']} evt"
            )

            col1, col2 = st.columns(2)

            with col1:
                if not is_active:
                    if st.button(
                        "Ouvrir",
                        key=f"open_{conv['id']}",
                        use_container_width=True,
                    ):
                        st.session_state.current_conversation_id = conv["id"]
                        data = (
                            st.session_state.conversation_manager
                            .get_conversation(conv["id"])
                        )
                        if data:
                            st.session_state.messages = data["messages"]

                        st.session_state.timeline_ultra = TimelineUltra(
                            conversation_id=conv["id"]
                        )
                        st.rerun()

            with col2:
                if st.button(
                    "🗑️",
                    key=f"del_{conv['id']}",
                    use_container_width=True,
                ):
                    if st.session_state.conversation_manager.delete_conversation(
                        conv["id"]
                    ):
                        if is_active:
                            new_id = (
                                st.session_state.conversation_manager
                                .create_conversation()
                            )
                            st.session_state.current_conversation_id = new_id
                            st.session_state.messages = []
                            st.session_state.timeline_ultra = TimelineUltra(
                                conversation_id=new_id
                            )
                        st.rerun()

            # Bouton Synthèse pour chaque conversation
            if conv["message_count"] >= 2:
                st.divider()

                # Afficher estimation
                conv_data = st.session_state.conversation_manager.get_conversation(conv["id"])
                if conv_data:
                    estimation = estimate_synthesis_length(conv_data["messages"])
                    st.caption(f"📝 {estimation}")

                if st.button(
                    "📋 Générer synthèse",
                    key=f"synth_{conv['id']}",
                    use_container_width=True,
                    type="secondary",
                ):
                    # Charger la conversation
                    conv_data = st.session_state.conversation_manager.get_conversation(conv["id"])

                    if conv_data and conv_data["messages"]:
                        with st.spinner("🔍 Génération de la synthèse en cours..."):
                            try:
                                # Générer la synthèse
                                synthesis = generate_conversation_synthesis(
                                    client=client,
                                    model=SYNTHESIS_MODEL,
                                    messages=conv_data["messages"],
                                    conversation_name=conv["name"]
                                )

                                # Exporter en DOCX
                                buffer = create_response_docx(
                                    question=f"Synthèse - {conv['name']}",
                                    response=synthesis,
                                    metadata={
                                        "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                        "model": SYNTHESIS_MODEL,
                                        "conversation_id": conv["id"],
                                        "message_count": conv["message_count"],
                                    },
                                )

                                # Télécharger
                                st.download_button(
                                    "⬇️ Télécharger la synthèse (DOCX)",
                                    data=buffer,
                                    file_name=f"synthese_{conv['id']}_{datetime.now():%Y%m%d_%H%M%S}.docx",
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    key=f"download_synth_{conv['id']}",
                                )

                                st.success("✅ Synthèse générée avec succès !")

                            except Exception as e:
                                st.error(f"❌ Erreur lors de la génération : {str(e)}")
                    else:
                        st.warning("⚠️ Impossible de charger la conversation")

    st.divider()

    # Actions
    st.header("⚙️ Actions")

    if st.button("🔄 Réinitialiser conversation", use_container_width=True):
        st.session_state.messages = []
        if "timeline_ultra" in st.session_state:
            st.session_state.timeline_ultra.clear()
        st.rerun()

    if st.button(
        "🗑️ Effacer timeline",
        use_container_width=True,
        type="secondary",
    ):
        if "timeline_ultra" in st.session_state:
            st.session_state.timeline_ultra.clear()
            if st.session_state.timeline_ultra.memory:
                st.session_state.timeline_ultra.memory.clear_all()
        st.rerun()

# -----------------------------------------------------------------------------
# TIMELINE
# -----------------------------------------------------------------------------

render_timeline_ultra(st.session_state.timeline_ultra)
st.divider()

# -----------------------------------------------------------------------------
# AFFICHAGE CONVERSATION
# -----------------------------------------------------------------------------

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------------------------------------------------------------
# INPUT USER
# -----------------------------------------------------------------------------

if prompt := st.chat_input("Posez votre question juridique…"):

    st.session_state.messages.append({"role": "user", "content": prompt})

    st.session_state.conversation_manager.add_message(
        st.session_state.current_conversation_id,
        {"role": "user", "content": prompt}
    )

    with st.chat_message("assistant"):
        with st.spinner("🔍 Analyse en cours…"):
            try:
                # Préparer les messages avec le prompt système
                messages_to_send = [{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.messages

                # Obtenir les limites du modèle
                model_limits = get_model_limits(OPENAI_MODEL)

                # Tronquer intelligemment si nécessaire
                messages_to_send = smart_truncate_conversation(
                    messages_to_send,
                    max_tokens=model_limits["max_tokens"],
                    response_buffer=model_limits["response_buffer"],
                    keep_recent=8  # Garder les 8 derniers messages
                )

                # Vérification finale avant l'appel
                is_ok, tokens, check_msg = check_context_before_call(
                    messages_to_send,
                    model_max_tokens=model_limits["max_tokens"],
                    response_buffer=model_limits["response_buffer"]
                )

                if not is_ok:
                    st.error(check_msg)
                    st.error("⚠️ La conversation est trop longue. Créez une nouvelle conversation pour continuer.")
                    st.stop()

                # Appeler l'API
                response = chat_with_tools(
                    messages=messages_to_send,
                    client=client,
                    model=OPENAI_MODEL,
                    max_iterations=max_iterations,
                )

                st.markdown(response)

                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )

                st.session_state.conversation_manager.add_message(
                    st.session_state.current_conversation_id,
                    {"role": "assistant", "content": response}
                )

                # Extraction timeline
                events = extract_events_silently(
                    client=client,
                    model=OPENAI_MODEL,
                    response_text=response,
                    extraction_model=EXTRACTION_MODEL,
                )

                if events:
                    new_count = len(
                        st.session_state.timeline_ultra.ingest_llm_events(events)
                    )
                    if new_count > 0:
                        st.session_state.conversation_manager.update_event_count(
                            st.session_state.current_conversation_id,
                            len(st.session_state.timeline_ultra.events),
                        )

                # Génération automatique du nom
                conv = st.session_state.conversation_manager.get_conversation(
                    st.session_state.current_conversation_id
                )

                if conv and should_generate_name(
                    st.session_state.messages, conv["metadata"]["name"]
                ):
                    name = generate_conversation_name(
                        client=client,
                        model=EXTRACTION_MODEL or OPENAI_MODEL,
                        messages=st.session_state.messages,
                    )
                    st.session_state.conversation_manager.update_conversation_name(
                        st.session_state.current_conversation_id,
                        name,
                    )

                st.rerun()

            except Exception as e:
                st.error("❌ Une erreur est survenue lors de l'analyse")
                st.error(str(e))

                # Si c'est une erreur de contexte, donner plus d'infos
                if "max_tokens" in str(e).lower():
                    st.info("💡 Conseil : La conversation est trop longue. Créez une nouvelle conversation pour continuer.")

# -----------------------------------------------------------------------------
# EXPORT DOCX
# -----------------------------------------------------------------------------

if st.session_state.messages:
    st.divider()

    if st.button("📄 Exporter la conversation (DOCX)"):
        conversation = ""
        for msg in st.session_state.messages:
            role = "Question" if msg["role"] == "user" else "Réponse"
            conversation += f"## {role}\n\n{msg['content']}\n\n"

        buffer = create_response_docx(
            question="Conversation juridique",
            response=conversation,
            metadata={
                "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "model": OPENAI_MODEL,
            },
        )

        st.download_button(
            "⬇️ Télécharger le DOCX",
            data=buffer,
            file_name=f"conversation_{datetime.now():%Y%m%d_%H%M%S}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

# -----------------------------------------------------------------------------
# FOOTER
# -----------------------------------------------------------------------------

st.divider()

col1, col2 = st.columns(2)
col1.caption("⚖️ Données officielles Légifrance")
col2.caption("⚠️ Contenu généré par une IA — Vérifiez les réponses")
