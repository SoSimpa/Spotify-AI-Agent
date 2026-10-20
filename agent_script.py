# Import necessary libraries
import os
import asyncio
import requests
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.graph import MessagesState

from mcp_use.client import MCPClient
from mcp_use.adapters.langchain_adapter import LangChainAdapter

load_dotenv()


def check_spotify_credentials() -> bool:
    """Check if Spotify API credentials are valid by attempting to get an access token."""
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")

    if not all([client_id, client_secret, redirect_uri]):
        print("❌ Missing Spotify credentials in .env file")
        return False

    auth_url = "https://accounts.spotify.com/api/token"
    auth_headers = {"Content-Type": "application/x-www-form-urlencoded"}
    auth_data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }

    try:
        response = requests.post(auth_url, headers=auth_headers, data=auth_data)
        if response.status_code == 200:
            print("✅ Spotify credentials are valid")
            return True
        else:
            print(f"❌ Spotify credentials invalid. Status: {response.status_code}")
            print(f"Response: {response.json()}")
            return False
    except Exception as e:
        print(f"❌ Error checking Spotify credentials: {e}")
        return False


def check_groq_credentials() -> bool:
    """Check if Groq API key is valid by making a simple test request."""
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        print("❌ Missing Groq API key in .env file")
        return False

    url = "https://api.groq.com/openai/v1/models"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print("✅ Groq API key is valid")
            return True
        else:
            print(f"❌ Groq API key invalid. Status: {response.status_code}")
            print(f"Response: {response.json()}")
            return False
    except Exception as e:
        print(f"❌ Error checking Groq API key: {e}")
        return False


async def create_graph():
    """Create the LangGraph agent with Spotify MCP tools."""
    client = MCPClient.from_config_file("mcp_config.json")
    adapter = LangChainAdapter()

    tools = await adapter.create_tools(client)
    # Filter out pure playback tools — focus on playlist creation & recommendations
    excluded = {
        "getNowPlaying", "getRecentlyPlayed", "getQueue", "playMusic",
        "pausePlayback", "skipToNext", "skipToPrevious", "resumePlayback",
        "addToQueue", "getMyPlaylists", "getUsersSavedTracks",
        "saveOrRemoveAlbum", "checkUsersSavedAlbums"
    }
    tools = [t for t in tools if t.name not in excluded]

    llm = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct")
    llm_with_tools = llm.bind_tools(tools, parallel_tool_calls=False)

    system_msg = SystemMessage(content="""You are a helpful assistant that has access to Spotify.
You can create playlists, find songs, and provide music recommendations.

When creating playlists:
- If the user does not specify playlist size, limit playlist lengths to only 10 songs.
- Always provide helpful music recommendations based on user preferences and create well-curated playlists with appropriate descriptions.
- When the user requests a playlist to be created, ensure that songs are actually added to the playlist you create.
""")

    def assistant(state: MessagesState):
        response = llm_with_tools.invoke([system_msg] + state["messages"])
        return {"messages": [response]}

    builder = StateGraph(MessagesState)
    builder.add_node("assistant", assistant)
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "assistant")
    builder.add_conditional_edges("assistant", tools_condition)
    builder.add_edge("tools", "assistant")

    return builder.compile()


async def main():
    print("Checking API credentials...\n")

    spotify_valid = check_spotify_credentials()
    groq_valid = check_groq_credentials()

    print("\nCredentials Summary:")
    print(f"Spotify: {'✅ Valid' if spotify_valid else '❌ Invalid'}")
    print(f"Groq: {'✅ Valid' if groq_valid else '❌ Invalid'}")

    if not (spotify_valid and groq_valid):
        print("\n⚠️  Please fix invalid credentials before proceeding.")
        return

    print("\n🎉 All credentials are working! Starting agent...\n")
    print("Type 'exit', 'quit', or 'bye' to stop.\n")

    agent = await create_graph()
    messages = []

    while True:
        try:
            user_input = input("User: ").strip()
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit", "bye"}:
                print("Goodbye!")
                break

            messages.append(HumanMessage(content=user_input))

            # Run the agent graph
            result = await agent.ainvoke({"messages": messages})

            # Extract the latest assistant reply
            ai_message = result["messages"][-1]
            print(f"\nAssistant: {ai_message.content}\n")

            # Keep full history for multi-turn context
            messages = result["messages"]

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            # Continue the loop so the user can try again


if __name__ == "__main__":
    asyncio.run(main())
