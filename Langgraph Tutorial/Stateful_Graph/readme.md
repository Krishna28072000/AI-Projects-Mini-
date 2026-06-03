# Stateful_Graph

This folder contains a simple LangGraph classifier workflow implemented in a Jupyter notebook.

## What it does

- Uses `langgraph.graph.StateGraph` to build a linear stateful pipeline.
- Defines three processing nodes:
  - `classification_node`: classifies user text into Billing, Technical, or General categories.
  - `entity_recognition_node`: extracts entities such as Response, Troubleshoot, or FAQ from the same input.
  - `summarization_node`: summarizes the user text in one or two sentences.
- Uses `langchain_openai.ChatOpenAI` with `gpt-4.1-mini` for inference.
- Visualizes the state graph using Mermaid and displays it in the notebook.

## Usage

1. Install the required dependencies.
2. Set `OPENAI_API_KEY` in the environment or a `.env` file.
3. Open and run `classifier.ipynb`.
4. Provide text input via the sample state or modify the notebook to pass your own text.

## Example

The notebook includes a sample input to classify an internet connectivity issue, identify the relevant entity type, and create a short summary.

## Purpose

This notebook demonstrates how to connect OpenAI prompt-based tasks in a stateful workflow, enabling sequential text processing and graph-based orchestration within a Python notebook.
