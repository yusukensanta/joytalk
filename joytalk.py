import os
import logging
import discord

import random
from google.cloud import texttospeech
from typing import Dict, Any

TOKEN = os.getenv('DISCORD_TOKEN')
formatter = '%(levelname)s : %(asctime)s : %(message)s'
logging.basicConfig(level=logging.DEBUG, format=formatter)

# limited server can use
ALLOWED_SERVERS = list(map(int, os.getenv('ALLOWED_SERVERS').split(',')))
BOT_NAME = 'JoyTalk'


class JoyTalk(discord.Client):
    VOICE_CLIENTS: Dict[Any, Any] = {}
    CHATS: Dict[int, Dict] = {}
    TTS_CLIENT = texttospeech.TextToSpeechClient()

    async def on_ready(self):
        for guild in self.guilds:
            logging.info(f"- {guild.id} (name: {guild.name})")

        logging.info(
            f"JoyTalk(bot) has joined in {len(self.guilds)} server(s)")

    async def on_message(self, message):

        voice_state = message.author.voice

        if message.author.bot:
            return

        # this won't work unless enable mapping user id and display name
        if message.content == '@' + BOT_NAME:
            await message.channel.send("""
                ```
                **JoyTalk使い方**
                VCに入れる: /jt s
                VCから切る: /jt e

                その他機能
                VC内にBOT一人になったら自動で抜けます

                以上！

                ※ 勢いで作ったので足りないところは随時更新します！
                ※ 反応するサーバーをJOYNITEに限定しています
                （故に他のサーバーではBOTをサーバーに招待はできても使えはしないです）

                製作者: ゆーすけ
                ```
                """)
        elif message.content == '/jtstart' or message.content == '/jt s':
            if not message.author.bot and message.guild.id not in ALLOWED_SERVERS:
                await message.channel.send("β版なためこのサーバーではJoyTalkは使えません")
            else:
                if self.VOICE_CLIENTS.get(message.guild.id, None):
                    await message.channel.send(
                        f"すでに'{self.VOICE_CLIENTS[message.guild.id].channel.name}'のvcに入っています"
                    )

                if voice_state:
                    self.CHATS[message.guild.id] = message.channel.id
                    self.VOICE_CLIENTS[
                        message.guild.id] = await voice_state.channel.connect(
                        )
                else:
                    await message.channel.send("先にボイスチャンネルに入ってください")
        elif message.content == '/jtend' or message.content == '/jt e':
            if not message.author.bot and message.guild.name not in ALLOWED_SERVERS:
                await message.channel.send("β版なためこのサーバーではJoyTalkは使えません")
            elif self.VOICE_CLIENTS.get(message.guild.id, None):
                await self.VOICE_CLIENTS[message.guild.id].disconnect()

        elif voice_state and self.VOICE_CLIENTS.get(
                message.guild.id, None) and self.CHATS.get(
                    message.guild.id, None) and self.CHATS.get(
                        message.guild.id) == message.channel.id:
            voice_path = self._generate_audio(message.content)
            self._play(voice_path, self.VOICE_CLIENTS[message.guild.id])

    async def on_voice_state_update(self, member, before, after):
        if before.channel and len(
                before.channel.members) < 2 and member.name != BOT_NAME:
            vc = self.VOICE_CLIENTS[member.guild.id]
            self.VOICE_CLIENTS[member.guild.id] = None
            self.CHATS[member.guild.id] = None
            try:
                await vc.disconnect()
            except AttributeError:
                logging.info("VC is already disconnected")

        if before.channel and member.name == BOT_NAME:
            vc = self.VOICE_CLIENTS[member.guild.id]
            self.VOICE_CLIENTS[member.guild.id] = None
            try:
                await vc.disconnect()
            except AttributeError:
                logging.info("VC is already disconnected")

    def _generate_audio(self, content):
        s_input = texttospeech.SynthesisInput(text=content)
        voice = texttospeech.VoiceSelectionParams(
            language_code="ja_JP",
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL)
        config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3)
        resp = self.TTS_CLIENT.synthesize_speech(input=s_input,
                                                 voice=voice,
                                                 audio_config=config)

        path = "%032x" % random.getrandbits(64) + ".mp3"
        with open(path, "wb") as o:
            o.write(resp.audio_content)

        return path

    def _play(self, path, vc):
        ffmpeg_audio = discord.FFmpegPCMAudio(path)
        vc.play(ffmpeg_audio)


bot = JoyTalk()
bot.run(TOKEN)
