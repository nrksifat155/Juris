import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from prompts import ACTIVE_PROMPT, ALL_PROMPTS


# ─────────────────────────────────────────────
# 1. ENV LOAD
# ─────────────────────────────────────────────
load_dotenv()

API_KEY  = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
MODEL    = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")

if not API_KEY:
    st.error("❌ OPENROUTER_API_KEY not found. Please check your .env file.")
    st.stop()

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)


# ─────────────────────────────────────────────
# 2. PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="",
    page_icon="⚖️",
    layout="centered",
)
st.title("⚖️JurisAI: Criminal Law RAG Framework")
st.caption("Ask in English • বাংলা • Banglish")


# ─────────────────────────────────────────────
# 3. SESSION STATE
# ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []


# ─────────────────────────────────────────────
# 4. SIDEBAR — Prompt selector + controls
# ─────────────────────────────────────────────
with st.sidebar:
    st.header("🎛️ Prompt Control")

    default_name = next(
        (name for name, txt in ALL_PROMPTS.items() if txt == ACTIVE_PROMPT),
        list(ALL_PROMPTS.keys())[0],
    )

    selected_name = st.selectbox(
        "Prompt version",
        options=list(ALL_PROMPTS.keys()),
        index=list(ALL_PROMPTS.keys()).index(default_name),
    )

    use_custom = st.checkbox("✍️ Write custom prompt")
    if use_custom:
        system_prompt = st.text_area(
            "Custom system prompt",
            value=ALL_PROMPTS[selected_name],
            height=320,
        )
    else:
        system_prompt = ALL_PROMPTS[selected_name]

    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.3,
        step=0.1,
        help="Lower = more precise, higher = more creative",
    )

    with st.expander("👀 View active prompt"):
        st.code(system_prompt, language="text")

    st.divider()

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.caption(f"Provider: OpenRouter\n\nModel: `{MODEL}`")


# ─────────────────────────────────────────────
# 5. RENDER CHAT HISTORY
# ─────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ─────────────────────────────────────────────
# 6. CHAT INPUT + RESPONSE
#    👇 Placeholder: English / বাংলা / Banglish
# ─────────────────────────────────────────────
user_input = st.chat_input(
    "Ask in English, বাংলা, or Banglish... (e.g. 'varatia ke evict korbo kivabe?')"
)

if user_input:
    # user message সংরক্ষণ + দেখানো
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # payload তৈরি (system prompt + সম্পূর্ণ history)
    payload = [{"role": "system", "content": system_prompt}] + st.session_state.messages

    # assistant response (streaming)
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        try:
            stream = client.chat.completions.create(
                model=MODEL,
                messages=payload,
                temperature=temperature,
                stream=True,
            )

            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                full_response += delta
                placeholder.markdown(full_response + "▌")

            placeholder.markdown(full_response)

        except Exception as e:
            full_response = f"❌ Error: {e}"
            placeholder.error(full_response)

    # assistant message সংরক্ষণ
    st.session_state.messages.append(
        {"role": "assistant", "content": full_response}
    )