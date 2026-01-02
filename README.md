# 🐉 Dragon's Codex

## A Local RAG System for the Wheel of Time Series

Query the complete Wheel of Time universe using local LLMs powered by Ollama. Get accurate, spoiler-free answers about characters, magic, prophecies, and more.

---
                                                                                               Question
                     Chunks       Segmentation           Model              Aliases           Classifier     retrieval_quality
---------------  -------------   --------------  ---------------------  ------------------  -------------  ---------------------;
   Phase 1A        Only Books     Paragraphs      Ollama / nomic-2048         No                  N/A        0.4800
   Phase 1A1       Only Books     Semantic        Ollama / nomic-2048         No                  N/A        0.8186 (+70,5%)
   Phase 1B        Only Books     Semantic        Ollama / nomic-2048    Simple Expansion         N/A        0.8396 (+2,5%)
   Phase 1B1       Only Books     Semantic        Ollama / nomic-2048    Expansion + BM25         N/A        0.8502 (+1,3%)
   Phase 2A       + Characters    Semantic        Ollama / nomic-2048    Expansion + BM25       Model v0
   Phase 2B       + Concepts      Semantic        Ollama / nomic-2048    Expansion + BM25       Model v0
   Phase 2C       + Magic         Semantic        Ollama / nomic-2048    Expansion + BM25       Model v0
   Phase 2D       + Prophecy      Semantic        Ollama / nomic-2048    Expansion + BM25       Model v0
   Phase 2E       + Timeline      Semantic        Ollama / nomic-2048    Expansion + BM25       Model v0
   Phase 2F       + Plot Event    Semantic        Ollama / nomic-2048    Expansion + BM25       Model v0
   Phase 2G       + Relationship  Semantic        Ollama / nomic-2048    Expansion + BM25       Model v0
   Phase 2H       + Cross_ref.    Semantic        Ollama / nomic-2048    Expansion + BM25       Model v0

### Chunks

   Only books

### Segmentation

   Paragraphs maximizing the size. Poorly curated

###

## ✨ Features

- **Character Evolution Tracking**: Follow character development across all 15 books
- **Magic System Queries**: Understand the One Power, channeling, and weaves
- **Prophecy Analysis**: Cross-reference prophecies with events
- **Spoiler-Free Mode**: Temporal filtering prevents spoilers beyond a specified book
- **Wiki Integration**: Combines book content with character wiki data
- **100% Local**: All processing runs on your machine - no cloud APIs required

---

## 🎯 Quick Start

### Prerequisites

- **Windows 10/11**
- **Python 3.11+**
- **32GB RAM** (recommended)
- **20GB free disk space**
- **Ollama for Windows**

### Installation

1. **Clone or download this repository**

   ```bash
   cd C:\Users\YourName\Documents
   git clone <repo-url> dragon-codex
   cd dragon-codex
   ```

