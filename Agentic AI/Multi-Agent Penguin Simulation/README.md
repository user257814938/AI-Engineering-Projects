# Multi-Agent Penguin Simulation

A multi-agent simulation using Hugging Face's `smolagents` library where penguin agents interact with a scientist agent to manage resources.

## Overview

This simulation demonstrates agent-to-agent interaction where:
- **Penguin Agents**: Make decisions about finding food (fishing or foraging) or requesting resources
- **Scientist Agent**: Responds to penguin actions by distributing food and tools based on history and available resources

## Prerequisites

- Python 3.8+
- A free [Hugging Face API Token](https://huggingface.co/settings/tokens)

## Setup

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment:**
   Copy `.env.example` to `.env` and add your Hugging Face token:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and set:
   ```
   HUGGINGFACEHUB_API_TOKEN=hf_your_actual_token_here
   ```

## Usage

Run the simulation:
```bash
python starter.py
```

The simulation will run for 3 rounds with 4 penguin agents. Each round:
1. Penguins decide their actions (find food or request resources)
2. Penguins with tools can fish (higher yield: 2-7 food)
3. Penguins without tools can forage (lower yield: 0-3 food)
4. The scientist distributes resources based on penguin history and needs

## Features

- **Tool System**: Custom tools for checking history, recording distributions, and finding food
- **Resource Management**: Scientist manages limited food supply and tool availability
- **History Tracking**: Tracks resource distribution history for each penguin
- **Periodic Refresh**: Scientist's resources refresh every 5 turns

## Project Structure

- `starter.py` - Main simulation code with agent definitions
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variable template
- `.gitignore` - Git ignore rules (protects `.env` file)
