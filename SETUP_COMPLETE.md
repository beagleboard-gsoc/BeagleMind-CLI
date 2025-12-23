# BeagleMind RAG PoC - Setup Complete ✓

## Issues Fixed

### 1. **Import Issues in Gradio App**
   - **Problem**: `gradio_app.py` and `qa_system.py` were using absolute imports instead of relative imports
   - **Solution**: Changed imports to use relative imports (`.module_name`) to work properly with Python's module system
   - **Files Modified**:
     - `src/gradio_app.py`: Changed `from qa_system import` → `from .qa_system import`
     - `src/gradio_app.py`: Changed `import config` → `from . import config`
     - `src/qa_system.py`: Changed `from config import` → `from .config import`
     - `src/qa_system.py`: Changed `from tools_registry import` → `from .tools_registry import`

### 2. **Gradio Version Compatibility**
   - **Problem**: Gradio 5.46.1 had issues with pathlib when reading source files
   - **Solution**: Downgraded to Gradio 4.40.0 - 4.x series which is more stable
   - **Command**: `pip install "gradio>=4.40.0,<5.0.0"`

## How to Run

### CLI Application
```bash
# Show help
python -m src.cli --help

# List available models
python -m src.cli list-models

# Interactive chat mode
python -m src.cli chat

# Single prompt mode
python -m src.cli chat -p "Your question here"

# Chat with specific backend and model
python -m src.cli chat -b groq -m "llama-3.3-70b-versatile" -p "Your question"
```

### Gradio RAG Web Application
```bash
# Start the Gradio web app
python -m src.gradio_app
```

The app will be available at: **http://127.0.0.1:7860**

## Project Structure
```
BeagleMind-RAG-PoC/
├── app.py                 # Main entry point
├── src/
│   ├── cli.py            # CLI application (Click)
│   ├── gradio_app.py     # Gradio web interface
│   ├── qa_system.py      # Core RAG system
│   ├── config.py         # Configuration & ConfigManager
│   └── main.py           # Main module for REPL
├── data/                 # Datasets and indices
├── requirements.txt      # Python dependencies
└── README.md
```

## Available Commands

### CLI Commands
- `list-models` - Show all available AI models
- `chat` - Start chat with BeagleMind
  - `-p, --prompt TEXT` - Single prompt mode
  - `-b, --backend TEXT` - Choose backend (groq, openai, ollama)
  - `-m, --model TEXT` - Specific model to use
  - `-t, --temperature FLOAT` - Temperature (0.0-1.0)
  - `-i, --interactive` - Force interactive mode
  - `--sources` - Show source documents
  - `--no-tools` - Disable tool usage

## Status
✅ All problems fixed
✅ CLI is functional
✅ Gradio app is running
✅ Dependencies are properly installed

## Configuration
- Default Backend: GROQ
- Default Model: llama-3.3-70b-versatile
- Collection: beagleboard
- Config file: `~/.beaglemind_config.json`

## Next Steps
1. Set your API keys in `.env` file (GROQ_API_KEY, OPENAI_API_KEY, etc.)
2. Ensure RAG backend is running (if using remote backend)
3. Access the Gradio app at http://127.0.0.1:7860
4. Use CLI for command-line interactions
