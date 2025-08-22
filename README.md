# LeadSense

AI-powered lead generation and customer finding system with both CrewAI and OpenAI implementations.

## Prerequisites

- Python 3.12+ (for OpenAI implementation) or Python 3.10+ (for CrewAI implementation)
- [uv](https://docs.astral.sh/uv/) package manager

## Installation

### Install uv (if not already installed)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Clone and setup the project
```bash
git clone <repository-url>
cd leadsense
```

## Running the Project

This project contains two implementations:

### 1. CrewAI Implementation
```bash
cd crewai
uv sync
# Set up environment variables (copy .env.example to .env and configure)
cp .env.example .env
crewai run
```

### 2. OpenAI Implementation
```bash
cd openai
uv sync
# Set up environment variables (copy .env.example to .env and configure)
cp .env.example .env
# Edit .env with your API keys
uv run agents/leadsense.py
```

## Environment Setup

Both implementations require API keys. Create `.env` files in the respective directories:

- `crewai/.env` - Configure CrewAI specific environment variables
- `openai/.env` - Configure OpenAI API keys and other settings

## Project Structure

- `crewai/` - CrewAI-based implementation for multi-agent customer finding
- `openai/` - OpenAI-based implementation using agents framework
- Each directory contains its own dependencies and configuration files


Run leadsense_app: uvicorn leadsense_app.api.server:app --reload
Run leadsense_ui: npm run dev
