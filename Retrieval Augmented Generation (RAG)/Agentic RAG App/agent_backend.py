import os
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain_community.embeddings import FakeEmbeddings # Using FakeEmbeddings to avoid extra API costs for this demo/challenge
# In a real scenario, use OpenAIEmbeddings or similar

def get_agent_executor():
    """
    Initializes and returns the agent executor with RAG and Search capabilities.
    """
    
    # 1. Setup LLM
    llm = ChatGroq(
        temperature=0,
        model_name="llama3-70b-8192", # Or "mixtral-8x7b-32768"
        api_key=os.environ.get("GROQ_API_KEY")
    )

    # 2. Setup Tools
    search = TavilySearchResults(max_results=2)
    
    # 3. Setup RAG (Simple Demo Version)
    # create some dummy documents to demonstrate RAG
    docs = [
        Document(page_content="The Agentic RAG Streamlit App is a daily challenge to build a tool-using agent.", metadata={"source": "challenge_description"}),
        Document(page_content="This app uses Groq for the LLM, Tavily for search, and Streamlit for the UI.", metadata={"source": "tech_stack"}),
        Document(page_content="You are Antigravity, a powerful agentic AI coding assistant.", metadata={"source": "identity"}),
    ]
    
    # Use FakeEmbeddings for simplicity in this challenge unless we want to require OpenAI Key
    # If the user has other embeddings, they can swap this.
    embeddings = FakeEmbeddings(size=1536) 
    vector = FAISS.from_documents(docs, embeddings)
    retriever = vector.as_retriever()
    
    from langchain.tools.retriever import create_retriever_tool
    retriever_tool = create_retriever_tool(
        retriever,
        "search_local_knowledge",
        "Searches for information about the Agentic RAG Streamlit App challenge specifics and identity."
    )

    tools = [search, retriever_tool]

    # 4. Create Agent
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant. Use the tools available to answer the user's question. If you need to search the web, use the search tool. If you need to know about the app itself, use the local knowledge."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    return agent_executor
