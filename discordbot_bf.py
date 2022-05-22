import asyncio
import re
from asyncio import sleep
from datetime import datetime
from difflib import get_close_matches

import cv2
import discord
import gspread
import numpy as np
import pyocr
import pyocr.builders
from discord import Embed
from discord.ui import Button, InputText, Modal, View
from neologdn import normalize
from oauth2client.service_account import ServiceAccountCredentials
from PIL import Image
from scipy.spatial import distance

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('makesomenoise-4243a19364b1.json', scope)
gc = gspread.authorize(credentials)
SPREADSHEET_KEY = '1WcwdGVf7NRKerM1pnZu9kIsgA0VYy5TddyGdKHBzAu4'
workbook = gc.open_by_key(SPREADSHEET_KEY)
worksheet = workbook.worksheet('botデータベース（さわらないでね）')
intents = discord.Intents.all()  # デフォルトのIntentsオブジェクトを生成
intents.typing = False  # typingを受け取らないように
client = discord.Bot(intents=intents)
re_hiragana = re.compile(r'^[あ-んー]+$')
print("ビト森杯bot: 起動完了")

class ModalA(Modal):
    def __init__(self, name) -> None:
        super().__init__(title="A部門 読みがな登録")
        self.add_item(
            InputText(label=f"あなたの名前（{name}）の「読みがな」を、ひらがなで入力", placeholder=f"{name} の読みがな"))

    async def callback(self, interaction):
        channel = client.get_channel(916608669221806100)  # ビト森杯 進行bot
        if re_hiragana.fullmatch(self.children[0].value):
            try:
                entry_amount = int(worksheet.acell('J1').value) + 1
                worksheet.update_cell(1, 10, f"{entry_amount}")
                worksheet.update_cell(entry_amount + 1, 1, f"{interaction.user.display_name}")
                worksheet.update_cell(entry_amount + 1, 2, f"{self.children[0].value}")
                worksheet.update_cell(entry_amount + 1, 3, f"{interaction.user.id}")
            except gspread.exceptions.APIError:
                embed = Embed(title="Error", description="🇦部門 登録できませんでした。\n\nアクセス過多によるエラーです。\nお手数ですが、しばらく時間をおいてからもう一度お試しください。", color=0xff0000)
                await channel.send(interaction.user.mention, embed=embed)
                await interaction.response.send_message(interaction.user.mention, embed=embed, ephemeral=True)
                return
            embed = Embed(title="🇦部門 受付完了", description="エントリー受付が完了しました。", color=0x00ff00)
            embed.add_field(name=f"`名前：`{interaction.user.display_name}", value=f"`読み：`{self.children[0].value}", inline=False)
            role = interaction.guild.get_role(920320926887862323)  # A部門 ビト森杯
            await interaction.user.add_roles(role)
            await interaction.response.send_message("🇦部門 受付完了", ephemeral=True)  # 全ての作業が終わってから送信する！
            await channel.send(f"{interaction.user.mention}", embed=embed)
        else:
            embed = Embed(title="Error", description=f"🇦部門 登録できませんでした。\n読みがなは、ひらがな・伸ばし棒 `ー` のみで入力してください。\n\n入力内容：{self.children[0].value}", color=0xff0000)
            await channel.send(interaction.user.mention, embed=embed)
            await interaction.response.send_message(interaction.user.mention, embed=embed, ephemeral=True)

class ModalB(Modal):
    def __init__(self, name) -> None:
        super().__init__(title="🅱️部門 読みがな登録")
        self.add_item(
            InputText(label=f"あなたの名前（{name}）の「読みがな」を、ひらがなで入力", placeholder=f"{name} の読みがな"))

    async def callback(self, interaction):
        channel = client.get_channel(916608669221806100)  # ビト森杯 進行bot
        if re_hiragana.fullmatch(self.children[0].value):
            try:
                entry_amount = int(worksheet.acell('J2').value) + 1
                worksheet.update_cell(2, 10, f"{entry_amount}")
                worksheet.update_cell(entry_amount + 1, 5, f"{interaction.user.display_name}")
                worksheet.update_cell(entry_amount + 1, 6, f"{self.children[0].value}")
                worksheet.update_cell(entry_amount + 1, 7, f"{interaction.user.id}")
            except gspread.exceptions.APIError:
                embed = Embed(title="Error", description="🅱️部門 登録できませんでした。\n\nアクセス過多によるエラーです。\nお手数ですが、しばらく時間をおいてからもう一度お試しください。", color=0xff0000)
                await channel.send(interaction.user.mention, embed=embed)
                await interaction.response.send_message(interaction.user.mention, embed=embed, ephemeral=True)
                return
            embed = Embed(title="🅱️部門 受付完了", description="エントリー受付が完了しました。", color=0x00ff00)
            embed.add_field(name=f"`名前：`{interaction.user.display_name}", value=f"`読み：`{self.children[0].value}", inline=False)
            role = interaction.guild.get_role(920321241976541204)  # B部門 ビト森杯
            await interaction.user.add_roles(role)
            await interaction.response.send_message("🅱️部門 受付完了", ephemeral=True)  # 全ての作業が終わってから送信する！
            await channel.send(f"{interaction.user.mention}", embed=embed)
        else:
            embed = Embed(title="Error", description=f"🅱️部門 登録できませんでした。\n読みがなは、ひらがな・伸ばし棒 `ー` のみで入力してください。\n\n入力内容：{self.children[0].value}", color=0xff0000)
            await channel.send(interaction.user.mention, embed=embed)
            await interaction.response.send_message(interaction.user.mention, embed=embed, ephemeral=True)

