import sys
import os
import re
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from dotenv import load_dotenv
load_dotenv()

import aqxle
from datasets.load_data import load_tables_from_excel, get_options  

CACHE_PATH = "enriched_metadata.json"

# Load all tables and structured options
all_tables = load_tables_from_excel('datasets/W48Tables_Cleaned.xlsx')
options_dict = get_options(all_tables)  

# Read prompt templates
selector_prompt_path = "src/prompts/table_selector.txt"
codegen_prompt_path = "src/prompts/code_generator.txt"
contextgen_prompt_path = "src/prompts/context_generator.txt"

with open(selector_prompt_path, "r", encoding="utf-8") as f:
    table_selector_template = f.read()
with open(codegen_prompt_path, "r", encoding="utf-8") as f:
    codegen_template = f.read()
with open(contextgen_prompt_path, "r", encoding="utf-8") as f:
    contextgen_template = f.read()

# Try to load enriched metadata from cache
if os.path.exists(CACHE_PATH):
    print(f"Loading enriched metadata from {CACHE_PATH}...")
    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        options_dict = json.load(f)
else:
    print("Generating table context (keywords and summaries)...")
    # Build tables_metadata string for context generator
    all_tables_metadata = []
    for table_name, meta in options_dict.items():
        columns = ', '.join(meta['columns'])
        rows = ', '.join(meta['rows'])
        all_tables_metadata.append(f"Table Name: {table_name}\nColumns: {columns}\nRows: {rows}")
    tables_metadata_str = '\n\n'.join(all_tables_metadata)

    contextgen_prompt = contextgen_template.replace("{{tables_metadata}}", tables_metadata_str)

    # Initialize LLM system
    aqxle.init("config.yml")

    # Run context generator LLM ONCE for all tables
    with aqxle.params(name="contextgen", history_length=3, max_retries=2, logging=True) as contextgen_session:
        contextgen_result = (
            contextgen_session
            .llm("context_generator_llm", message=contextgen_prompt)
        )

    # Parse contextgen_result to extract keywords and summary for each table
    context_output = contextgen_result.data
    # Simple parser for the expected output format
    context_blocks = re.split(r"Table Name: ", context_output)
    for block in context_blocks:
        if not block.strip():
            continue
        lines = block.strip().splitlines()
        table_name = lines[0].strip()
        keywords = []
        summary = ""
        for line in lines[1:]:
            if line.startswith("keywords:"):
                # Extract list from [ ... ]
                kw_match = re.search(r'\[(.*?)\]', line)
                if kw_match:
                    keywords = [k.strip().strip('"\'') for k in kw_match.group(1).split(',') if k.strip()]
            elif line.startswith("summary:"):
                summary = line[len("summary:"):].strip()
        # Append to options_dict
        if table_name in options_dict:
            options_dict[table_name]["keywords"] = keywords
            options_dict[table_name]["summary"] = summary
    # Save enriched metadata to cache
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(options_dict, f, indent=2)
    print(f"Enriched metadata saved to {CACHE_PATH}.")

# Get user question
question = input("Ask a question about your data: ")

# Convert enriched options dict to string for prompt 
options_str = json.dumps(options_dict, indent=2)
selector_prompt = table_selector_template.replace("{{options}}", options_str).replace("{{question}}", question)

# Initialize LLM system (if not already done)
try:
    aqxle.init("config.yml")
except Exception:
    pass

# Run table selector LLM
with aqxle.params(name="table_selector", history_length=3, max_retries=2, logging=True) as selector_session:
    selector_result = (
        selector_session
        .llm("table_selector_llm", message=selector_prompt)
    )

# Debug: print LLM output
print("LLM raw output:", repr(selector_result.data))

selected_table = selector_result.data.strip()
selected_table = selected_table.strip('\'"')

# Try exact match first
if selected_table in all_tables:
    matched_table = selected_table
else:
    matches = [k for k in all_tables if selected_table.lower() == k.lower()]
    if len(matches) == 1:
        matched_table = matches[0]
    else:
        print("No relevant tables found by the Table Selector LLM. Please refine your question.")
        exit(1)

# Prepare full metadata for codegen from selected table
full_meta = options_dict.get(matched_table)
if not full_meta:
    print("Selected table metadata not found. Something went wrong.")
    exit(1)

metadata_str = f"Table: {matched_table}\nColumns: {', '.join(full_meta['columns'])}\nRows: {', '.join(full_meta['rows'])}\nKeywords: {', '.join(full_meta.get('keywords', []))}\nSummary: {full_meta.get('summary', '')}"
codegen_prompt = codegen_template.replace("{{table_metadata}}", metadata_str).replace("{{question}}", question)

# Run code generation and execution
with aqxle.params(name="logicgen", history_length=5, max_retries=3, logging=True) as session:
    result = (
        session
        .llm("codegen_llm", message=codegen_prompt)
        .segment(kernel="python")
        .execute(kernel="python", function="main", df={matched_table: all_tables[matched_table]})
    )

print(result.data.output)
print(result.data.error)
