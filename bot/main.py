import os
import asyncio
import nest_asyncio
from dotenv import load_dotenv
from telegram.ext import Application
from handlers import setup_handlers

# Load environment variables BEFORE importing handlers
load_dotenv()

async def main():
    # Get Telegram Bot Token from environment variable
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not bot_token:
        raise ValueError(
            "No Telegram Bot Token found. Please set TELEGRAM_BOT_TOKEN in the .env file."
        )
    
    try:
        # Create the Application and pass it your bot's token
        application = Application.builder().token(bot_token).build()
        
        # Setup handlers
        setup_handlers(application)
        
        # Start the Bot
        print("Bot is running. Press Ctrl+C to stop.")
        await application.run_polling()
    
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Apply nest_asyncio to handle nested event loops
    nest_asyncio.apply()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user.")