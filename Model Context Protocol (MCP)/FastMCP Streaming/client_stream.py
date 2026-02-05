import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
# from mcp.client.sse import sse_client # If available

async def on_message(message):
    """
    Handle incoming messages from the server.
    We are looking for notifications (log messages) to display progress.
    """
    # Check if the message is a notification/log
    # The structure of message depends on the SDK version, but typically it has a 'method' and 'params'
    # Notifications often come as 'notifications/message' or '$/log'
    
    # For debugging/demonstration, we'll print what we get if it looks like a notification
    if hasattr(message, 'root'):
         msg_root = message.root
         if msg_root.get('method') == 'notifications/message':
             params = msg_root.get('params', {})
             level = params.get('level')
             data = params.get('data')
             print(f"NOTIFICATION: [{level}] {data}")
    
    # Basic print for anything else that might be a notification
    # print(f"Raw Message: {message}") 

async def run():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["server_stream.py"],
        env=None
    )

    print("Connecting to server via STDIO...", flush=True)
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("Session initialized.", flush=True)
            
            # Handler for logging notifications from server
            def log_handler(*args, **kwargs):
                print(f"NOTIFICATION args: {args} kwargs: {kwargs}", flush=True)

            # Hook into the private logging callback if available
            if hasattr(session, '_logging_callback'):
                session._logging_callback = log_handler
                print("Registered logging callback.", flush=True)
            else:
                 print("WARNING: Could not find _logging_callback.", flush=True)
            
            # Ensure we receive INFO logs
            try:
               if hasattr(session, 'set_logging_level'):
                   await session.set_logging_level("info")
                   print("Set logging level to 'info'.", flush=True)
            except Exception as e:
                print(f"WARNING: Failed to set logging level: {e}", flush=True)
            
            print("Calling process_items...", flush=True)

            result = await session.call_tool("process_items", arguments={"total": 5})
            print(f"Final Result: {result.content[0].text}", flush=True)

if __name__ == "__main__":
    asyncio.run(run())
