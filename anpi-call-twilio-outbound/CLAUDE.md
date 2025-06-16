# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered eldercare monitoring system that enables voice conversations between elderly users and AI agents through WebSocket communication using OpenAI's Realtime API. The system consists of multiple specialized agents that handle different aspects of the conversation.

## Development Commands

### Environment Setup
```bash
# Install dependencies using uv (recommended)
uv sync

# Run the FastAPI application
python main:app --reload --port 8080
```

## Architecture Overview

### Agent System
The system uses multiple AI agents with specialized roles:
- **通話エージェント (Call Agent)**: Primary agent that converses directly with elderly users via WebSocket. Must be implemented using OpenAI Realtime API.
- **俳句エージェント (Haiku Agent)**: Specialized agent for creating haiku poems when requested.
- **イベント推薦エージェント（Event Agent)**: Specialized agent for recomming event

### Layer Architecture
- **Controller Layer**: Handles WebSocket communication and routing
- **Model Layer**: Contains business logic, agent implementations, and data processing

### Technology Stack
- **Web Framework**: FastAPI
- **Python Version**: 3.11
- **Package Manager**: pip
- **Real-time Communication**: WebSocket + OpenAI Realtime API
- **Deployment**: GitHub Actions → GCP

## Implementation Guidelines

For detailed implementation guidelines, refer to:
- [Application Development Rules](./instructions/app-instructions.md)
- [Database Rules](./instructions//db-instructions.md)