import streamlit as st
import requests
import json
import re
from openai import AzureOpenAI
# ====== CONFIG ======
AZURE_SEARCH_ENDPOINT = ""
AZURE_SEARCH_API_KEY = ""
AZURE_SEARCH_INDEX = "azureblob-index"
AZURE_OPENAI_ENDPOINT = ""
AZURE_OPENAI_API_KEY = ""
AZURE_OPENAI_DEPLOYMENT = "gpt-35-turbo"
# ====== BUSINESS KEYWORDS ======
KEYWORD_PATTERNS = {
   "highest": {"order": "desc", "field": "SalesQty"},
   "top": {"order": "desc", "field": "SalesQty"},
   "maximum": {"order": "desc", "field": "SalesQty"},
   "max": {"order": "desc", "field": "SalesQty"},
   "largest": {"order": "desc", "field": "SalesQty"},
   "most": {"order": "desc", "field": "SalesQty"},
   "lowest": {"order": "asc", "field": "SalesQty"},
   "minimum": {"order": "asc", "field": "SalesQty"},
   "min": {"order": "asc", "field": "SalesQty"},
   "least": {"order": "asc", "field": "SalesQty"},
   "smallest": {"order": "asc", "field": "SalesQty"},
   "bottom": {"order": "asc", "field": "SalesQty"},
}
# ====== DETECTION FUNCTIONS ======
def has_business_keyword(query):
   return any(kw in query.lower() for kw in KEYWORD_PATTERNS.keys())
def is_multiple_rag_query(query):
   query_lower = query.lower()
   return (
       "compare" in query_lower
       or " vs " in query_lower
       or " and " in query_lower
       or len(re.findall(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|202\d)", query_lower)) > 0
   )
def extract_top_n(query):
   match = re.search(r"\b(?:top|highest|lowest|bottom|best|worst)\s+(\d+)", query.lower())
   return int(match.group(1)) if match else None
# ====== SIMPLE RAG ======
def simple_rag_search(query):
   url = f"{AZURE_SEARCH_ENDPOINT}/indexes/{AZURE_SEARCH_INDEX}/docs/search?api-version=2023-07-01-Preview"
   headers = {"Content-Type": "application/json", "api-key": AZURE_SEARCH_API_KEY}
   # --- detect month/year keywords ---
   months = [
       "january","february","march","april","may","june",
       "july","august","september","october","november","december"
   ]
   years = re.findall(r"\b(20\d{2})\b", query.lower())  # capture 20xx years
   month_matches = [m for m in months if m in query.lower()]
   # --- build search string ---
   keywords = month_matches + years
   if keywords:
    if len(month_matches) > 1 or len(years) > 1:
        # multiple months/years → fall back to loose search
        search_text = query          # use full query
        search_mode = "any"
    else:
        # single month/year → strict search
        search_text = " ".join(keywords)
        search_mode = "all"
   else:
    # no keywords at all → loose search
    search_text = query
    search_mode = "any"
   payload = {
       "search": search_text,
       #"top": 3,
       "searchMode": search_mode
   }
   resp = requests.post(url, headers=headers, json=payload)
   resp.raise_for_status()
   return [doc["content"] for doc in resp.json().get("value", [])]
# ====== HARDCODED QUERY BUILDER ======
def build_search_query(user_query):
   uq_lower = user_query.lower()
   for keyword, config in KEYWORD_PATTERNS.items():
       if keyword in uq_lower:
           top_n = extract_top_n(user_query) or 1
           search_query = {
               "search": "*",
               "orderby": f"{config['field']} {config['order']}",
               "top": top_n
           }
           return json.dumps(search_query)
   return None
# ====== AZURE SEARCH CALL ======
def search_ai(query_json):
   query_payload = json.loads(query_json)
   url = f"{AZURE_SEARCH_ENDPOINT}/indexes/{AZURE_SEARCH_INDEX}/docs/search?api-version=2023-07-01-Preview"
   headers = {"Content-Type": "application/json", "api-key": AZURE_SEARCH_API_KEY}
   resp = requests.post(url, headers=headers, json=query_payload)
   resp.raise_for_status()
   return [doc["content"] for doc in resp.json()["value"]]
# ====== LLM ANSWER ======
def ask_llm(question, context):
   client = AzureOpenAI(
       api_key=AZURE_OPENAI_API_KEY,
       api_version="2024-12-01-preview",
       azure_endpoint=AZURE_OPENAI_ENDPOINT
   )
   prompt = f"Answer the question based only on the context below:\n\n{context}\n\nQuestion: {question}"
   resp = client.chat.completions.create(
       model=AZURE_OPENAI_DEPLOYMENT,
       messages=[{"role": "system", "content": "You are a helpful assistant for answering historical sales questions."},
                 {"role": "user", "content": prompt}],
       temperature=0.3
   )
   return resp.choices[0].message.content
# ====== ROUTER ======
def handle_user_query(user_query):
   if has_business_keyword(user_query) and not is_multiple_rag_query(user_query):
       query_json = build_search_query(user_query)
       retrieved_contexts = search_ai(query_json)
   else:
       retrieved_contexts = simple_rag_search(user_query)
   answer = ask_llm(user_query, "\n".join(retrieved_contexts))
   return retrieved_contexts, answer
'''# ====== STREAMLIT UI ======
st.title("📊 Business Data Q&A")
user_query = st.text_input("Enter your question:")
if st.button("Search") and user_query.strip():
   with st.spinner("Processing..."):
       contexts, ans = handle_user_query(user_query)
       st.subheader("Retrieved Context")
       for c in contexts:
           st.write("-", c)
       st.subheader("LLM Answer")
       st.write(ans)'''