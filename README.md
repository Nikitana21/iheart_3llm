# iHeart 3LLMs

## Overview

This project enables users to ask questions about survey data stored in Excel tables. The system uses three Large Language Models (LLMs) via Aqxle: one to enrich table metadata with keywords and summary (context llm), one to select the most relevant table, and another to generate Python code to answer the question using only the selected table's data. The project includes a command-line demo (`demo.py`).

---

## Workflow 

1. **Configuration and Setup:**  
   Loads configuration from `config.yml`, API keys from `.env`, and initializes the environment.

2. **Table Loading:**  
   Loads all tables from the Excel file (`datasets/W48Tables_Cleaned.xlsx`) and extracts their metadata (column names and categories) using helpers in `datasets/load_data.py`.

3. **Metadata Enrichment:**  
   If not already cached in `enriched_metadata.json`, the system uses an LLM (via the context generator prompt in `src/prompts/context_generator.txt`) to generate keywords and summaries for each table. The enriched metadata is cached for future runs.

4. **User Question:**  
   The user is prompted in the terminal to enter a question about the data.

5. **Table Selection Prompt Construction:**  
   The system inserts the user question and the enriched metadata into the table selector prompt (`src/prompts/table_selector.txt`).

6. **Table Selection (LLM):**  
   The table selector LLM receives the prompt and returns the name of the most relevant table.

7. **Code Generation Prompt Construction:**  
   The system builds a prompt for the code generator LLM (`src/prompts/code_generator.txt`), including the selected table's metadata and the user question.

8. **Code Generation and Execution (LLM):**  
   The code generator LLM returns a Python function, which is executed on the selected table's DataFrame. The result (and any error) is displayed in the terminal.

---

## Setup Instructions

1. **Clone the repository and navigate to the project directory.**

2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

3. **Configure your API keys and dataset path in `config.yml` and `.env`.**

4. **Run the command-line demo:**
   ```sh
   python demo.py
   ```

---

## File Structure

- `demo.py` — Command-line script for Q&A with LLM-powered table selection and code generation
- `datasets/load_data.py` — Helper for extracting tables and metadata from Excel
- `src/prompts/` — Prompt templates for the LLMs (context generator, table selector, code generator)
- `config.yml` — Configuration file (API keys, dataset path, etc.)
- `.env` — Environment variables (not tracked in git)
- `enriched_metadata.json` — Cached enriched metadata for tables
- `README.md` — Project documentation
- `.gitignore` — Files and folders excluded from version control

---

## Notes

- Ensure your Excel data is formatted with clear table titles and a 'Category' column for row labels.
- If you use a virtual environment, activate it before installing dependencies.
- If `aqxle` is a private package, ensure it is installed in your environment.
- The demo script will cache enriched metadata after the first run to speed up subsequent runs.

---

## Example Usage

- Run `python demo.py` and enter a question about your data when prompted.
- The LLMs will enrich table metadata, select the most relevant table, and generate code to answer your question.
- The generated code will be executed, and the answer will be displayed using only the selected table. 