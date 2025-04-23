#!/usr/bin/env python3
import os
import discord
import requests
import json
from typing import List, Dict, Set
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Chai API configuration
CHAI_API_URL = "http://guanaco-submitter.guanaco-backend.k2.chaiverse.com/endpoints/onsite/chat"
CHAI_API_KEY = os.environ.get("CHAI_API_KEY", "CR_14d43f2bf78b4b0590c2a8b87f354746")

# Discord bot configuration
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "YOUR_DISCORD_BOT_TOKEN")
DISCORD_APP_ID = os.environ.get("DISCORD_APP_ID", "1364074638271058000")

# Bot configuration
BOT_NAME = "ChaiBot"
USER_NAME = "User"
BOT_PROMPT = "A helpful and engaging conversation with ChaiBot."

# Initialize Discord bot with intents
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
bot = commands.Bot(command_prefix='!', intents=intents)

# Chat history storage - simple in-memory storage
# In a production environment, you might want to use a database
chat_histories = {}

# Set to track active chat channels
active_channels = set()

async def call_chai_api(prompt: str, bot_name: str, user_name: str, 
                        chat_history: List[Dict[str, str]]) -> str:
    """Call the Chai API and return the response."""
    
    headers = {
        "Authorization": f"Bearer {CHAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "memory": "",  # deprecated
        "prompt": prompt,
        "bot_name": bot_name,
        "user_name": user_name,
        "chat_history": chat_history
    }
    
    try:
        response = requests.post(CHAI_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        # Extract just the bot's response from the model output
        # The API response includes the bot's name and user's name in the output
        bot_response = result.get("model_output", "Sorry, I couldn't process your request.")
        
        # Extract just the bot's response (removing any user response the model might have generated)
        if user_name in bot_response:
            bot_response = bot_response.split(user_name)[0].strip()
            
        return bot_response
    
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return "Sorry, I encountered an error while processing your request."

@bot.event
async def on_ready():
    """Event called when the bot is ready."""
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('------')
    await bot.change_presence(activity=discord.Game(name="Chat with me!"))

@bot.event
async def on_message(message):
    """Handle all incoming messages."""
    # Don't respond to ourselves
    if message.author == bot.user:
        return
    
    # Process commands if the message starts with the command prefix
    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)
        return
    
    # Only respond in active channels or direct messages
    channel_id = message.channel.id
    if not isinstance(message.channel, discord.DMChannel) and channel_id not in active_channels:
        return
    
    # Process the message as a chat with the bot
    user_id = message.author.id
    user_key = f"{channel_id}_{user_id}"
    
    # Initialize chat history for new users
    if user_key not in chat_histories:
        chat_histories[user_key] = []
    
    # Add user message to chat history
    chat_histories[user_key].append({"sender": USER_NAME, "message": message.content})
    
    # Set typing indicator while processing
    async with message.channel.typing():
        # Call Chai API with the updated chat history
        bot_response = await call_chai_api(
            prompt=BOT_PROMPT,
            bot_name=BOT_NAME,
            user_name=USER_NAME,
            chat_history=chat_histories[user_key]
        )
    
    # Add bot response to chat history
    chat_histories[user_key].append({"sender": BOT_NAME, "message": bot_response})
    
    # Send response to Discord
    await message.reply(bot_response)

@bot.command(name="start")
async def start_chat(ctx):
    """Start a chat session in the current channel."""
    channel_id = ctx.channel.id
    
    # Add the channel to active channels
    active_channels.add(channel_id)
    
    await ctx.send(f"Chat session started in this channel! Just talk normally and I'll respond.")

@bot.command(name="stop")
async def stop_chat(ctx):
    """Stop the bot from responding in the current channel."""
    channel_id = ctx.channel.id
    
    # Remove the channel from active channels
    if channel_id in active_channels:
        active_channels.remove(channel_id)
        await ctx.send("Chat session ended. I'll no longer respond to messages in this channel unless you use commands.")
    else:
        await ctx.send("There's no active chat session in this channel.")

@bot.command(name="chat")
async def chat(ctx, *, message: str):
    """Chat with the Chai bot (alternative to direct messaging)."""
    channel_id = ctx.channel.id
    user_id = ctx.author.id
    user_key = f"{channel_id}_{user_id}"
    
    # Initialize chat history for new users
    if user_key not in chat_histories:
        chat_histories[user_key] = []
    
    # Add user message to chat history
    chat_histories[user_key].append({"sender": USER_NAME, "message": message})
    
    # Set typing indicator while processing
    async with ctx.typing():
        # Call Chai API with the updated chat history
        bot_response = await call_chai_api(
            prompt=BOT_PROMPT,
            bot_name=BOT_NAME,
            user_name=USER_NAME,
            chat_history=chat_histories[user_key]
        )
    
    # Add bot response to chat history
    chat_histories[user_key].append({"sender": BOT_NAME, "message": bot_response})
    
    # Send response to Discord
    await ctx.reply(bot_response)

@bot.command(name="clear")
async def clear(ctx):
    """Clear the chat history for the current user in the current channel."""
    channel_id = ctx.channel.id
    user_id = ctx.author.id
    user_key = f"{channel_id}_{user_id}"
    
    if user_key in chat_histories:
        chat_histories[user_key] = []
        await ctx.reply("Your chat history has been cleared.")
    else:
        await ctx.reply("You don't have any chat history to clear.")

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors."""
    if isinstance(error, commands.CommandNotFound):
        return
    await ctx.reply(f"An error occurred: {str(error)}")

if __name__ == "__main__":
    if DISCORD_TOKEN == "YOUR_DISCORD_BOT_TOKEN":
        print("Please set your Discord bot token in the DISCORD_TOKEN environment variable.")
        print("Example: export DISCORD_TOKEN=your_token_here")
        exit(1)
    
    print("Starting Discord bot...")
    bot.run(DISCORD_TOKEN)