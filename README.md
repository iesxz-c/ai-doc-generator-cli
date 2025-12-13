# AI DocGen – Intelligent Code Documentation Generator

Automatically generate comprehensive, AI-powered technical documentation for Python, JavaScript, and TypeScript codebases. **AI DocGen** parses your code, analyzes git history, builds knowledge graphs, and generates beautifully formatted Markdown documentation with intelligent summaries, line-by-line explanations, dry runs, and execution traces.

## 🎯 Overview

**AI DocGen** is an end-to-end documentation generation pipeline that transforms raw code into structured, human-readable technical documentation. It leverages:

- **Multi-language parsers** (Python, JavaScript, TypeScript) with tree-sitter for robust AST parsing
- **Git history analysis** to understand code evolution and hotspots
- **Knowledge graphs** to visualize dependencies and relationships
- **LLM integration** (Google Gemini) for intelligent summaries with graceful fallbacks
- **Heuristic analysis** for code flow, execution traces, and line-by-line explanations

### Key Features

✨ **Automatic Multi-Language Parsing**
- Python (.py) – tree-sitter + stdlib ast fallback
- JavaScript (.js, .jsx) – tree-sitter with regex fallback
- TypeScript (.ts, .tsx) – tree-sitter with regex fallback
- Extracts: functions, classes, imports, docstrings, call graphs

📊 **Architecture Visualization**
- Mermaid flowcharts showing file dependencies
- Per-file workflow diagrams
- Knowledge graphs with nodes (files, functions, classes) and edges (imports, calls, definitions)
- Folder structure trees

📝 **Rich Code Documentation**
- **What This File Does** – AI-powered or heuristic summary of file purpose
- **Line-by-Line Explanation** – Detailed breakdown of significant code lines
- **Dry Run / Execution Trace** – Simulated execution with inputs/outputs
- **Function/Class Docs** – Extracted signatures and docstrings

🔍 **Git History Integration**
- Commit analysis and recent changes
- File hotspot detection
- Change impact tracking
- Graceful handling of non-git repos

🧠 **LLM-Powered Summaries**
- Gemini 2.0 Flash integration for intelligent analysis
- Automatic fallback to heuristics when API unavailable
- Handles quota limits gracefully

