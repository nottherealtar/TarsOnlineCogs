#
#  _   _  ___ _____ _____ _   _ _____ ____  _____    _    _   _____  _    ____  
# | \ | |/ _ \_   _|_   _| | | | ____|  _ \| ____|  / \  | | |_   _|/ \  |  _ \ 
# |  \| | | | || |   | | | |_| |  _| | |_) |  _|   / _ \ | |   | | / _ \ | |_) |
# | |\  | |_| || |   | | |  _  | |___|  _ <| |___ / ___ \| |___| |/ ___ \|  _ < 
# |_| \_|\___/ |_|   |_| |_| |_|_____|_| \_\_____/_/   \_\_____|_/_/   \_\_| \_\
# 
#  Most of the logic is from https://gist.github.com/Nemika-Haj/294b06f9fca1493443efe156697e57ac

import discord
from io import BytesIO
import logging
import numpy as np
import os
from PIL import Image, ImageFont, ImageDraw, ImageStat
import textwrap
from types import SimpleNamespace
from typing import Union

from redbot.core import checks, commands, Config
from redbot.core.data_manager import bundled_data_path
from redbot.core.utils import can_user_send_messages_in

log = logging.getLogger("red.nottherealtar.cafewelcome")


class CafeWelcome(commands.Cog):
    """Welcome users to your server using BytesToBits' image generation."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = Config.get_conf(self, 2773481001, force_registration=True)

        default_guild = {"welcome_channel": None}

        self.config.register_guild(**default_guild)

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @checks.mod_or_permissions(manage_channels=True)
    @commands.guild_only()
    @commands.group()
    async def cwset(self, ctx: commands.Context):
        """Cafe Welcome Settings."""
        pass

    @cwset.command()
    async def show(self, ctx: commands.Context):
        """Show the current welcome channel."""
        welcome_channel = await self.config.guild(ctx.guild).welcome_channel()
        welcome_channel_obj = ctx.guild.get_channel(welcome_channel)
        channel_name = "No channel." if not welcome_channel_obj else welcome_channel_obj.mention
        await ctx.send(f"Welcome channel is currently set to: {channel_name}")

    @cwset.command()
    async def channel(
        self,
        ctx: commands.Context,
        channel: Union[discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.Thread] = None,
    ):
        """Set a current welcome channel."""
        if not channel:
            channel = ctx.channel
        if not channel.permissions_for(ctx.me).read_messages:
            return await ctx.send("I don't have permissions to read that channel.")
        if not can_user_send_messages_in(ctx.me, channel):
            return await ctx.send("I don't have permissions to send messages in that channel.")
        author_perms = channel.permissions_for(ctx.author)
        if not author_perms.read_messages:
            return await ctx.send("You don't have permissions to read that channel.")
        await self.config.guild(ctx.guild).welcome_channel.set(channel.id)
        await ctx.send(f"Welcome channel set to {channel.mention}")

    @checks.is_owner()
    @cwset.command()
    async def join(self, ctx, member: discord.Member):
        """[Owner] Test creating the join message."""
        await ctx.typing()
        welcome_channel = await self.config.guild(member.guild).welcome_channel()
        if welcome_channel:
            welcome_channel_obj = member.guild.get_channel(welcome_channel)
            if welcome_channel_obj:
                welcome_image = await self._create_b2b_welcome(member)
                welcome_file = discord.File(fp=welcome_image, filename=f"welcome_{member.id}_{member.guild.id}.gif")
                await welcome_channel_obj.send(file=welcome_file)
        else:
            await ctx.send("No welcome channel set, or channel is unavailable.")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        welcome_channel = await self.config.guild(member.guild).welcome_channel()
        if welcome_channel:
            welcome_channel_obj = member.guild.get_channel(welcome_channel)
            if welcome_channel_obj:
                welcome_image = await self._create_b2b_welcome(member)
                welcome_file = discord.File(fp=welcome_image, filename=f"welcome_{member.id}_{member.guild.id}.gif")
                await welcome_channel_obj.send(file=welcome_file)

    @staticmethod
    def _get_average_l(image: Image.Image):
        im = np.array(image)
        w, h = im.shape
        return np.average(im.reshape(w * h))

    def _convert_image_to_ascii(self, IMAGE: Image.Image, cols: int, scale: float, moreLevels: bool):
        """https://www.geeksforgeeks.org/converting-image-ascii-image-python/"""

        image = IMAGE.convert("L")
        W, H = image.size
        w = W / cols
        h = w / scale
        rows = int(H / h)

        if cols > W or rows > H:
            return None

        aimg = []
        for j in range(rows):
            y1 = int(j * h)
            y2 = int((j + 1) * h)

            if j == rows - 1:
                y2 = H

            aimg.append("")

            for i in range(cols):
                x1 = int(i * w)
                x2 = int((i + 1) * w)
                if i == cols - 1:
                    x2 = W
                img = image.crop((x1, y1, x2, y2))
                avg = int(self._get_average_l(img))

                gscale1 = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "
                gscale2 = " .:-=+*#%@"

                if moreLevels:
                    gsval = gscale1[int((avg * 69) / 255)]
                else:
                    gsval = gscale2[int((avg * 9) / 255)]

                aimg[j] += gsval
        return aimg

    async def _ascii_art(self, image: BytesIO, more_levels=False):
        scale = 0.65
        cols = 100

        image = Image.open(image)

        aimg = self._convert_image_to_ascii(image, cols, scale, more_levels)
        return aimg

    @staticmethod
    def _brightness_level(image: Image.Image):
        image = image.convert("L")
        stat = ImageStat.Stat(image)
        return stat.mean[0]

    async def _create_b2b_welcome(self, member: discord.Member):
        try:
            canvas = Image.new("RGB", (600, 250), (0, 0, 0, 1))
            image_array = [canvas]
            text_color = (108, 247, 80)

            info_font = ImageFont.truetype(f"{bundled_data_path(self)}{os.sep}pixelscr.ttf", size=15)

            if len(member.guild.name) <= 22:
                welcome_font = ImageFont.truetype(f"{bundled_data_path(self)}{os.sep}pixelscr.ttf", size=20)
            elif 23 <= len(member.guild.name) <= 30:
                welcome_font = ImageFont.truetype(f"{bundled_data_path(self)}{os.sep}pixelscr.ttf", size=15)
            else:
                welcome_font = ImageFont.truetype(f"{bundled_data_path(self)}{os.sep}pixelscr.ttf", size=10)

            if len(member.name) <= 17:
                name_font = ImageFont.truetype(f"{bundled_data_path(self)}{os.sep}pixelscr.ttf", size=30)
            elif 18 <= len(member.name) <= 20:
                name_font = ImageFont.truetype(f"{bundled_data_path(self)}{os.sep}pixelscr.ttf", size=25)
            elif 21 <= len(member.name) <= 25:
                name_font = ImageFont.truetype(f"{bundled_data_path(self)}{os.sep}pixelscr.ttf", size=20)
            elif 26 <= len(member.name) <= 30:
                name_font = ImageFont.truetype(f"{bundled_data_path(self)}{os.sep}pixelscr.ttf", size=17)
            else:
                name_font = ImageFont.truetype(f"{bundled_data_path(self)}{os.sep}pixelscr.ttf", size=15)

            ascii_font = ImageFont.truetype(f"{bundled_data_path(self)}{os.sep}IBM-Courier-Bold.ttf", size=3)

            WELCOME_TEXT = ["Welcome to ", f"{member.guild.name},"]
            NAME_TEXT = member.name
            INFO_TEXT = [
                f"Subject ID: #{str(member.guild.member_count).zfill(4)}",
                member.created_at.strftime("Since %B %d, %Y"),
                f"Status: {member.status.name.upper()}",
            ] + textwrap.wrap(f"Activity: {member.activity.name if member.activity else 'UNDETECTED'}", 34)

            for index, line in enumerate(WELCOME_TEXT):
                for letter_range in range(len(line)):
                    im = image_array[-1].copy()
                    draw = ImageDraw.Draw(im)
                    draw.text(
                        (5 + (welcome_font.size - 5) * letter_range, 5 + 20 * index),
                        line[letter_range],
                        fill=text_color,
                        font=welcome_font,
                    )
                    image_array.append(im)

            # DELAY BEFORE WRITING THE NAME
            image_array += [image_array[-1] for _ in range(2)]

            for letter_range in range(len(NAME_TEXT)):
                im = image_array[-1].copy()
                draw = ImageDraw.Draw(im)
                draw.text(
                    (5 + (name_font.size - 10) * letter_range, 30 + 30),
                    NAME_TEXT[letter_range],
                    fill=text_color,
                    font=name_font,
                )
                image_array.append(im)

            # DELAY BEFORE WRITING THE INFO
            image_array += [image_array[-1] for _ in range(2)]

            for index, line in enumerate(INFO_TEXT):
                for letter_range in range(len(line)):
                    im = image_array[-1].copy()
                    draw = ImageDraw.Draw(im)
                    draw.text(
                        (5 + (info_font.size - 5) * letter_range, 30 + 80 + 20 * index),
                        line[letter_range],
                        fill=text_color,
                        font=info_font,
                    )
                    image_array.append(im)

            # DELAY BEFORE DRAWING THE IMAGE
            image_array += [image_array[-1] for _ in range(2)]

            user_avatar = await member.display_avatar.read()
            brightness = self._brightness_level(Image.open(BytesIO(user_avatar)))
            ascii = await self._ascii_art(BytesIO(user_avatar), more_levels=brightness > 170)

            if not ascii:
                return

            ascii_len = len(ascii) * ascii_font.size

            ascii_image = Image.new("RGB", (ascii_len, ascii_len), (0, 0, 0))
            draw = ImageDraw.Draw(ascii_image)

            for index, line in enumerate(ascii):
                im = ascii_image.copy()
                draw = ImageDraw.Draw(im)
                draw.text((0, ascii_font.size * index), line, fill=text_color, font=ascii_font)
                ascii_image = im
                im = image_array[-1].copy()
                im.paste(ascii_image.resize((250, 250)), (368, 0))
                image_array.append(im)

            img = BytesIO()
            canvas.save(img, "GIF", save_all=True, append_images=image_array[1:], duration=50)
            img.seek(0)

            return img
        except Exception as e:
            log.error("CafeWelcome image generation exception:", exc_info=True)
