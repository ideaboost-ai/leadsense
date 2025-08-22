# LeadSense OpenAI

OpenAI-based implementation using the agents framework for lead generation and customer finding.

## Installation

1. Install dependencies:
```bash
uv sync
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your OpenAI API key and other required settings
```

## Running the Project

Run the LeadSense agent:
```bash
python -m agents.leadsense
```

Or using uv:
```bash
uv run python -m agents.leadsense
```

## Development

Install development dependencies:
```bash
uv sync --group dev
```

This includes Jupyter kernel support for interactive development.

## Requirements

- Python 3.12+
- OpenAI API key
- MCP (Model Context Protocol) support
- Required environment variables configured in `.env`