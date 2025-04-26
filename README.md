# 🤖 Gemini Coding Agent

**Deepwiki doc**<https://deepwiki.com/praveenhm/coding-agent>

Building a code-editing agent is simpler than it seems—it’s mainly a loop with an LLM and enough tokens. With less than 400 lines of mostly boilerplate code, we can create a small but impressive agent.

---
This project implements a Python-based interactive coding agent powered by Google's Gemini models (using the newer `google-genai` SDK).

The agent can:
- Understand and respond to natural language prompts.
- Interact with your local file system (read, list, edit files).
- Execute shell commands.
- Run commands within a secure Docker sandbox (no network access, resource limits).
- Find arxiv papers.
- Maintain conversation history.
- Display the token count of the current conversation context in the input prompt.
- Upload and discuss PDF documents using the Gemini File API.

## ✨ Features

- **Interactive Chat:** Engage in a conversational manner with the AI.
- **File Operations:** Ask the agent to read, list, or modify files within the project directory.
- **Arxiv Search:** Ask the agent to find arxiv papers from cs or stat categories matching keywords.
- **Command Execution:** Request the agent to run shell commands in the project's context.
- **Sandboxed Execution:** Safely run potentially risky commands in an isolated Docker container using the `run_in_sandbox` tool (requires Docker).
- **Tool Integration:** Leverages Gemini's function calling capabilities to use defined Python tools.
- **Context Token Count:** Displays the approximate token count for the next API call right in the prompt (e.g., `You (123):`).
- **PDF Context Support:** Upload and discuss PDF documents using the Gemini File API.
- **Web Search:** Query Google and return top results as a JSON list of titles and URLs using the `google_search` tool. *Warning: This tool can be very slow to return results and consumes a lot of tokens. Also web-search-related token use is not shown in the coding-agent's token count.*
- **URL Browsing:** Visit any webpage and extract its visible text using the `open_url` tool.

## 🛠️ Setup

1.  **Clone the repository:**
    ```bash
    # Make sure you have the code, e.g., by cloning or downloading a zip file
    git clone git@github.com:praveenhm/coding-agent.git
    cd coding-agent
    ```
2.  **Set up a virtual environment and install dependencies using UV:**
    (Assumes you have [UV](https://github.com/astral-sh/uv) installed: `pip install uv`)
    ```bash
    # Create and activate a virtual environment
    uv venv
    source .venv/bin/activate # Or `.venv\Scripts\activate` on Windows

    # Install dependencies from pyproject.toml
    uv pip install .

    # (Optional) Install development dependencies
    uv pip install .[dev]
    ```

3.  **Set up API Key:**
    - The agent reads your Gemini API key exclusively from the `GEMINI_API_KEY` environment variable.
    - Before running, export your key:
      ```bash
      export GEMINI_API_KEY="your_key_here"
      ```

4.  **(Optional) Docker for Sandbox:**
    - If you want to use the `run_in_sandbox` tool, ensure you have Docker installed and running on your system.
    - You might need to pull the base image specified in `src/tools.py` (e.g., `python:3.12-slim`) if it's not already available locally:
      ```bash
      docker pull python:3.12-slim
      ```

## ▶️ Running the Agent

Ensure your virtual environment is active.

Run the agent as a module:
```bash
python -m src.main
```

(Note: Using `python -m src.main` ensures Python treats `src` as a package, correctly handling absolute imports like `from src.tools import ...`.)

## 📝 Notes
- The agent operates relative to the directory it was started from.

## 💬 Usage

- Simply type your requests or questions at the `You (<token_count>):` prompt.
- To exit the agent, type `exit`, `quit`, `/exit` or `/q`.
- Ask it to perform tasks like:
    - "Read the file src/tools.py"
    - "List files in the root directory"
    - "Edit README.md and add a section about future plans"
    - "run the command 'ls -l'"
    - "run 'pip list' in the sandbox"
    - "Search Google for 'latest AI news'"
    - "Open https://example.com and extract visible text"
- The number in parentheses indicates the approximate token count of the conversation history that will be sent with your *next* message.

### 📄 Working with PDFs

The agent can include PDF documents in the conversation context, allowing you to discuss and ask questions about their content:

1. **Upload a PDF:** Use the `/upload` command followed by the path to the PDF (relative to the project directory):
   ```
   /upload path/to/your/document.pdf
   ```

2. **Ask Questions:** Once uploaded, you can directly ask questions about the document:
   ```
   What are the key points in this paper?
   Summarize the methodology section.
   Extract all tables from this document.
   ```

3. **PDF Ingestion:** Use the `/upload` command to seed an uploaded PDF's text into the chat context (only once per file):
   ```
   /upload path/to/your/document.pdf
   ```
   After ingestion, the PDF is not reprocessed on each query.

4. **Reset Chat:** To clear the entire chat context (including any seeded PDF text) and start a fresh session:
   ```
   /reset
   ```

5. **View Status:** The number of active PDFs is shown in the prompt (e.g., `You (123) [2 files]:`)

### 🔍 Example: Web Search & Browse

```bash
# Launch the agent
coding-agent

# Perform a Google search
🔵 You (0): Search Google for "Python 3.14 new features"
🟢 Agent: [
  {"title": "What's New in Python 3.14", "url": "https://docs.python.org/3/whatsnew/3.14.html"},
  {"title": "Python 3.14 Release Notes", "url": "https://www.python.org/downloads/release/python-3140/"}
]

# Browse a webpage
🔵 You (123): Open https://docs.python.org/3/tutorial/
🟢 Agent: The Python Tutorial — Python 3.x ...
