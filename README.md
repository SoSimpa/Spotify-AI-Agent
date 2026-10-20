# Spotify-AI-Agent

An AI agent that helps you create curated Spotify playlists based on your preferences using natural language.

It uses **LangGraph** + **Groq** (Llama) + a **Spotify MCP server** to search music, create playlists, and add tracks.

## Features
- Interactive chat interface
- Creates playlists with real songs added
- Limits default playlist size to 10 tracks (configurable via prompt)
- Credential validation on startup
- Focuses on playlist creation & recommendations (playback tools filtered out)

## Prerequisites
- Python 3.12+
- A [Spotify Developer app](https://developer.spotify.com/dashboard) with Client ID, Client Secret, and a Redirect URI
- A [Groq API key](https://console.groq.com/)
- A running **Spotify MCP server** (see configuration below)

## Setup

1. Clone the repo and create a virtual environment:

```bash
git clone https://github.com/SoSimpa/Spotify-AI-Agent.git
cd Spotify-AI-Agent
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -e .
```

2. Create a `.env` file in the project root:

```env
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
GROQ_API_KEY=your_groq_api_key
```

3. Configure your Spotify MCP server in `mcp_config.json`.

   The included `mcp_config.json` contains a placeholder. You must point it at a working Spotify MCP server.

   Example using the popular `varunneal/spotify-mcp` (requires `uv`):

```json
{
  "mcpServers": {
    "spotify": {
      "command": "uvx",
      "args": [
        "--python", "3.12",
        "--from", "git+https://github.com/varunneal/spotify-mcp",
        "spotify-mcp"
      ],
      "env": {
        "SPOTIFY_CLIENT_ID": "your_client_id",
        "SPOTIFY_CLIENT_SECRET": "your_client_secret",
        "SPOTIFY_REDIRECT_URI": "http://127.0.0.1:8080/callback"
      }
    }
  }
}
```

   Other good options:
   - [@tbrgeek/spotify-mcp-server](https://www.npmjs.com/package/@tbrgeek/spotify-mcp-server) via `npx`
   - Your own locally built Node or Python Spotify MCP server

   Make sure the tool names match what the agent expects (or update the filter list in `agent_script.py`).

## Run

```bash
python agent_script.py
```

Example prompts:
- "Create a chill lo-fi study playlist"
- "Make a 15-song playlist of upbeat 90s hip-hop"
- "Find songs similar to Radiohead and build a playlist"

Type `exit`, `quit`, or `bye` to stop.

## Notes
- The agent filters out pure playback-control tools so it focuses on discovery and playlist management.
- Playlist creation is instructed to always add actual songs.
- Credentials are validated at startup.