2. **Install Python dependencies**

   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Install Ollama** (from <https://ollama.ai/download>)

   ```bash
   ollama pull nomic-embed-text
   ollama pull llama3.1:8b
   ```

4. **Organize your data**
   - Copy 15 book markdown files to `data/raw/books/`
   - Copy ~6000 wiki markdown files to `data/raw/wiki/`

5. **Configure environment**

   ```bash
   copy .env.template .env
   # Edit .env with your paths
   ```

6. **Verify setup**

   ```bash
   python test_setup.py
   ```

---

## 📚 Usage

### Basic Query (Coming in Week 7)

```bash
python main.py "How does Rand's character develop through book 6?"
```

### Spoiler-Free Mode

```bash
python main.py "What do we know about Moiraine?" --max-book 5
```

### Interactive Mode

```bash
python main.py
> /help
> What is the One Power?
> /temporal 3
> Who is the Dragon Reborn?
```

---

## 🏗️ Project Structure

``` markdown
dragon-codex/
├── data/
│   ├── raw/
│   │   ├── books/          # 15 book markdown files
│   │   └── wiki/           # ~6000 wiki markdown files
│   ├── processed/          # Parsed and chunked data
│   └── metadata/           # Character index, prophecies, etc.
├── vector_stores/          # ChromaDB collections
├── src/
│   ├── ingestion/          # Data parsing and chunking
│   ├── retrieval/          # Vector search and retrieval
│   ├── query/              # Query processing
│   ├── generation/         # LLM response generation
│   └── utils/              # Config, logging, constants
├── notebooks/              # Jupyter exploration notebooks
├── tests/                  # Test queries and data
└── main.py                 # CLI interface
```

---

## 🎓 Example Queries

### Character Development

``` markdown
"Trace Egwene's journey from the Two Rivers to becoming Amyrlin Seat"
"How does Perrin's relationship with wolves develop?"
```

### Magic System

``` markdown
"Explain the difference between saidin and saidar"
"What is balefire and why is it dangerous?"
"How does Traveling work?"
```

### Prophecies

``` markdown
"What are the main Dragon Reborn prophecies?"
"What do Min's viewings reveal about Rand?"
```

### Timeline & Events

``` markdown
"What happens at the Battle of Falme?"
"Describe the events in Rhuidean"
```

---

## ⚙️ Configuration

Edit `.env` to customize:

```ini
# Models
EMBEDDING_MODEL=nomic-embed-text
LLM_MODEL=llama3.1:8b

# Chunk settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=100

# Retrieval
TOP_K_RETRIEVAL=10
SIMILARITY_THRESHOLD=0.7

# LLM generation
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
```

---

## 📖 Data Sources

This project works with:

- **15 Book Files**: All Wheel of Time books in markdown format
  - New Spring (prequel, book 0)
  - The Eye of the World through A Memory of Light (books 1-14)
- **~6000 Wiki Files**: Character and concept wikis with temporal sections

### Expected Data Format

**Books**: Markdown with chapter structure

```markdown
Prologue
*Title*
[Content]

Chapter 
1
*Title*
[Content]

Glossary
***Character*** Description
```

**Wiki**: Markdown with temporal sections

```markdown
# Character Name
## In The Eye of the World
### Events
## In The Great Hunt
### Events
## Abilities and Skills
```

---

## 🔧 Development Status

**Current Phase**: Week 1 - Environment Setup ✅

**Completed**:

- ✅ Python environment configuration
- ✅ Ollama integration
- ✅ Data organization
- ✅ Utility modules (config, logging, constants)
- ✅ Test queries defined

**Next Phase**: Week 2 - Book Processing Pipeline

---

## 🛠️ Troubleshooting

### Ollama Not Found

```bash
# Check Ollama is running
ollama list

# Restart Ollama if needed
# (Close from system tray and restart)
```

### Import Errors

```bash
# Ensure virtual environment is activated
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

### ChromaDB Issues

```bash
# May need Visual C++ Build Tools
# Download from Microsoft
pip install chromadb --no-build-isolation
```

### Data Not Found

- Check paths in `.env` match your actual directory structure
- Use absolute paths (e.g., `C:\Users\...`)
- Verify files are in `data/raw/books/` and `data/raw/wiki/`

---

## 📊 System Requirements

### Minimum

- Windows 10/11
- Python 3.11+
- 16GB RAM
- 15GB free disk space

### Recommended

- Windows 11
- Python 3.12
- 32GB RAM
- 25GB free disk space
- SSD for vector store

---

## 🎯 Development Roadmap

### Phase 1: Foundation (Weeks 1-3) ✅

- Environment setup
- Data parsing
- Character and concept extraction

### Phase 2: Core RAG (Weeks 4-6)

- Chunking strategy
- Vector stores
- Basic retrieval

### Phase 3: Intelligence (Weeks 7-8)

- Query classification
- LLM integration
- Query expansion

### Phase 4: Quality (Weeks 9-10)

- Context assembly
- Response quality
- CLI interface

### Phase 5: Advanced (Weeks 11-12)

- MCP server
- Testing
- Documentation

---

## 📝 License

This project is for personal use with legally obtained Wheel of Time content.

**The Wheel of Time** is © Robert Jordan and the Bandersnatch Group.

---

## 🙏 Acknowledgments

- Built using **Ollama** for local LLM inference
- Vector search powered by **ChromaDB**
- Framework by **LangChain**
- Inspired by the **Malazan RAG** project approach

---

## 📞 Support

For issues or questions:

1. Check the troubleshooting section above
2. Review the Week 1 Complete Guide
3. Verify all setup tests pass (`python test_setup.py`)

---

**May the Light illuminate your queries and the Creator shelter your code!** 🐉📚✨

---

## 🔄 Recent Updates

**Week 1 Complete** - 2025

- ✅ Environment fully configured
- ✅ Data organized and documented
- ✅ Utility modules created
- ✅ Ready for Week 2 development
