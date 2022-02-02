import logging
import os
import random
import re
import time
from typing import Any, Dict

import discord

from google.cloud import texttospeech

TOKEN = os.getenv('DISCORD_TOKEN')
formatter = '%(levelname)s : %(asctime)s : %(message)s'
logging.basicConfig(level=logging.DEBUG, format=formatter)

# limited server can use
ALLOWED_SERVERS = list(map(int, os.getenv('ALLOWED_SERVERS').split(',')))
BOT_NAME = 'JoyTalk'


class JoyTalk(discord.Client):
    VOICE_CLIENTS: Dict[Any, Any] = {}
    MENTIONS: Dict[int, Dict] = {}
    CHATS: Dict[int, Dict] = {}
    TTS_CLIENT = texttospeech.TextToSpeechClient()

    def __init__(self, intents):
        super().__init__(intents=intents)

    async def on_ready(self):
        for guild in self.guilds:
            logging.info(f"- {guild.id} (name: {guild.name})")
            self.MENTIONS[guild.id] = {}

        logging.info(
            f"{BOT_NAME} has joined in {len(self.guilds)} server(s)")

    async def on_message(self, message):

        voice_state = message.author.voice

        if message.author.bot:
            return

        content = self._replace_mention(message.content, message.guild.id)
        # this won't work unless enable mapping user id and display name
        if content == 'アット' + BOT_NAME + " hey!":
            botnick = self._get_botnick(message)
            await message.channel.send(f"""
                ```\
                **{botnick}の使い方**\n
**`/jt s`**:  {botnick}の利用を開始
**`/jt e`**:  {botnick}の利用を終了

VC内にBOT一人になったら自動で抜けます

※ 勢いで作ったので足りないところは随時更新します！
※ 反応するサーバーを限定しています
（故に他のサーバーではBOTをサーバーに招待はできても使えはしないです）

製作者: ゆーすけ
```
                """)
        elif content == '/jtstart' or content == '/jt s':
            botnick = self._get_botnick(message)
            if not message.author.bot and message.guild.id not in ALLOWED_SERVERS:
                await message.channel.send(f"β版なためこのサーバーでは{botnick}は使えません")
            else:
                if self.VOICE_CLIENTS.get(message.guild.id, None):
                    await message.channel.send(
                        f"すでに'{self.VOICE_CLIENTS[message.guild.id].channel.name}'のvcに入っています"
                    )

                if voice_state:
                    self.CHATS[message.guild.id] = message.channel
                    self.VOICE_CLIENTS[
                        message.guild.id] = await voice_state.channel.connect(
                        )
                    desc = f"""**`/jt s`**:  {botnick}の利用を開始
**`/jt e`**:  {botnick}の利用を終了\n
いつもありがとうございます:bow:
                    """
                    embeded_message = discord.Embed(colour=discord.Color(10).from_rgb(153, 0, 255),
                            title=f":arrow_forward: {botnick} 使い方",
                            description=desc)
                    await message.channel.send(embed=embeded_message)
                else:
                    await message.channel.send("先にボイスチャンネルに入ってください")
            self._update_members(message.guild)

        elif content == '/jtend' or content == '/jt e':
            botnick = self._get_botnick(message)
            if not message.author.bot and message.guild.id not in ALLOWED_SERVERS:
                await message.channel.send(f"β版なためこのサーバーでは{botnick}は使えません")
            elif self.VOICE_CLIENTS.get(message.guild.id, None):
                vc = self.VOICE_CLIENTS[message.guild.id]
                self.VOICE_CLIENTS[message.guild.id] = None
                try:
                    await vc.disconnect()
                except AttributeError:
                    logging.info("VC is already disconnected")
            self._update_members(message.guild)

        elif voice_state and self.VOICE_CLIENTS.get(
                message.guild.id, None) and self.CHATS.get(
                    message.guild.id, None) and self.CHATS.get(
                        message.guild.id).id == message.channel.id:
            voice_path = self._generate_audio(content)
            self._play(voice_path, self.VOICE_CLIENTS[message.guild.id])
            self._update_members(message.guild)

    async def on_voice_state_update(self, member, before, after):
        if not after.channel:
            text_channel = self.CHATS[member.guild.id]
            self.CHATS[member.guild.id] = None
            await text_channel.send("お疲れ様でした:video_game:")
        elif before.channel and len(
                before.channel.members
        ) < 2 and member.name != BOT_NAME and before.channel.id == self.VOICE_CLIENTS[
                member.guild.id].channel.id:
            vc = self.VOICE_CLIENTS[member.guild.id]
            text_channel = self.CHATS[member.guild.id]
            self.VOICE_CLIENTS[member.guild.id] = None
            self.CHATS[member.guild.id] = None
            try:
                await vc.disconnect()
            except AttributeError:
                logging.info("VC is already disconnected")

            await text_channel.send("お疲れ様でした:video_game:")

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

        path = os.path.abspath(os.curdir) + "%032x" % random.getrandbits(64) + ".mp3"
        with open(path, "wb") as o:
            o.write(resp.audio_content)

        return path

    def _play(self, path, vc):
        ffmpeg_audio = discord.FFmpegPCMAudio(path)
        while vc.is_playing():
            try:
                time.sleep(1)
            except:
                pass

        vc.play(ffmpeg_audio)

    def _get_botnick(self, message):
        return message.guild.me.nick

    def _update_members(self, guild):
        print(guild.roles)
        ms = {}
        for m in guild.members:
            ms['a' + str(m.id)] = m.nick if m.nick else m.name # aをつけるのは後ほど値代入で置換するため

        for r in guild.roles:
            ms['a' + str(r.id)] = r.name

        self.MENTIONS[guild.id] = ms
        return None

    def _replace_mention(self, text, guild_id):
        if re.match(r'<@(!|&)\d+>', text):
            subbed_text = re.sub(r'<@(!|&)(\d+)>', r'あっと{a\2}', text)
            return subbed_text.format(**self.MENTIONS[guild_id])
        
        return text


if __name__ == "__main__":
    intents = discord.Intents.all()
    bot = JoyTalk(intents)
    bot.run(TOKEN)
