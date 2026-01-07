# ForecastIQ – Smart Sales Prediction Assistant

## Overview

ForecastIQ is an AI-powered sales forecasting application designed to enhance sales planning and business decision-making. It integrates statistical time-series forecasting with conversational AI, allowing users to generate forecasts from historical data and interact with insights using natural language.

The application is built to serve both technical and non-technical users through an intuitive web interface.

---

## Problem Statement

Traditional sales forecasting and reporting approaches suffer from multiple challenges:

- Manual and time-consuming spreadsheet-based workflows  
- Static dashboards with limited analytical depth  
- High technical complexity in building and interpreting forecasting models  
- Lack of interactive and conversational data exploration  

ForecastIQ solves these issues by combining automated forecasting with AI-driven conversational insights.

---

## Key Features

- Automated sales forecasting using SARIMA  
- Automatic model selection based on accuracy metrics (MAPE)  
- Natural language question answering on forecasted data  
- Retrieval-Augmented Generation (RAG) using business knowledge  
- Interactive visualizations of historical and forecasted trends  
- Context-aware multi-turn conversations with memory  

---

## High-Level Architecture

ForecastIQ follows a modular and scalable architecture consisting of the following layers:

### User Interaction Layer
- Streamlit-based web application
- Supports Excel upload, visualization, and chat interaction

### Forecasting and Analytics Layer
- SARIMA model implemented using statsmodels
- Automatic parameter tuning for optimal accuracy
- Generates forecast plots and performance metrics

### AI and Knowledge Layer
- Azure OpenAI (GPT-3.5 Turbo) for conversational intelligence
- Azure Cognitive Search for knowledge retrieval (RAG)
- Enables contextual and factual responses

### Integration and Deployment Layer
- Azure OpenAI Service
- Azure Cognitive Search
- Azure Blob Storage
- Python backend using Streamlit and LangChain

---

## End-to-End Workflow

1. User uploads an Excel file containing historical sales data  
2. Data is preprocessed and passed to the SARIMA forecasting pipeline  
3. Forecasted values are generated and evaluated  
4. Key insights are indexed into Azure Cognitive Search  
5. User queries are processed using Azure OpenAI with retrieved context  
6. Forecasts and AI-generated insights are displayed in the UI  

---

## Technology Stack

- Frontend: Streamlit (Python)  
- Forecasting Model: SARIMA (statsmodels)  
- AI Assistant: Azure OpenAI (GPT-3.5 Turbo)  
- Knowledge Retrieval: Azure Cognitive Search  
- Data Handling: Pandas, JSON  
- Storage: Azure Blob Storage  
- Hosting: Local / Streamlit Cloud / Azure  

---

## Azure Services Used

### Azure OpenAI
- Powers the conversational AI assistant
- Enables natural language understanding and contextual responses
- Provides enterprise-grade security and scalability

### Azure Blob Storage
- Stores uploaded Excel datasets
- Ensures persistence and reproducibility of forecasts
- Supports future scalability

### Azure Cognitive Search
- Acts as the knowledge base for RAG
- Indexes structured and unstructured business data
- Improves factual accuracy of AI responses

---

## Application Workflow

### Dataset Upload
- User uploads historical sales data in Excel format

### Forecast Generation
- SARIMA parameters are automatically selected
- Forecasts generated based on accuracy metrics

### Knowledge Base Indexing
- Processed data and insights indexed into Azure Cognitive Search

### Query Handling
- Relevant context retrieved from search index
- GPT model generates a grounded response

### User Interaction
- Forecast plots displayed
- Chat interface supports follow-up questions and comparisons

---

## Testing and Validation

- Unit testing for forecasting and preprocessing logic  
- Integration testing across upload, forecast, and chat pipeline  
- System testing for end-to-end stability  
- User acceptance testing with sample business datasets  

---

## Cost Analysis

- Azure OpenAI (GPT-3.5 Turbo): Rs 3.69  
- Azure Blob Storage: Rs 0.48  
- Azure Cognitive Search: Free tier  

Total development and testing cost: Rs 4.17

---

## Future Enhancements

- Automatic selection among multiple forecasting models  
- Persistent and shareable chat sessions  
- Full deployment using Azure App Service  
- Semantic and vector-based search indexing  
- Batch ingestion and scheduled data pipelines  

---

## How to Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
