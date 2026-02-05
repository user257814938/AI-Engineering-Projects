import streamlit as st
import asyncio
import os
from client import MCPClient
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="MCP Research Assistant", layout="wide")

st.title("🤖 MCP Research Assistant")
st.markdown("Integrates **Brave Search** and **Filesystem** MCP servers.")

# Sidebar Config
with st.sidebar:
    st.header("Configuration")
    provider = st.selectbox("LLM Provider", ["groq", "ollama"], index=0)
    # We might want to allow updating env vars here, but for now relying on .env
    
    if provider == "groq":
        api_key = st.text_input("Groq API Key", type="password", value=os.getenv("GROQ_API_KEY", ""))
        os.environ["GROQ_API_KEY"] = api_key
    
    st.info("Ensure you have BRAVE_API_KEY in your .env or environment.")

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

if "client" not in st.session_state:
    # We need to run client init in loop
    st.session_state.client = MCPClient()
    # Initializing connection needs async
    # We will do it lazily or start a loop in a separate thread/way? 
    # Streamlit is synchronous by default, but supports async function calls via asyncio.run or loop attached
    pass

# Chat Interface
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "tool_calls" in msg:
            with st.expander("Tool Calls"):
                st.json(msg["tool_calls"])

user_input = st.chat_input("What would you like to research?")

async def run_query(query):
    client = st.session_state.client
    # Make sure client is initialized (connected)
    if not client.sessions:
        with st.spinner("Connecting to MCP servers..."):
             await client.initialize()
    
    with st.spinner("Thinking..."):
        response, tool_results = await client.process_query(query)
    return response, tool_results

if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Run loop
    try:
        response, tool_results = asyncio.run(run_query(user_input))
        
        # Add assistant message
        msg_data = {"role": "assistant", "content": response}
        if tool_results:
            msg_data["tool_calls"] = tool_results
        
        st.session_state.messages.append(msg_data)
        
        with st.chat_message("assistant"):
            st.write(response)
            if tool_results:
                with st.expander("Tool Usage"):
                    for t in tool_results:
                        st.caption(f"Tool: {t['name']}")
                        st.code(t['content'])

    except Exception as e:
        st.error(f"Error: {e}")