@client.event
async def on_member_update(before, after):
    if before.display_name != after.display_name:
        roleA = after.get_role(920320926887862323)  # A部門 ビト森杯
        roleB = after.get_role(920321241976541204)  # B部門 ビト森杯
        admin = after.guild.get_role(904368977092964352)  # ビト森杯運営
        channel = client.get_channel(916608669221806100)  # ビト森杯 進行bot
        if roleA is None and roleB is None:
            return
        if roleA is not None and roleB is not None:
            await channel.send(f"{admin.mention} 重複エントリー検知\n\n{after.display_name} {after.id}")
        try:
            cell = worksheet.find(f'{after.id}')
        except gspread.exceptions.APIError:
            await channel.send(f"{admin.mention}\nError: gspread.exceptions.APIError\n\n{after.display_name} {after.id}")
            return
        if cell is None:
            if roleA is None:
                await channel.send(f"{admin.mention} データベース破損検知\n\n{after.display_name} {after.id}\nB部門")
                return
            if roleB is None:
                await channel.send(f"{admin.mention} データベース破損検知\n\n{after.display_name} {after.id}\nA部門")
                return
        try:
            right_name = worksheet.cell(cell.row, cell.col - 2).value
        except gspread.exceptions.APIError:
            await channel.send(f"{admin.mention}\nError: gspread.exceptions.APIError\n\n{after.display_name} {after.id}")
            return
        if after.display_name != right_name:
            await after.edit(nick=right_name)
            await channel.send(f"{after.mention}\nエントリー後のニックネーム変更は禁止されています\nchanging nickname after entry is prohibited")
        bot_channel = client.get_channel(897784178958008322)  # bot用チャット
        await bot_channel.send(f"ニックネーム変更検知\n\nbefore: {before.display_name}\nafter: {after.display_name}\nid: {after.id}")
        return

