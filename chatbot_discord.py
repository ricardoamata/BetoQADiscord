import discord

from chatbot import BetoQA

with open("token.txt", "r") as f:
    TOKEN = f.read()

client = discord.Client()
chatbot = BetoQA()

@client.event
async def on_ready():
    print(f"Loged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return
        
    content = str(message.content)

    bot_message = chatbot.process_message(content)
    print(bot_message)
    await message.channel.send(f"```\n{bot_message}\n```")


client.run(TOKEN)

