import discord
from redbot.core import commands
from PIL import Image, ImageFont, ImageDraw, ImageStat
import textwrap
from io import BytesIO

class CafeWelcome(commands.Cog):
    """ An Ascii themed Welcome GIF."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        avatar = await member.display_avatar.read()

        # Do it like this because the welcome image might take some time to make, and the bot would freeze otherwise.
        welcome_image = await self.bot.loop.run_in_executor(None, lambda: create_welcome(member, avatar, member.guild.member_count))
        
        welcome_channel = discord.utils.get(ctx.guild.text_channels, name="welcome")
        if welcome_channel:
            with open(welcome_image, "rb") as file:
                await welcome_channel.send(file=discord.File(file, "welcome.gif"))
        else:
            await ctx.send("The 'welcome' channel does not exist on this server.")

# Credit for the ascii art (it's slightly modified though) -> https://www.geeksforgeeks.org/converting-image-ascii-image-python/
    gscale1 = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. "

    gscale2 = ' .:-=+*#%@'

    def getAverageL(image: Image.Image):
        im = np.array(image)
        w, h = im.shape
        return np.average(im.reshape(w * h))

    def covertImageToAscii(IMAGE: Image.Image, cols: int, scale: float, moreLevels: bool):
        global gscale1, gscale2
        image = IMAGE.convert('L')
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
                avg = int(getAverageL(img))

                if moreLevels:
                    gsval = gscale1[int((avg * 69) / 255)]
                else:
                    gsval = gscale2[int((avg * 9) / 255)]

                aimg[j] += gsval
        return aimg

    def ascii_art(image: BytesIO, more_levels=False):
        scale = 0.65
        cols = 100

        image = Image.open(image)

        aimg = covertImageToAscii(image, cols, scale, more_levels)
        return aimg

    def brightness_level(image: Image.Image):
        image = image.convert('L')
        stat = ImageStat.Stat(image)
        return stat.mean[0]

    def create_welcome(user: discord.Member, user_avatar, join_pos):
        canvas = Image.new('RGB', (600, 250), (0, 0, 0, 1))

        image_array = [canvas]

        text_color = (108, 247, 80)
        info_font = ImageFont.truetype("assets/fonts/terminal.ttf", size=15)
        welcome_font = ImageFont.truetype("assets/fonts/terminal.ttf", size=20)
        name_font = ImageFont.truetype("assets/fonts/terminal.ttf", size=30)
        ascii_font = ImageFont.truetype("assets/fonts/terminal.ttf", size=3)
        WELCOME_TEXT = "Welcome to BytesToBits,"
        NAME_TEXT = user.name
        INFO_TEXT = [
            f"Subject ID: #{str(join_pos).zfill(4)}",
            user.created_at.strftime("Since %B %d, %Y"),
            f"Status: {user.status.name.upper()}",
            f"Activity:",
        ] + textwrap.wrap(user.activity.name if user.activity else "UNDETECTED", 25)

        for letter_range in range(len(WELCOME_TEXT)):
            im = image_array[-1].copy()
            draw = ImageDraw.Draw(im)
            draw.text((5 + (welcome_font.size - 5) * letter_range, 5), WELCOME_TEXT[letter_range], fill=text_color, font=welcome_font)
            image_array.append(im)

        # DELAY BEFORE WRITING THE NAME
        image_array += [image_array[-1] for _ in range(2)]

        for letter_range in range(len(NAME_TEXT)):
            im = image_array[-1].copy()
            draw = ImageDraw.Draw(im)
            draw.text((5 + (name_font.size - 10) * letter_range, 30), NAME_TEXT[letter_range], fill=text_color, font=name_font)
            image_array.append(im)

        # DELAY BEFORE WRITING THE INFO
        image_array += [image_array[-1] for _ in range(2)]

        for (index, line) in enumerate(INFO_TEXT):
            for letter_range in range(len(line)):
                im = image_array[-1].copy()
                draw = ImageDraw.Draw(im)
                draw.text((5 + (info_font.size - 5) * letter_range, 80 + 20 * index), line[letter_range], fill=text_color, font=info_font)
                image_array.append(im)

        # DELAY BEFORE DRAWING THE IMAGE
        image_array += [image_array[-1] for _ in range(2)]

        brightness = brightness_level(Image.open(BytesIO(user_avatar)))
        ascii = ascii_art(BytesIO(user_avatar), more_levels=brightness > 170)

        if not ascii: return

        ascii_len = len(ascii) * ascii_font.size

        ascii_image = Image.new('RGB', (ascii_len, ascii_len), (0, 0, 0))
        draw = ImageDraw.Draw(ascii_image)

        for (index, line) in enumerate(ascii):
            im = ascii_image.copy()
            draw = ImageDraw.Draw(im)
            draw.text((0, ascii_font.size * index), line, fill=text_color, font=ascii_font)
            ascii_image = im
            im = image_array[-1].copy()
            im.paste(ascii_image.resize((250, 250)), (350, 0))
            image_array.append(im)

        img = BytesIO()
        canvas.save(img, "GIF", save_all=True, append_images=image_array[1:], duration=50)
        img.seek(0)

        return img
