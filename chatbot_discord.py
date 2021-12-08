import discord

from chatbot import BetoQA

TOKEN = 'OTE4MDU3NjgzMzA5OTU3MTIw.YbBt2A.WIq1_yR5yRUJChy9M1400eEfcFU'

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

