import os
import re
import json
import uuid
import warnings
import requests
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from datetime import datetime
from dateutil.relativedelta import relativedelta
from statsmodels.tsa.statespace.sarimax import SARIMAX
from langchain.chat_models import AzureChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
warnings.filterwarnings("ignore")
from rag_test_app import (
   has_business_keyword,
   is_multiple_rag_query,
   extract_top_n,
   simple_rag_search,
   build_search_query,
   search_ai
)
st.set_page_config(page_title="📊 ForecastIQ", page_icon="📈", layout="centered")
# -------------------- Styling --------------------
st.markdown("""
<style>
body, .main, .block-container {
    background-color: #0b1f3a !important;
    color: #ffffff;
}

.chat-container {
    display: flex;
    flex-direction: column;
    gap: 10px;
    max-height: 600px;
    overflow-y: auto;
    padding: 0px;
    border-radius: 10px;
    background-color: #0b1f3a;
    box-shadow: 0 2px 10px rgba(255,255,255,0.1);
}

.chat-message {
    padding: 12px 20px;
    margin: 5px 0;
    border-radius: 10px;
    font-size: 16px;
    line-height: 1.5;
    max-width: 70%;
    display: inline-block;
    word-wrap: break-word;
    box-shadow: 2px 2px 10px rgba(255,255,255,0.2);
}

.chat-message.user {
    background-color: #DCF8C6;
    color: #1a1a1a;
    align-self: flex-end;
    margin-left: auto;
    text-align: left;
}

.chat-message.assistant {
    background-color: #F1F0F0;
    color: #1a1a1a;
    align-self: flex-start;
    margin-right: auto;
    text-align: left;
}

h1, h2, h3, .stSelectbox label, .stFileUploader label {
    background-color: #f0f8ff;
    color: #1a1a1a !important;
    padding: 10px 15px;
    margin: 10px 0px;
    border-radius: 10px;
    box-shadow: 2px 2px 8px rgba(255, 255, 255, 0.3);
    display: inline-block;
    margin-bottom: 15px;
}

footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

st.title("📊 ForecastIQ – Smart Sales Prediction Assistant")
# -------------------- Session State --------------------
if "chat_history" not in st.session_state:
   st.session_state.chat_history = []
if "is_thinking" not in st.session_state:
   st.session_state.is_thinking = False
if "last_input" not in st.session_state:
   st.session_state.last_input = ""
if "forecast_intro" not in st.session_state:
   st.session_state.forecast_intro = ""
if "forecast_loaded" not in st.session_state:
   st.session_state.forecast_loaded = False
# -------------------- Azure Config --------------------
os.environ["OPENAI_API_TYPE"] = "azure"
os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""
os.environ["OPENAI_API_VERSION"] ="2024-12-01-preview"

llm = AzureChatOpenAI(
   deployment_name="gpt-35-turbo",
   temperature=0.7,
   max_tokens=500
)
# -------------------- File Upload --------------------
uploaded_file = st.file_uploader("📁 Upload Excel File (Month & Sales Qty)", type=["xlsx"])
horizon = st.selectbox("⏳ Forecast Horizon (months)", [12, 6, 3])
if uploaded_file:
   try:
       df = pd.read_excel(uploaded_file, engine="openpyxl")
       df = df.rename(columns={"Month": "date", "Sales Qty": "value"})
       df["date"] = pd.to_datetime(df["date"], format="%b-%y")
       df = df.sort_values("date").set_index("date")
       model = SARIMAX(df["value"], order=(1, 0, 0), seasonal_order=(2, 0, 2, 12),
                       enforce_stationarity=False, enforce_invertibility=False)
       model_fit = model.fit()
       forecast = model_fit.forecast(steps=horizon)
       last_date = df.index[-1]
       future_dates = [last_date + relativedelta(months=i) for i in range(1, horizon + 1)]
       forecast_df = pd.DataFrame({"Forecast": forecast}, index=future_dates)
       forecast_json = [{"month": i.strftime("%b-%Y"), "sales": int(v)} for i, v in forecast_df["Forecast"].items()]
       st.session_state.forecast_intro = f"""
You are a precise forecasting/Historical assistant. Use the SARIMA forecast data provided below and, when available, the historical context provided at answer time.
✅ DO:
- Answer based only on the forecast data and the historical data 
- Follow up accurately using past messages
❌ DO NOT:
- Hallucinate or invent values
SARIMA Forecast:
{json.dumps(forecast_json, indent=2)}
"""
       # Plot
       st.subheader("📈 Forecast Plot")
       with st.container():
        st.markdown("""
        <div style="background-color: #f0f8ff; padding: 0px; border-radius: 0px; box-shadow: 2px 2px 8px rgba(255, 255, 255, 0.3); max-width: 900px; margin: auto;">
        """, unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(df.index, df["value"], label="Actual", color="#1a2b4c")
        ax.plot(forecast_df.index, forecast_df["Forecast"], label="Forecast", linestyle="--", color="#2c7fb8")
        ax.set_title("SARIMA Sales Forecast", color="#1a2b4c")
        ax.set_xlabel("Month")
        ax.set_ylabel("Sales Qty")
        ax.legend()
        ax.grid(True)
        fig.patch.set_facecolor("#ffffff")
        st.pyplot(fig)
        st.markdown("</div>", unsafe_allow_html=True)
   except Exception as e:
       st.error(f"❌ Error: {e}")
# -------------------- Chat Display --------------------
st.subheader("💬  Chat")
with st.container():
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for role, msg in st.session_state.chat_history:
               css_class = "user" if role == "user" else "assistant"
               st.markdown(f'<div class="chat-message {css_class}">{msg}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------- Input & Thinking Logic --------------------
# === Sidebar toggle for chat context ===
if uploaded_file:
   chat_mode = st.sidebar.radio(
       "Choose Chat Context:",
       ["Forecast", "Historical", "Both"],
       index=2
   )
else:
   chat_mode = st.sidebar.radio(
       "Choose Chat Context:",
       ["Historical"],  # Only historical available if no file
       index=0
   )
if not st.session_state.is_thinking:
   col1, col2 = st.columns([6, 1])
   user_input=None
   with col1:
       user_input = st.chat_input("Ask about forecast, historical data, or both:")
   with col2:
       st.empty()
else:
   col1, col2 = st.columns([6, 1])
   with col1:
       st.chat_input(disabled=True, placeholder="Waiting for response...")
   with col2:
       if st.button("❌ Cancel"):
           st.session_state.is_thinking = False
           st.stop()
if not st.session_state.is_thinking and "user_input" in locals() and user_input:
   st.session_state.chat_history.append(("user", user_input))
   st.session_state.last_input = user_input
   st.session_state.is_thinking = True
   st.rerun()
elif st.session_state.is_thinking and st.session_state.last_input:
   # === Retrieve historical context via RAG (only if mode requires it) ===
   try:
       if chat_mode in ["Historical", "Both"]:
           if has_business_keyword(st.session_state.last_input) and not is_multiple_rag_query(st.session_state.last_input):
               _query_json = build_search_query(st.session_state.last_input)
               _rag_contexts = search_ai(_query_json)
           else:
               _rag_contexts = simple_rag_search(st.session_state.last_input)
       else:
           _rag_contexts = []  # Forecast-only mode: skip RAG
   except Exception as _e:
       _rag_contexts = []
   # === Build historical block based on mode ===
   if chat_mode in ["Historical", "Both"]:
       _historical_block = 'Historical Context:\n' + ('\n'.join(_rag_contexts) if _rag_contexts else 'No historical data found.')
   else:
       _historical_block = ''
   # === Build forecast block based on mode (only if file uploaded) ===
   if uploaded_file and chat_mode in ["Forecast", "Both"]:
       _forecast_block = (st.session_state.forecast_intro or '')
   elif not uploaded_file and chat_mode in ["Forecast", "Both"]:
       st.warning("⚠️ No forecast data available. Please upload a file to access forecast chat.")
       _forecast_block = ''
   else:
       _forecast_block = ''
   # === Final system content ===
   _system_content = _forecast_block
   if _historical_block:
       _system_content += '\n\n' + _historical_block + '\n\n'
   if chat_mode == "Both":
       _system_content += 'Use both the SARIMA forecast data and (if present) the historical context above to answer. Be concise and factual.'
   elif chat_mode == "Forecast":
       _system_content += 'Use only the SARIMA forecast data to answer. Be concise and factual.'
   elif chat_mode == "Historical":
       _system_content += 'Use only the historical context above to answer. Be concise and factual.'
   # === Build full context ===
   full_context = [SystemMessage(content=_system_content)]
   for role, msg in st.session_state.chat_history:
       if role == 'user':
           full_context.append(HumanMessage(content=msg))
       else:
           full_context.append(AIMessage(content=msg))
   # === Call LLM ===
   with st.spinner("Thinking..."):
       reply = llm(full_context)
       st.session_state.chat_history.append(("assistant", reply.content))
       st.session_state.last_input = ""
       st.session_state.is_thinking = False
   st.rerun()    
# -------------------- Footer --------------------
st.markdown("""
---
<p style="text-align:center; color: grey; font-size: 0.9em;">
© 2025 Lakshaant | ForecastIQ – Built with ❤️ using Streamlit & Azure OpenAI
</p>
""", unsafe_allow_html=True)