🚀 **Run Instructions**
- Auto-detected run commands per language
- Dependency extraction and listing
- Ready-to-copy execution commands

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Output Structure](#output-structure)
- [Examples](#examples)
- [Requirements](#requirements)

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- Node.js 14+ (for tree-sitter support)
- Git (optional, for git history analysis)

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/iesxz-c/ai-doc-generator-cli.git
   cd ai-docgen
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Gemini API (optional):**
   Create a `.env` file in the project root:
   ```env
   GOOGLE_API_KEY=your_api_key_here
   ```
   Get your key from [Google AI Studio](https://aistudio.google.com/app/apikey)

## 🚀 Quick Start

### Basic Usage

Generate documentation for a repository:

```bash
python -m cli.cli <repo_path> --output <output_file>
```

### Examples

**Generate docs for sample repo:**
```bash
python -m cli.cli sample_repo --output build/docs.md
```

**Generate docs for current directory:**
```bash
python -m cli.cli . --output docs/API.md
```

**Generate docs for large project:**
```bash
python -m cli.cli /path/to/project --output /path/to/output/docs.md
```

## 📖 Usage

### Command Line Interface

```bash
usage: python -m cli.cli [-h] [--output OUTPUT] [repo]

positional arguments:
  repo              Path to repo to document (default: sample_repo)

optional arguments:
  --output OUTPUT   Output markdown path (default: build/docs.md)
  -h, --help        Show this help message
```

### Programmatic Usage

```python
from cli.cli import run_pipeline

# Generate documentation
output_path = run_pipeline(
    repo_path="path/to/your/repo",
    output_path="docs.md"
)
print(f"Documentation generated at {output_path}")
```

### As a Python Module

```python
from parser import PythonParser, JavaScriptParser
from git_analyzer.git_history import describe_repo
from graph.knowledge_graph import build_graph, to_mermaid
from summarizer.llm_summarizer import LLMSummarizer
from docs_generator.markdown_builder import MarkdownBuilder

# Parse code
py_parser = PythonParser()
js_parser = JavaScriptParser()
parsed_files = py_parser.walk_directory("repo") + js_parser.walk_directory("repo")

# Analyze git
git_info = describe_repo("repo")

# Build graph
graph = build_graph(parsed_files, git_info)
mermaid = to_mermaid(graph)

# Generate summaries
summarizer = LLMSummarizer()
summaries = summarizer.generate_all(parsed_files, mermaid, git_info, None, {})

# Build markdown
builder = MarkdownBuilder()
docs = builder.build(parsed_files, summaries, mermaid, git_info, None, {}, "", "", [], [])
```

## 🏗️ Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Input Repository                         │
│              (Python, JavaScript, TypeScript)                │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
    ┌────────┐  ┌────────┐  ┌────────┐
    │Python  │  │  JS    │  │   TS   │
    │Parser  │  │Parser  │  │Parser  │
    └────┬───┘  └───┬────┘  └───┬────┘
         │          │           │
         └──────────┼───────────┘
                    │
         ┌──────────▼──────────┐
         │  Parsed AST Data    │
         │  (Functions, Classes│
         │   Imports, Calls)   │
         └──────────┬──────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
    ┌────────┐ ┌────────┐ ┌────────┐
    │  Git   │ │Knowledge│ │ LLM    │
    │Analyzer│ │ Graph  │ │Summary │
    └────┬───┘ └───┬────┘ └───┬────┘
         │         │          │
         └─────────┼──────────┘
                   │
        ┌──────────▼──────────┐
        │  Markdown Builder   │
        │  (Format & Render)  │
        └──────────┬──────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  Output: docs.md     │
        │  (Full Documentation)│
        └──────────────────────┘
```

### Module Breakdown

**`parser/`** – Multi-language code parsing
- `base_parser.py` – Abstract parser interface
- `python_parser.py` – Python AST extraction
- `js_parser.py` – JavaScript/TypeScript parsing

**`git_analyzer/`** – Git history analysis
- `git_history.py` – Commit mining, hotspot detection

**`graph/`** – Knowledge graph construction
- `knowledge_graph.py` – Build nodes/edges, Mermaid rendering

**`summarizer/`** – LLM-powered analysis
- `llm_summarizer.py` – Gemini integration, heuristic fallbacks

**`docs_generator/`** – Markdown generation
- `markdown_builder.py` – Format and render documentation

**`cli/`** – Command-line orchestration
- `cli.py` – Pipeline orchestrator

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Google Gemini API Key (optional)
GOOGLE_API_KEY=your_key_here

# Optional: Model selection
# GEMINI_MODEL=gemini-2.0-flash-exp
```

### Default Settings

| Setting | Default | Purpose |
|---------|---------|---------|
| Output Path | `build/docs.md` | Where to save generated docs |
| Repo Path | `sample_repo` | Code repository to document |
| Model | `gemini-2.0-flash-exp` | LLM model for summaries |
| Max Tree Depth | 4 | Folder structure depth limit |

## 📄 Output Structure

Generated documentation includes:

### 1. **Project Overview**
   - File count, functions, classes, imports
   - High-level project summary

### 2. **Architecture Overview**
   - Mermaid flowchart of file dependencies
   - Class and function definitions

### 3. **Statistics**
   - Code metrics (files, functions, classes)

### 4. **Folder Structure**
   - Directory tree (respects max depth)

### 5. **Per-File Workflows**
   - Mermaid flowchart per file
   - Shows functions and classes defined

### 6. **Modules**
   - Per-file documentation:
     - **What This File Does** – Purpose summary
     - **Line-by-Line Explanation** – Code breakdown
     - **Dry Run / Execution Trace** – Example execution
     - **Imports** – External dependencies
     - **Functions** – Signatures and docstrings
     - **Classes** – Class definitions

### 7. **Summaries**
   - Architecture summary
   - File roles
   - Function documentation
   - Recent changes (from git)
   - .gitignore analysis

### 8. **Git Insights**
   - Recent commits
   - File hotspots
   - Change history

### 9. **How to Run**
   - Run command per file
   - Dependency listing

## 📚 Examples

### Example 1: Python Project

**Input:** `sample_repo/sample.py`
```python
class Solution(object):
    def twoSum(self, nums, target):
        """Find two numbers that sum to target."""
        d = {}
        for i, j in enumerate(nums):
            k = target - j
            if k in d:
                return [d[k], i]
            d[j] = i
```

**Generated Output:**
```markdown
#### What This File Does
This file implements a LeetCode-style solution for the two-sum problem. 
It contains a Solution class with a method that finds two numbers in a 
list that add up to a target value using a hash map for O(n) time complexity.

#### Line-by-Line Explanation
Line 1: Define class Solution
Line 2: Define function twoSum
Line 8: Variable assignment - d={}
Line 9: Loop iteration - for i,j in enumerate(nums):
Line 10: Variable assignment - k=target-j
Line 11: Conditional check - if k in d:
Line 12: Return statement - return [d[k],i]

#### Dry Run / Execution Trace
Example Execution (Two-Sum Problem):
Input: nums = [2, 7, 11, 15], target = 9
1. Initialize empty dict: d = {}
2. Iterate through nums:
   - i=0, j=2: k = 9-2 = 7, 7 not in d, d[2] = 0
   - i=1, j=7: k = 9-7 = 2, 2 IS in d, return [d[2], 1] = [0, 1]
Output: [0, 1]
```

### Example 2: JavaScript Server

**Input:** `sample_repo/index.js`
```javascript
const http = require('node:http');
const hostname = '127.0.0.1';
const port = 3000;

const server = http.createServer((req, res) => {
  res.statusCode = 200;
  res.setHeader('Content-Type', 'text/plain');
  res.end('Hello, World!\n');
});

server.listen(port, hostname, () => {
  console.log(`Server running at http://${hostname}:${port}/`);
});
```

**Generated Output:**
```markdown
#### What This File Does
This file sets up a web server. It creates an HTTP server that listens 
on a specified port and handles incoming requests, returning responses to clients.

#### How to Run
**Command:** `node index.js`
**Dependencies:**
- (no external dependencies)
```

## 📦 Requirements

See `requirements.txt`:

```
GitPython>=3.1.0
google-genai>=0.3.0
python-dotenv>=0.19.0
tree-sitter>=0.20.0
```

### Optional Dependencies

- **tree-sitter-python** – Enhanced Python parsing
- **tree-sitter-javascript** – Enhanced JavaScript parsing
- **tree-sitter-typescript** – TypeScript parsing

## 🔄 Workflow

1. **Parse Code** – Extract AST, functions, classes, imports
2. **Analyze Git** – Mine commits, identify hotspots
3. **Build Graph** – Create knowledge graph with dependencies
4. **Generate Summaries** – Use Gemini or heuristics
5. **Render Markdown** – Format and output documentation

## ⚡ Performance

- **Small repos** (<50 files): ~5-10 seconds
- **Medium repos** (50-200 files): ~20-30 seconds
- **Large repos** (200+ files): ~1-2 minutes

*Times include Gemini API calls; faster with fallback heuristics.*

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- [ ] Additional language support (Go, Rust, Java, etc.)
- [ ] VS Code extension
- [ ] Enhanced call graph analysis
- [ ] Custom template support
- [ ] HTML/PDF output formats
- [ ] CI/CD integration examples

## 📜 License

MIT License – See LICENSE file

## 🙋 Support

Found a bug or have a feature request? Open an issue on [GitHub](https://github.com/iesxz-c/ai-doc-generator-cli/issues).

---

**Happy documenting!** 🚀
