# Marketing / Business Intelligence Agent with Google ADK

![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)
![uv](https://img.shields.io/badge/uv-managed-430f8e.svg?style=flat&logo=python&logoColor=white)
![Gradio Version](https://img.shields.io/badge/gradio-6.1.0-orange.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🎓 University Project

This repository contains our university project for building a multi-agent Business Intelligence system using Google's Agent Development Kit (ADK).

The system translates natural language questions into SQL queries, executes them against a Microsoft SQL Server database, and automatically generates visualizations and explanations using Google's Gemini AI.

Repository:  
https://github.com/fabianerens/marketing-agent.git

---

## ✨ Key Features

- 🤖 Multi-agent pipeline using ADK's `SequentialAgent`
- 🌐 Dual interfaces: ADK Web + Gradio UI
- 📊 Automatic chart generation with Altair
- 💬 AI-generated business insights
- 🛠️ Tool-based agent architecture
- 🔐 SQL validation and safe query execution

---

## 🏗 Architecture Overview

The system consists of a `root_agent` orchestrating multiple sub-agents:

1. **Text-to-SQL Agent** – Converts natural language into SQL
2. **SQL Executor Agent** – Executes validated SELECT queries
3. **Data Formatter Agent** – Prepares data for visualization
4. **Insight Pipeline**
   - Visualization Agent
   - Explanation Agent

Both ADK Web and Gradio use the same agent pipeline.

---

# 🚀 Setup Instructions

## 1️⃣ Prerequisites

You need:

- Python 3.12+
- `uv` package manager
- Gemini API key
- Access to a Microsoft SQL Server database
- ODBC Driver 18 for SQL Server

Install `uv` if needed:

```bash
pip install uv
