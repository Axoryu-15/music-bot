import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
import time

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

music_states = {}

class MusicState:
    def __init__(self):
        self.queue = []
        self.current_url = None
        self.voice = None
        self.start_time = 0

def get_state(guild):
    if guild.id not in music_states:
        music_states[guild.id] = MusicState()
    return music_states[guild.id]

async def get_audio_url(url):
    ydl_opts = {
        'format': 'bestaudio',
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info['url']

def play_next(ctx):
    state = get_state(ctx.guild)
    if state.queue:
        next_song = state.queue.pop(0)
        asyncio.run_coroutine_threadsafe(play_song(ctx, next_song), bot.loop)

async def play_song(ctx, url, seek_time=0):
    state = get_state(ctx.guild)

    if os.path.exists(url):
        source = discord.FFmpegPCMAudio(url)
    else:
        stream_url = await get_audio_url(url)
        source = discord.FFmpegPCMAudio(
            stream_url,
            before_options=f"-ss {seek_time}",
            options="-vn"
        )

    state.current_url = url
    state.start_time = time.time()

    state.voice.play(source, after=lambda e: play_next(ctx))

@bot.command()
async def join(ctx):
    if not ctx.author.voice:
        await ctx.send("Join a voice channel first.")
        return

    channel = ctx.author.voice.channel
    state = get_state(ctx.guild)

    if state.voice and state.voice.is_connected():
        await state.voice.move_to(channel)
    else:
        state.voice = await channel.connect(reconnect=True)

    await ctx.send("Connected to voice.")

@bot.command()
async def play(ctx, *, url):
    state = get_state(ctx.guild)
    if not state.voice:
        await ctx.send("Use !join first.")
        return
    await play_song(ctx, url)
    await ctx.send("Playing.")

@bot.command()
async def queue(ctx, *, url):
    state = get_state(ctx.guild)
    state.queue.append(url)
    await ctx.send("Added to queue.")

@bot.command()
async def skip(ctx):
    state = get_state(ctx.guild)
    state.voice.stop()
    await ctx.send("Skipped.")

@bot.command()
async def stop(ctx):
    state = get_state(ctx.guild)
    state.queue.clear()
    state.voice.stop()
    await ctx.send("Stopped and cleared queue.")

@bot.command()
async def seek(ctx, seconds: int):
    state = get_state(ctx.guild)
    if not state.current_url:
        return
    state.voice.stop()
    await play_song(ctx, state.current_url, seek_time=seconds)
    await ctx.send(f"Seeked to {seconds} seconds.")

import os

bot.run(os.getenv("TOKEN"))
