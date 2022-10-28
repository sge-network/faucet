import datetime
import json
import discord
import requests
import redis
import os

db = redis.Redis()

intents = discord.Intents(messages=True, guilds=True, message_content=True)
client = discord.Client(intents=intents)

FAUCET_ENDPOINT = os.getenv('FAUCET_ENDPOINT', default='http://localhost:8000')


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

    if message.content.startswith('$request sge1'):
        words = message.content.split()
        author = str(message.author)
        addr = words[1]

        if db.exists(author):
            last_time = float(db.get(author))
            time_diff = datetime.datetime.now().timestamp() - last_time

            if (time_diff - last_time) < 86400.0:
                rsp_msg = "You can request coins no more than once every 24 hours."
                rsp_msg = rsp_msg + " The next attempt is possible after "

                next_time = last_time + 86400.0 - datetime.datetime.now().timestamp()
                rsp_msg = rsp_msg + str(datetime.timedelta(seconds=next_time))

                await message.channel.send(rsp_msg)
                return

        data = {'address': addr}

        rsp = requests.post(url=FAUCET_ENDPOINT, data=json.dumps(data))
        rsp_content = json.loads(rsp.content.decode('utf-8'))

        if not bool(rsp_content):
            rsp_msg = "Successfully transferred 1000SGE to " + addr
            db.setex(
                author,
                datetime.timedelta(days=1),
                datetime.datetime.now().timestamp()
            )
            await message.channel.send(rsp_msg)
        else:
            rsp_msg = "Failed to transfer tokens to " + addr + ". REASON: " + rsp.text
            await message.channel.send(rsp_msg)
    else:
        rsp_msg = "Badly Formatted Request. Use `$request sge1...`"
        await message.channel.send(rsp_msg)

discord_token = os.getenv('DISCORD_TOKEN')
client.run(discord_token)