@client.event
async def on_message(message):
    if message.author.id == message.guild.me.id:
        return

    emoji_list = ["⭕", "❌"]
    if message.content.startswith("contact:"):
        admin = message.guild.get_role(904368977092964352)  # ビト森杯運営
        await message.channel.send(admin.mention)
        input_ = [j for j in message.content.split()]
        member = message.guild.get_member(int(input_[1]))
        roleA = member.get_role(920320926887862323)  # A部門 ビト森杯
        roleB = member.get_role(920321241976541204)  # B部門 ビト森杯
        if roleA is None and roleB is None:
            embed = Embed(description="ビト森杯にエントリーしていません")
            embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
            embed.add_field(name="ID", value=member.id, inline=False)
            embed.add_field(name="Discordユーザーネーム", value=f"{member.name}#{member.discriminator}", inline=False)
            await message.channel.send(embed=embed)
        elif roleA is not None and roleB is not None:
            embed = Embed(title="Error: 重複エントリーを検知", color=0xff0000)
            embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
            embed.add_field(name="ID", value=member.id, inline=False)
            embed.add_field(name="Discordユーザーネーム", value=f"{member.name}#{member.discriminator}", inline=False)
            await message.channel.send(f"{admin.mention}", embed=embed)
        else:
            if roleA is not None:
                category = "🇦 ※マイク設定確認不要"
            elif roleB is not None:
                category = "🅱️部門"
            try:
                cell = worksheet.find(f'{member.id}')
            except gspread.exceptions.APIError:
                await message.channel.send("Error: gspread.exceptions.APIError")
                return
            if cell is None:
                embed = Embed(title="Error: DB検索結果なし", color=0xff0000)
                embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
                embed.add_field(name="エントリー部門", value=category, inline=False)
                embed.add_field(name="ID", value=member.id, inline=False)
                embed.add_field(name="Discordユーザーネーム", value=f"{member.name}#{member.discriminator}", inline=False)
                check_mic = member.get_role(952951691047747655)  # verified
                if check_mic is None and category == "🅱️部門":
                    embed.add_field(name="マイク設定確認", value="❌", inline=False)
                elif check_mic is not None and category == "🅱️部門":
                    embed.add_field(name="マイク設定確認", value="⭕確認済み", inline=False)
                await message.channel.send(f"{admin.mention}", embed=embed)
            else:
                try:
                    read = worksheet.cell(cell.row, cell.col - 1).value
                except gspread.exceptions.APIError:
                    await message.channel.send("Error: gspread.exceptions.APIError")
                    return
                check_mic = member.get_role(952951691047747655)  # verified
                embed = Embed()
                embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
                embed.add_field(name="読みがな", value=read, inline=False)
                embed.add_field(name="エントリー部門", value=category, inline=False)
                embed.add_field(name="ID", value=member.id, inline=False)
                embed.add_field(name="Discordユーザーネーム", value=f"{member.name}#{member.discriminator}", inline=False)
                if check_mic is None and category == "🅱️部門":
                    embed.add_field(name="マイク設定確認", value="❌", inline=False)
                elif check_mic is not None and category == "🅱️部門":
                    embed.add_field(name="マイク設定確認", value="⭕確認済み", inline=False)
                await message.channel.send(embed=embed)
        await message.channel.send(f"{member.mention}\nご用件をこのチャンネルにご記入ください。\nplease write your inquiry here.")
        return

    if message.content.startswith("s.cancel"):
        await message.delete(delay=1)
        admin = message.author.get_role(904368977092964352)  # ビト森杯運営
        if admin is None:
            await message.channel.send(f"{message.author.mention}\nError: s.cancelはビト森杯運営専用コマンドです\n\n`{message.content}`")
            return
        input_ = message.content[9:]  # s.cancel をカット
        try:
            member = message.guild.get_member(int(input_))
        except ValueError:
            member = message.guild.get_member_named(input_)
        if member is None:
            await message.channel.send("Error: 検索結果なし")
            return
        roleA = member.get_role(920320926887862323)  # A部門 ビト森杯
        roleB = member.get_role(920321241976541204)  # B部門 ビト森杯
        if roleA is None and roleB is None:
            await message.channel.send("%sさんはビト森杯にエントリーしていません" % (member.display_name))
            return
        notice = await message.channel.send(f"{member.display_name} さんのビト森杯エントリーを取り消します。\n\n⭕ `OK`\n❌ 中止")
        await notice.add_reaction("⭕")
        await notice.add_reaction("❌")

        def check(reaction, user):
            return user == message.author and str(reaction.emoji) in emoji_list and reaction.message == notice

        try:
            reaction, user = await client.wait_for('reaction_add', timeout=10.0, check=check)
        except asyncio.TimeoutError:
            await message.channel.send("Error: Timeout")
            return
        if str(reaction.emoji) == "❌":
            await message.channel.send(f"{user.mention}\n中止しました。")
            return
        await message.channel.send("処理中...", delete_after=5)
        try:
            cell = worksheet.find(f'{member.id}')
        except gspread.exceptions.APIError:
            await message.channel.send("Error: gspread.exceptions.APIError")
            return
        if cell is not None:
            try:
                worksheet.update_cell(cell.row, cell.col, '')
                worksheet.update_cell(cell.row, cell.col - 1, '')
                worksheet.update_cell(cell.row, cell.col - 2, '')
            except gspread.exceptions.APIError:
                await message.channel.send("Error: gspread.exceptions.APIError")
                return
            await message.channel.send(f"DB削除完了 `{cell.row}, {cell.col}`")
        else:
            await message.channel.send("Error: DB登録なし")
        channel = client.get_channel(916608669221806100)  # ビト森杯 進行bot
        if roleA is not None:
            await member.remove_roles(roleA)
            await message.channel.send("%sさんのビト森杯 🇦部門エントリーを取り消しました。" % (member.display_name))
            await channel.send("%sさんのビト森杯 🇦部門エントリーを取り消しました。" % (member.display_name))
        if roleB is not None:
            await member.remove_roles(roleB)
            await message.channel.send("%sさんのビト森杯 🅱️部門エントリーを取り消しました。" % (member.display_name))
            await channel.send("%sさんのビト森杯 🅱️部門エントリーを取り消しました。" % (member.display_name))
        return

    if message.content.startswith("s.s"):
        await message.delete(delay=1)
        admin = message.guild.get_role(904368977092964352)  # ビト森杯運営
        input_ = message.content[4:]
        try:
            member = message.guild.get_member(int(input_))
        except ValueError:
            member = message.guild.get_member_named(input_)
        embed = Embed(title="検索中...")
        embed_msg = await message.channel.send(embed=embed)
        if member is None:
            all_names = []
            for mem in message.guild.members:
                if not mem.bot:
                    all_names.append(mem.display_name)
            all_names_edited = [normalize(mem).lower() for mem in all_names]
            results_edited = get_close_matches(normalize(input_).lower(), all_names_edited, n=5, cutoff=0.3)
            stamps = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
            if len(results_edited) == 0:
                embed = Embed(title="検索結果なし", description=f"`検索ワード：`{input_}")
                await embed_msg.edit(embed=embed)
                return
            results = []
            embeds = []
            embed = Embed(title="検索結果", description=f"`検索ワード：`{input_}")
            embeds.append(embed)
            for i in range(len(results_edited)):
                index = all_names_edited.index(results_edited[i])
                result_member = message.guild.get_member_named(all_names[index])
                results.append(f"{result_member.name}#{result_member.discriminator}")
                embed = Embed(description=f"{stamps[i]}: {result_member.name}#{result_member.discriminator}", color=0x00bfff)
                embed.set_author(name=result_member.display_name, icon_url=result_member.display_avatar.url)
                await embed_msg.add_reaction(stamps[i])
                embeds.append(embed)
            await embed_msg.edit(embeds=embeds)

            def check(reaction, user):
                return user == message.author and str(reaction.emoji) in stamps and reaction.message == embed_msg

            try:
                reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await embed_msg.clear_reactions()
                return
            await embed_msg.clear_reactions()
            index_result = stamps.index(reaction.emoji)
            member = message.guild.get_member_named(results[index_result])
        roleA = member.get_role(920320926887862323)  # A部門 ビト森杯
        roleB = member.get_role(920321241976541204)  # B部門 ビト森杯
        if roleA is not None and roleB is not None:  # 重複エントリー警告
            embed = Embed(title="Error: 重複エントリーを検知", color=0xff0000)
            embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
            embed.add_field(name="ID", value=member.id, inline=False)
            embed.add_field(name="Discordユーザーネーム", value=f"{member.name}#{member.discriminator}", inline=False)
            await embed_msg.edit(admin.mention, embed=embed)
            return
        if roleA is None and roleB is None:  # 未エントリー
            embed = Embed(description="ビト森杯にエントリーしていません")
            embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
            embed.add_field(name="ID", value=member.id, inline=False)
            embed.add_field(name="Discordユーザーネーム", value=f"{member.name}#{member.discriminator}", inline=False)
            await embed_msg.edit(embed=embed)
            await embed_msg.add_reaction("🇦")
            await embed_msg.add_reaction("🅱️")

            def check(reaction, user):
                ab = ["🇦", "🅱️"]
                return user == message.author and str(reaction.emoji) in ab and reaction.message == embed_msg

            try:
                reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await embed_msg.clear_reactions()
                return
            await embed_msg.clear_reactions()
            category = str(reaction.emoji)
            while True:
                typing = await message.channel.send(f"{member.display_name} {category}部門 手動エントリー\n`cancelと入力するとキャンセルされます`\n名前の読みかたを入力してください：")

                def check(m):
                    return m.channel == message.channel and m.author == message.author

                try:
                    read = await client.wait_for('message', timeout=60.0, check=check)
                except asyncio.TimeoutError:
                    await message.channel.send("Error: timeout")
                    return
                if read.content == "cancel":
                    await message.channel.send("キャンセルしました。")
                    return
                if re_hiragana.fullmatch(read.content):
                    break
                await typing.delete()
                await read.delete()
                embed = Embed(description="登録できませんでした。\n読みがなは、ひらがな・伸ばし棒 `ー` のみで入力してください。", color=0xff0000)
                await message.channel.send(embed=embed, delete_after=5)
            await message.channel.send("処理中...", delete_after=5)
            try:
                if category == "🇦":
                    entry_amount = int(worksheet.acell('J1').value) + 1
                    place_key = 0
                    worksheet.update_cell(1, 10, entry_amount)
                    role = message.guild.get_role(920320926887862323)  # A部門 ビト森杯
                elif category == "🅱️":
                    entry_amount = int(worksheet.acell('J2').value) + 1
                    place_key = 4
                    worksheet.update_cell(2, 10, entry_amount)
                    role = message.guild.get_role(920321241976541204)  # B部門 ビト森杯
                worksheet.update_cell(entry_amount + 1, place_key + 1, member.display_name)
                worksheet.update_cell(entry_amount + 1, place_key + 2, read.content)
                worksheet.update_cell(entry_amount + 1, place_key + 3, f"{member.id}")
            except gspread.exceptions.APIError:
                await message.channel.send("Error: gspread.exceptions.APIError")
                return
            await member.add_roles(role)
            embed = Embed(title=f"{category}部門 受付完了", description="エントリー受付が完了しました。", color=0x00ff00)
            embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
            embed.add_field(name="読みがな", value=read.content, inline=False)
            await message.channel.send(embed=embed)
            channel = client.get_channel(916608669221806100)  # ビト森杯 進行bot
            await channel.send(embed=embed)
            return
        if roleA is not None:
            category = "🇦 ※マイク設定確認不要"
        elif roleB is not None:
            category = "🅱️部門"
        try:
            cell = worksheet.find(f'{member.id}')
        except gspread.exceptions.APIError:
            read = "gspread.exceptions.APIError"
        else:
            if cell is None:
                embed = Embed(title="Error: DB検索結果なし", color=0xff0000)
                embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
                embed.add_field(name="エントリー部門", value=category, inline=False)
                embed.add_field(name="ID", value=member.id, inline=False)
                embed.add_field(name="Discordユーザーネーム", value=f"{member.name}#{member.discriminator}", inline=False)
                await embed_msg.edit(admin.mention, embed=embed)
                return
            try:
                read = worksheet.cell(cell.row, cell.col - 1).value
            except gspread.exceptions.APIError:
                read = "gspread.exceptions.APIError"
        check_mic = member.get_role(952951691047747655)  # verified
        embed = Embed()
        embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        embed.add_field(name="読みがな", value=read, inline=False)
        embed.add_field(name="エントリー部門", value=category, inline=False)
        embed.add_field(name="ID", value=member.id, inline=False)
        embed.add_field(name="Discordユーザーネーム", value=f"{member.name}#{member.discriminator}", inline=False)
        if check_mic is None and category == "🅱️部門":
            embed.add_field(name="マイク設定確認", value="❌", inline=False)
            button = Button(label="verify", style=discord.ButtonStyle.success, emoji="🎙️")
            async def button_callback(interaction):
                admin = interaction.user.get_role(904368977092964352)  # ビト森杯運営
                if admin is not None:
                    channel = client.get_channel(897784178958008322)  # bot用チャット
                    await channel.send(f"interaction verify: {interaction.user.display_name}\nID: {interaction.user.id}")
                    verified = message.guild.get_role(952951691047747655)  # verified
                    await member.add_roles(verified)
                    await interaction.response.send_message(f"✅{member.display_name}にverifiedロールを付与しました。")
            button.callback = button_callback
            view = View()
            view.add_item(button)
            await embed_msg.edit(embed=embed, view=view)
            return
        if check_mic is not None:
            embed.add_field(name="マイク設定確認", value="⭕確認済み", inline=False)
        await embed_msg.edit(embed=embed)
        return

    if message.content.startswith("s.poll"):
        names = [(j) for j in message.content.split()]
        names.remove("s.poll")
        if len(names) != 2:
            await message.channel.send("Error: 入力方法が間違っています。")
            return
        embed = Embed(title="投票箱", description="1⃣ %s\n2⃣ %s" % (names[0], names[1]))
        poll = await message.channel.send(embed=embed)
        await poll.add_reaction("1⃣")
        await poll.add_reaction("2⃣")
        return

    if message.content.startswith("s.role"):
        await message.delete(delay=1)
        input_id = [(j) for j in message.content.split()]
        try:
            role = message.guild.get_role(int(input_id[1]))
        except ValueError:
            await message.channel.send("Error: ロールIDを入力してください")
            return
        else:
            try:
                role_member = role.members
            except AttributeError:
                await message.channel.send("Error: ロールが見つかりませんでした")
                return
            else:
                for member in role_member:
                    await message.channel.send(f"{member.display_name}, {member.id}")
                await message.channel.send("---finish---")
                return

    if message.content == "s.mt":
        await message.channel.send("メンテナンス中...")
        error = []
        roleA = message.guild.get_role(920320926887862323)  # A部門 ビト森杯
        roleB = message.guild.get_role(920321241976541204)  # B部門 ビト森杯
        memberA = set(roleA.members)
        memberB = set(roleB.members)
        mid_A = [member.id for member in roleA.members]
        mid_B = [member.id for member in roleB.members]
        try:
            DBidA_str = worksheet.col_values(3)
            DBidB_str = worksheet.col_values(7)
        except gspread.exceptions.APIError:
            await message.channel.send("Error: gspread.exceptions.APIError")
            return
        DBidA_str.remove("id")
        DBidB_str.remove("id")
        DBidA = [int(id) for id in DBidA_str]
        DBidB = [int(id) for id in DBidB_str]
        # メンテその1 重複ロール付与
        for member in memberA & memberB:
            error.append(f"・重複ロール付与\n{member.display_name}\nID: {member.id}")
        # メンテその2 ロール未付与
        for id in set(DBidA) - set(mid_A):
            member = message.guild.get_member(id)
            error.append(f"・🇦部門 ロール未付与\n{member.display_name}\nID: {member.id}")
        for id in set(DBidB) - set(mid_B):
            member = message.guild.get_member(id)
            error.append(f"・🅱️部門 ロール未付与\n{member.display_name}\nID: {member.id}")
        # メンテその3 DB未登録
        for id in set(mid_A) - set(DBidA):
            member = message.guild.get_member(id)
            error.append(f"・🇦部門 DB未登録\n{member.display_name}\nID: {member.id}")
        for id in set(mid_B) - set(DBidB):
            member = message.guild.get_member(id)
            error.append(f"・🅱️部門 DB未登録\n{member.display_name}\nID: {member.id}")
        # メンテその4 DB AB重複
        for id in set(DBidA) & set(DBidB):
            member = message.guild.get_member(id)
            error.append(f"・DB AB重複\n{member.display_name}\nID: {member.id}")
        if error == []:
            await message.channel.send("エラーなし")
            return
        await message.channel.send("<@412082841829113877>\n見つかったエラー：")
        for e in error:
            await message.channel.send(e)
        await message.channel.send("---finish---")
        return

    if len(message.attachments) != 2 and message.channel.id == 952946795573571654:  # 画像提出
        await message.delete(delay=1)
        await message.channel.send(f"{message.author.mention}\nError: 画像を2枚同時に投稿してください。")
        if len(message.attachments) == 1:
            await message.channel.send("画像1枚では、すべての設定項目が画像内に収まりません。")
        return

    if message.content == "button":
        if message.channel.id != 904367725416153118:  # ビト森杯 参加
            return
        await message.delete()
        buttonA = Button(label="Entry", style=discord.ButtonStyle.primary, emoji="🇦")
        buttonB = Button(label="Entry", style=discord.ButtonStyle.red, emoji="🅱️")
        channel = client.get_channel(897784178958008322)  # bot用チャット
        async def buttonA_callback(interaction):
            await interaction.response.send_modal(ModalA(interaction.user.display_name))
            await channel.send(f"interaction🇦: {interaction.user.display_name}\nID: {interaction.user.id}")
        async def buttonB_callback(interaction):
            await interaction.response.send_modal(ModalB(interaction.user.display_name))
            await channel.send(f"interaction🅱️: {interaction.user.display_name}\nID: {interaction.user.id}")
        buttonA.callback = buttonA_callback
        buttonB.callback = buttonB_callback
        view = View(timeout=None)
        view.add_item(buttonA)
        view.add_item(buttonB)
        await message.channel.send(view=view)
        return

    # 画像提出
    if len(message.attachments) == 2 and message.channel.id == 952946795573571654:
        # 初期設定
        contact = client.get_channel(920620259810086922)  # お問い合わせ
        overwrite = discord.PermissionOverwrite()
        overwrite.send_messages = False
        overwrite.view_channel = True
        roleA = message.guild.get_role(920320926887862323)  # A部門 ビト森杯
        roleB = message.guild.get_role(920321241976541204)  # B部門 ビト森杯
        await message.channel.set_permissions(roleA, overwrite=overwrite)
        await message.channel.set_permissions(roleB, overwrite=overwrite)
        overwrite.send_messages = True
        close_notice = await message.channel.send(f"一時的に提出受付をストップしています。しばらくお待ちください。\n\n※長時間続いている場合は、お手数ですが {contact.mention} までご連絡ください。")
        try:
            channel = await message.channel.create_thread(name=f"{message.author.display_name} 分析ログ", message=message)
        except AttributeError:
            await message.channel.set_permissions(roleA, overwrite=overwrite)
            await message.channel.set_permissions(roleB, overwrite=overwrite)
            await close_notice.delete()
            return
        embed = Embed(title="分析中...", description="0% 完了")
        status = await channel.send(embed=embed)
        tools = pyocr.get_available_tools()
        tool = tools[0]
        langs = tool.get_available_languages()
        lang = langs[1]
        file_names = []
        error_msg = []
        error_code = 0
        admin = message.guild.get_role(904368977092964352)  # ビト森杯運営
        for a in message.attachments:
            if a.content_type == "image/jpeg" or a.content_type == "image/png":
                if a.height < a.width:
                    await channel.send(f"{message.author.mention}\nbotでの画像分析ができない画像のため、運営による手動チェックに切り替えます。\nしばらくお待ちください。\n\n{admin.mention}")
                    await message.channel.set_permissions(roleA, overwrite=overwrite)
                    await message.channel.set_permissions(roleB, overwrite=overwrite)
                    await close_notice.delete()
                    return
                dt_now = datetime.now()
                name = "/tmp/" + dt_now.strftime("%H.%M.%S.png")  # "/tmp/" +
                await a.save(name)
                file_names.append(name)
                await sleep(1)
            else:
                await channel.send("Error: jpg, jpeg, png画像を投稿してください。")
                await message.channel.set_permissions(roleA, overwrite=overwrite)
                await message.channel.set_permissions(roleB, overwrite=overwrite)
                await close_notice.delete()
                return
        embed = Embed(title="分析中...", description="20% 完了")
        await status.edit(embed=embed)
        # 設定オン座標調査
        xy_list = []
        img0 = cv2.imread(file_names[0])
        img1 = cv2.imread(file_names[1])
        imgs = {"file0": img0, "file1": img1}
        for i in range(2):
            h, w, c = imgs[f"file{i}"].shape  # 高さ、幅
            print(h, w, c)
            # BGR色空間からHSV色空間への変換
            hsv = cv2.cvtColor(imgs[f"file{i}"], cv2.COLOR_BGR2HSV)
            lower = np.array([113, 92, 222])  # 色検出しきい値の設定 (青)
            upper = np.array([123, 102, 242])
            # 色検出しきい値範囲内の色を抽出するマスクを作成
            frame_mask = cv2.inRange(hsv, lower, upper)
            cv2.bitwise_and(
                imgs[f"file{i}"], imgs[f"file{i}"], mask=frame_mask)  # 論理演算で色検出
            contours, hierarchy = cv2.findContours(
                frame_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # 輪郭抽出
            print(hierarchy)
            areas = np.array(list(map(cv2.contourArea, contours)))  # 面積を計算
            for j in range(len(areas)):
                result = cv2.moments(contours[j])
                try:
                    x = int(result["m10"] / result["m00"])
                except ZeroDivisionError:
                    continue
                try:
                    y = int(result["m01"] / result["m00"])
                except ZeroDivisionError:
                    continue
                xy_list.append([x, y])
            xy_list.append("|")  # ￥のキー
        separator = xy_list.index("|")
        xy_0 = xy_list[:separator]
        try:
            xy_1 = xy_list[separator + 1:]
        except IndexError:
            xy_1 = []
        else:
            xy_1.remove("|")
        embed = Embed(title="分析中...", description="40% 完了\n一番時間のかかる作業を行っています...")
        await status.edit(embed=embed)
        # モバイルボイスオーバーレイ検出
        for i in range(2):
            text_box1 = tool.image_to_string(Image.open(
                file_names[i]), lang=lang, builder=pyocr.builders.LineBoxBuilder(tesseract_layout=12))
            text_box2 = tool.image_to_string(Image.open(
                file_names[i]), lang=lang, builder=pyocr.builders.LineBoxBuilder(tesseract_layout=6))
            text_box_list = [text_box1, text_box2]
            for text_box in text_box_list:
                for texts in text_box:
                    if "モバイルボイスオーバーレイ" in texts.content.replace(' ', ''):
                        text_position = texts.position
                        place_text = [text_position[1][0], text_position[1][1]]
                        if i == 0:
                            for xy in xy_0:
                                if distance.euclidean(place_text, (xy)) < 200:
                                    xy_0.remove(xy)
                                    error_msg.append("・例外検知（問題なし）: モバイルボイスオーバーレイ")
                                    break
                        elif i == 1:
                            for xy in xy_1:
                                if distance.euclidean(place_text, (xy)) < 200:
                                    error_msg.append("・例外検知（問題なし）: モバイルボイスオーバーレイ")
                                    xy_1.remove(xy)
                                    break
        # ワード検出(下準備)
        all_text = ""
        for i in range(2):
            text1 = tool.image_to_string(Image.open(
                file_names[i]), lang=lang, builder=pyocr.builders.TextBuilder(tesseract_layout=12))
            text2 = tool.image_to_string(Image.open(
                file_names[i]), lang=lang, builder=pyocr.builders.TextBuilder(tesseract_layout=6))
            all_text += text1 + text2
        all_text = all_text.replace(' ', '')
        print(all_text)
        embed = Embed(title="分析中...", description="60% 完了")
        await status.edit(embed=embed)
        # ワード検出
        if "troubleshooting" in all_text:
            await channel.send("word found: troubleshooting")
            await channel.send(f"{message.author.mention}\nbotでの画像分析ができない画像のため、運営による手動チェックに切り替えます。\nしばらくお待ちください。\n\n{admin.mention}")
            await message.channel.set_permissions(roleA, overwrite=overwrite)
            await message.channel.set_permissions(roleB, overwrite=overwrite)
            await close_notice.delete()
            return
        word_list = ["自動検出", "ノイズ抑制", "エコー除去", "ノイズ低減", "音量調節の自動化", "高度音声検出"]
        if "ノイズ抑制" not in all_text:  # ノイズ抑制は認識精度低 「マイクからのバックグラウンドノイズ」で代用
            error_msg.append("・例外検知（問題なし）: ノイズ抑制検知失敗")
            word_list[1] = "バックグラウンドノイズ"
        for word in word_list:
            if word not in all_text:
                error_msg.append(f"・検知失敗: {word}")
                error_code += 1
        if error_code > 0:
            error_msg.append("上記の設定が映るようにしてください。")
        if "マイクのテスト" in all_text:
            error_msg.append('・「マイクのテスト」ボタンを押して、感度設定が見える状態にしてください。')
            error_code += 1
        if "ハードウェア" in all_text:
            error_msg.append('・「ハードウェア拡大縮小を有効にする」の項目が映らないようにしてください。')
            error_code += 1
        embed = Embed(title="分析中...", description="80% 完了")
        await status.edit(embed=embed)
        # オンの設定検出
        for xy in xy_0:
            error_code += 1
            cv2.circle(img0, (xy), 65, (0, 0, 255), 20)
        for xy in xy_1:
            error_code += 1
            cv2.circle(img1, (xy), 65, (0, 0, 255), 20)
        if len(xy_0) > 0 or len(xy_1) > 0:
            error_msg.append("・丸で囲われた設定をOFFにしてください。")
        embed = Embed(title="分析中...", description="100% 完了")
        await status.edit(embed=embed, delete_after=5)
        # 結果通知
        files = []
        if error_code == 0:
            color = 0x00ff00
            description = "問題なし\n\n🙇‍♂️ご協力ありがとうございました！🙇‍♂️\n※以下のエラーログの内容にかかわらず、提出内容に問題はありません。ご安心ください。\n"
            verified = message.guild.get_role(952951691047747655)  # verified
            await message.author.add_roles(verified)
        else:
            color = 0xff0000
            description = f"以下の問題が見つかりました。\n内容に誤りがあると思われる場合、お手数ですが {contact.mention} までご連絡ください。\n\n"
            cv2.imwrite(file_names[0], img0)
            files.append(discord.File(file_names[0]))
            cv2.imwrite(file_names[1], img1)
            files.append(discord.File(file_names[1]))
        embed = Embed(
            title="分析結果", description=description, color=color)
        value = "なし"
        if len(error_msg) > 0:
            error_msg = str(error_msg)[1:-1]
            error_msg = error_msg.replace(',', '\n')
            value = '\n' + error_msg.replace('\'', '')
        embed.add_field(name="エラーログ", value=value, inline=False)
        await channel.send(content=f"{message.author.mention}", embed=embed, files=files)
        await message.channel.set_permissions(roleA, overwrite=overwrite)
        await message.channel.set_permissions(roleB, overwrite=overwrite)
        await close_notice.delete()
        return

client.run("OTUyOTYyOTAyMzI1ODg2OTg2.Yi9p3Q.bisIxDqKOMlESDLe1GBnvNseOBQ")
