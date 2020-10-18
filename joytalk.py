import os
import logging
import discord

TOKEN = os.getenv('DISCORD_TOKEN')
formatter = '%(levelname)s : %(asctime)s : %(message)s'
logging.basicConfig(level=logging.DEBUG, format=formatter)


class JoyTalk(discord.Client):
    async def on_ready(self):
        for guild in self.guilds:
            logging.info(f"- {guild.id} (name: {guild.name})")

        logging.info(
            f"JoyTalk(bot) has joined in {len(self.guilds)} server(s)")

    async def on_message(self, message):
        voice_state = message.author.voice

        if message.author.bot:
            logging.info("message from myself, ignored")
            return

        if message.content == '/neko':
            logging.info(f"messaging in {message.channel.name}")
            await message.channel.send('/neko')

        if message.content == '/join':
            if voice_state:
                await voice_state.channel.connect()
            else:
                await message.channel.send("先にボイスチャンネルに入ってください")

        if voice_state:
            # vc = message.guild.voice_client
            logging.info("call gcp tts service")

    async def on_voice_state_update(self, member, before, after):
        if len(before.channel.members) < 2 and not after.channel:
            await before.channel.guild.voice_client.disconnect()

    def _read(self, message):
        logging.info(message)

    def _execute_tts(self, message):
        pass


bot = JoyTalk()
bot.run(TOKEN)
