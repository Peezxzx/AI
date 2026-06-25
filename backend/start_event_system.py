"""
Integration script to start the Event System Manager
"""

import asyncio
import logging
from .event_system_manager import event_system_manager
from .redis_client import redis_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def start_event_system():
    """Start the event system"""
    try:
        print("Starting Atsawin AI Event System...")
        
        # Initialize the event system
        await event_system_manager.initialize()
        
        # Start the event system
        await event_system_manager.start()
        
        print("Event System started successfully!")
        
        # Keep the system running
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"Error starting event system: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(start_event_system())