print("Bot file started")

import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

YDL_OPTIONS = {
    "format": "bestaudio",
    "noplaylist": True,
    "quiet": True,
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.command()
async def join(ctx):
    if not ctx.author.voice:
        await ctx.send("You are not in a voice channel.")
        return

    channel = ctx.author.voice.channel

    if ctx.voice_client:
        await ctx.voice_client.disconnect()

    await channel.connect()
    await ctx.send("Connected to voice channel.")


@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Disconnected.")
    else:
        await ctx.send("Not connected.")


@bot.command()
async def play(ctx, url):
    if not ctx.author.voice:
        await ctx.send("Join a voice channel first.")
        return

    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()

    voice_client = ctx.voice_client

    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(url, download=False)
        audio_url = info["url"]

    source = await discord.FFmpegOpusAudio.from_probe(
        audio_url,
        **FFMPEG_OPTIONS
    )

    voice_client.stop()
    voice_client.play(source)

    await ctx.send("Playing audio.")


bot.run(os.getenv("TOKEN"))

