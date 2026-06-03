# Prompt_template

This folder contains a small example project demonstrating how to combine LangChain prompt templates with LangGraph stateful workflows.

## What it does

- `chain.py`
  - Defines two ChatPromptTemplate-based chains using `langchain_core` and `langchain_openai`.
  - `generate_chain` is configured to create a high-quality Twitter post from user input.
  - `reflection_chain` is configured to review and critique a tweet, then provide recommendations for improvement.
  - Both chains use `ChatOpenAI` as the underlying language model.

- `main.py`
  - Defines a state graph using `langgraph.graph.StateGraph`.
  - Creates `generation_node` and `reflection_node` that execute the respective LangChain chains and update the shared message state.
  - Uses a simple loop condition to alternate between generation and reflection until the conversation reaches a fixed depth.
  - Prints a Mermaid diagram and ASCII graph representation for debugging and visualization.
  - Includes a sample entry point demonstrating how to invoke the graph with an initial tweet prompt.

## Purpose

This example is meant to show how to build a basic stateful prompt workflow:
- generate content from user input,
- reflect on model output,
- revise the content iteratively,
- and manage the sequence of steps using a graph-based state machine.

## Requirements

The project depends on:

- `langchain`
- `langchain-core`
- `langchain-openai`
- `langgraph`
- `openai`
- `tiktoken`
- `python-dotenv`

## Usage

1. Install dependencies from `requirements.txt`.
2. Set your OpenAI API key, either through environment variables or a `.env` file.
3. Run `main.py` to see the graph execute and inspect the generated/reflected tweet output.
