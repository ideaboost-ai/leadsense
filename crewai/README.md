# LeadSense CrewAI

CrewAI-based implementation for multi-agent customer finding and lead generation.

## Installation

1. Install dependencies:
```bash
uv sync
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## Running the Project

To kickstart your crew of AI agents and begin task execution:

```bash
crewai run
```

This command initializes the customer-finder Crew, assembling the agents and assigning them tasks as defined in your configuration.

## Available Commands

- `uv run customer_finder` - Run the customer finder
- `uv run train` - Train the crew
- `uv run replay` - Replay previous runs
- `uv run test` - Run tests
