<div align="center">
  <img src="assets/logo.png" alt="Project Logo" width="200"/>
  <h1>Local Store MCP</h1>
  <p><em>Your Data, Store Local</em></p>
</div>


## Demo Video
[📹 View Full Video](assets/introduce.mp4)


## Features

- ✅ **Smart Storage**: Auto-generate titles and tags
- 🔍 **Powerful Search**: Support fuzzy search and tag filtering
- 🏷️ **Smart Tags**: AI-suggested tags based on content
- 📊 **Statistics**: Knowledge base usage statistics
- 💾 **Secure Storage**: Data stored in user home directory
- 🔒 **Thread Safe**: Support concurrent access

## Project Structure

```
knowledge_vault/
├── __init__.py          # Package initialization
├── server.py            # FastMCP server main file
├── storage.py           # Knowledge storage module
└── search.py            # Search functionality module
pyproject.toml           # Project configuration
start_server_new.py      # Startup script
```

## Installation

### Install dependencies with uv

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync
```

### Configure Claude Desktop

Edit `~/.config/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "knowledge-vault": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/your/local_store_mcp",
        "run",
        "python",
        "start_server_new.py"
      ],
      "cwd": "/path/to/your/local_store_mcp",
      "description": "Local Knowledge Management MCP Server"
    }
  }
}
```

### Restart Claude Desktop

Restart Claude Desktop after configuration.

## Usage

### Store Knowledge
```
Store a programming tip: Using Python list comprehension makes code more concise
```

### Search Knowledge
```
Search for Python knowledge
```

### View Statistics
```
Show knowledge base statistics
```

## Available Tools

1. **store_knowledge** - Store knowledge records
2. **search_knowledge** - Search knowledge records
3. **list_recent** - View recent records
4. **get_knowledge** - Get record by ID
5. **suggest_tags** - Suggest tags
6. **search_by_tags** - Search by tags
7. **get_stats** - Get statistics

## Data Storage

- Location: `~/.knowledge-vault/knowledge.jsonl`
- Format: JSON Lines
- Thread Safe: File locking for concurrent access

## Tech Stack

- **FastMCP**: MCP server framework
- **Pydantic**: Data validation
- **uv**: Modern Python package management
- **Python 3.10+**: Runtime environment
