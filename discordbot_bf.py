import asyncio
import re
from difflib import get_close_matches

import discord
import gspread
from discord import Embed
from discord.ui import Button, InputText, Modal, View
from neologdn import normalize
from oauth2client.service_account import ServiceAccountCredentials
from PIL import Image, ImageDraw, ImageFont

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    'makesomenoise-4243a19364b1.json', scope)
gc = gspread.authorize(credentials)
SPREADSHEET_KEY = '1WcwdGVf7NRKerM1pnZu9kIsgA0VYy5TddyGdKHBzAu4'
workbook = gc.open_by_key(SPREADSHEET_KEY)
worksheet = workbook.worksheet('botデータベース（さわらないでね）')
intents = discord.Intents.all()  # デフォルトのIntentsオブジェクトを生成
intents.typing = False  # typingを受け取らないように
client = discord.Bot(intents=intents)
re_hiragana = re.compile(r'^[ぁ-ゞ　 ]+$')
print('ビト森杯bot: 起動完了')


green = 0x00ff00
yellow = 0xffff00
red = 0xff0000


class entry_modal(Modal):
    def __init__(self, name, category) -> None:
        super().__init__(title=f"{category}部門 読みがな登録", custom_id=category)
        self.add_item(
            InputText(label=f"あなたの名前（{name}）の「読みがな」を、ひらがなで入力", placeholder=f"{name} の読みがな（ひらがな）"))

    # self = modal.children(ユーザー入力内容), custom_id, title
    async def callback(self, interaction):
        bot_channel = client.get_channel(1035946838487994449)  # ビト森杯 進行bot
        bot_test_channel = client.get_channel(897784178958008322)  # bot用チャット
        roleA = bot_channel.guild.get_role(1035945116591996979)  # A部門 ビト森杯
        roleB = bot_channel.guild.get_role(1035945267733737542)  # B部門 ビト森杯
        admin = bot_channel.guild.get_role(904368977092964352)  # ビト森杯運営
        materials = {"A": {"role": roleA, "number": 1},
                     "B": {"role": roleB, "number": 2}}
        material = materials[self.custom_id]

        await interaction.response.defer(ephemeral=True, invisible=False)
        if re_hiragana.fullmatch(self.children[0].value):
            worksheet_check = ""
            await interaction.user.add_roles(material["role"])
            try:
                entry_amount = int(worksheet.acell(
                    f'J{material["number"]}').value) + 1
                worksheet.update_cell(
                    material["number"], 10, f"{entry_amount}")
                worksheet.update_cell(
                    entry_amount + 1, 1, interaction.user.display_name)
                worksheet.update_cell(
                    entry_amount + 1, 2, self.children[0].value)
                worksheet.update_cell(
                    entry_amount + 1, 3, f"{interaction.user.id}")
            except gspread.exceptions.APIError as e:
                worksheet_check = e
            embed = Embed(title=f"{self.custom_id}部門 受付完了",
                          description="ご参加ありがとうごさいます！", color=green)
            embed.add_field(name=f"`名前：`{interaction.user.display_name}",
                            value=f"`読み：`{self.children[0].value}", inline=False)
            notice_entry = await bot_channel.send(interaction.user.mention, embed=embed)
            embed.set_footer(text="bot制作: tari3210#9924")
            if bool(worksheet_check):
                embed_error = Embed(
                    title="データベース登録失敗", description=f"{worksheet_check}\n\nロール付与は完了しました。運営はデータベースの確認を行ってください\n\n※{interaction.user.display_name}さんのエントリー受付は完了しています。ご安心ください", color=yellow)
                await notice_entry.reply(admin.mention, embed=embed_error)
                await bot_test_channel.send(embed=embed_error)
            # 全ての作業が終わってから送信する！
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            embed = Embed(
                title="Error", description=f"{self.custom_id}部門 登録できませんでした。\n読みがなは、ひらがな・伸ばし棒 `ー` のみで入力してください。\n\n入力内容：{self.children[0].value}", color=red)
            await bot_channel.send(interaction.user.mention, embed=embed)
            embed.set_footer(text="bot制作: tari3210#9924")
            await interaction.followup.send(interaction.user.mention, embed=embed, ephemeral=True)


@client.event
async def on_member_update(before, after):
    roleA = after.get_role(1035945116591996979)  # A部門 ビト森杯
    roleB = after.get_role(1035945267733737542)  # B部門 ビト森杯
    admin = after.guild.get_role(904368977092964352)  # ビト森杯運営
    bot_channel = client.get_channel(1035946838487994449)  # ビト森杯 進行bot
    bot_test_channel = client.get_channel(897784178958008322)  # bot用チャット
    if before.display_name != after.display_name:
        if roleA is None and roleB is None:
            return
        if bool(roleA) and bool(roleB):
            embed = Embed(
                title=f"AB重複エントリー検知", description=f"{after.display_name}\n{after.id}", color=red)
            await bot_channel.send(admin.mention, embed=embed)
            await bot_test_channel.send(embed=embed)
        try:
            cell = worksheet.find(f'{after.id}')
        except gspread.exceptions.APIError as e:
            embed = Embed(title="ニックネーム変更検知",
                          description=f"APIError:\n{e}\n\n{after.id}", color=red)
            embed.add_field(
                name="before", value=before.display_name, inline=False)
            embed.add_field(
                name="after", value=after.display_name, inline=False)
            await bot_channel.send(admin.mention, embed=embed)
            await bot_test_channel.send(embed=embed)
            return
        if cell is None:
            embed = Embed(title="ニックネーム変更・データベース破損検知",
                          description=f"{after.id}", color=red)
            embed.add_field(
                name="before", value=before.display_name, inline=False)
            embed.add_field(
                name="after", value=after.display_name, inline=False)
            await bot_channel.send(admin.mention, embed=embed)
            await bot_test_channel.send(embed=embed)
            return
        try:
            right_name = worksheet.cell(cell.row, cell.col - 2).value
        except gspread.exceptions.APIError as e:
            embed = Embed(title="ニックネーム変更検知",
                          description=f"APIError:\n{e}\n\n{after.id}", color=red)
            embed.add_field(
                name="before", value=before.display_name, inline=False)
            embed.add_field(
                name="after", value=after.display_name, inline=False)
            await bot_channel.send(admin.mention, embed=embed)
            await bot_test_channel.send(embed=embed)
            return
        if after.display_name != right_name:
            await after.edit(nick=right_name)
            embed = Embed(
                title="WARNING", description=f"エントリー後のニックネーム変更は禁止されています\nchanging nickname after entry is prohibited", color=red)
            await bot_channel.send(after.mention, embed=embed)
        embed = Embed(title="ニックネーム変更検知", description=f"{after.id}", color=red)
        embed.add_field(name="before", value=before.display_name, inline=False)
        embed.add_field(name="after", value=after.display_name, inline=False)
        await bot_test_channel.send(embed=embed)
        return


@client.event
async def on_user_update(before, after):
    admin = after.guild.get_role(904368977092964352)  # ビト森杯運営
    bot_channel = client.get_channel(1035946838487994449)  # ビト森杯 進行bot
    bot_test_channel = client.get_channel(897784178958008322)  # bot用チャット
    if before.display_name != after.display_name:
        try:
            cell = worksheet.find(f'{after.id}')
        except gspread.exceptions.APIError as e:
            embed = Embed(title="アカウント名変更検知（エントリー状況不明）",
                          description=f"APIError:\n{e}\n\n{after.id}", color=red)
            embed.add_field(
                name="before", value=before.display_name, inline=False)
            embed.add_field(
                name="after", value=after.display_name, inline=False)
            await bot_test_channel.send(embed=embed)
            return
        if cell is None:
            return
        try:
            right_name = worksheet.cell(cell.row, cell.col - 2).value
        except gspread.exceptions.APIError as e:
            embed = Embed(title="アカウント名変更検知",
                          description=f"APIError:\n{e}\n\n{after.id}", color=red)
            embed.add_field(
                name="before", value=before.display_name, inline=False)
            embed.add_field(
                name="after", value=after.display_name, inline=False)
            await bot_channel.send(admin.mention, embed=embed)
            await bot_test_channel.send(embed=embed)
            return
        member = after.guild.get_member(after.id)
        if member.display_name != right_name:
            await member.edit(nick=right_name)
            embed = Embed(
                title="WARNING", description=f"エントリー後のニックネーム変更は禁止されています\nchanging nickname after entry is prohibited", color=red)
            await bot_channel.send(after.mention, embed=embed)
        embed = Embed(title="アカウント名変更検知", description=f"{after.id}", color=red)
        embed.add_field(name="before", value=before.display_name, inline=False)
        embed.add_field(name="after", value=after.display_name, inline=False)
        await bot_test_channel.send(embed=embed)
    return


@client.event
async def on_message(message):
    bot_channel = client.get_channel(1035946838487994449)  # ビト森杯 進行bot
    bot_test_channel = client.get_channel(897784178958008322)  # bot用チャット
    admin = message.guild.get_role(904368977092964352)  # ビト森杯運営
    roleA = member.get_role(1035945116591996979)  # A部門 ビト森杯
    roleB = member.get_role(1035945267733737542)  # B部門 ビト森杯
    image_channel = client.get_channel(952946795573571654)  # 画像提出
    verified = message.guild.get_role(952951691047747655)  # verified
    contact = client.get_channel(1035964918198960128)  # 問い合わせ
    main_ch = client.get_channel(1030840789040893962)  # メイン会場
    ox_list = ["⭕", "❌"]

    if message.author.id == 952962902325886986:  # ビト森杯bot
        return

    if message.content == "s.test":
        await message.channel.send(f"ビト森杯 (Local): {client.latency}")
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
        roleA = member.get_role(1035945116591996979)  # A部門 ビト森杯
        roleB = member.get_role(1035945267733737542)  # B部門 ビト森杯
        if roleA is None and roleB is None:
            await message.channel.send(f"{member.display_name}はビト森杯にエントリーしていません")
            return
        notice = await message.channel.send(f"{member.display_name}のビト森杯エントリーを取り消します。\n\n⭕ `OK`\n❌ 中止")
        await notice.add_reaction("⭕")
        await notice.add_reaction("❌")

        def check(reaction, user):
            return user == message.author and reaction.emoji in ox_list and reaction.message == notice

        try:
            reaction, user = await client.wait_for('reaction_add', timeout=10.0, check=check)
        except asyncio.TimeoutError:
            await message.channel.send("Error: Timeout")
            await notice.clear_reactions()
            return
        await notice.clear_reactions()
        if reaction.emoji == "❌":
            await message.channel.send(f"{user.mention}\n中止しました。")
            return
        await message.channel.send("処理中...", delete_after=5)
        try:
            cell = worksheet.find(f'{member.id}')
        except gspread.exceptions.APIError as e:
            await message.channel.send(f"Error: {e}")
            return
        if bool(cell):
            try:
                worksheet.update_cell(cell.row, cell.col, '')
                worksheet.update_cell(cell.row, cell.col - 1, '')
                worksheet.update_cell(cell.row, cell.col - 2, '')
            except gspread.exceptions.APIError as e:
                await message.channel.send(f"Error: {e}")
                return
            await message.channel.send(f"DB削除完了 `{cell.row}, {cell.col}`")
        else:
            await message.channel.send("Error: DB登録なし")
        if bool(roleA):
            await member.remove_roles(roleA)
            await message.channel.send(f"{member.display_name}のビト森杯 🇦部門エントリーを取り消しました。")
            await bot_test_channel.send(f"{member.display_name}のビト森杯 🇦部門エントリーを取り消しました。")
        if bool(roleB):
            await member.remove_roles(roleB)
            await message.channel.send(f"{member.display_name}のビト森杯 🅱️部門エントリーを取り消しました。")
            await bot_test_channel.send(f"{member.display_name}のビト森杯 🅱️部門エントリーを取り消しました。")
        return

    if message.content.startswith("s.s") and not message.content.startswith("s.start") and not message.content.startswith("s.stage"):
        await message.delete(delay=1)
        input_ = message.content[4:]
        if input_ == "":
            await message.channel.send("`cancelと入力するとキャンセルできます`\n検索したいワードを入力してください：")

            def check(m):
                return m.channel == message.channel and m.author == message.author

            try:
                msg2 = await client.wait_for('message', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await message.channel.send("Error: timeout")
                return
            if msg2.content == "cancel":
                await message.channel.send("キャンセルしました。")
                return
            if msg2.content.startswith("s.s"):
                return
            input_ = msg2.content
        try:
            member = message.guild.get_member(int(input_))
        except ValueError:
            member = message.guild.get_member_named(input_)
        embed = Embed(title="検索中...")
        embed_msg = await message.channel.send(embed=embed)
        if member is None:
            all_names = []
            for mem in message.guild.members:
                # RUSY, RUSY_2sub
                RUSY = [332886651107934219, 826371622084542474]
                if not mem.bot and mem.id not in RUSY:
                    all_names.append(mem.display_name)
            all_names_edited = [normalize(mem).lower() for mem in all_names]
            results_edited = get_close_matches(
                normalize(input_).lower(), all_names_edited, n=5, cutoff=0.3)
            stamps = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
            if len(results_edited) == 0:
                embed = Embed(title="検索結果なし", description=f"`検索ワード：`{input_}")
                await embed_msg.edit(embed=embed)
                await embed_msg.add_reaction("🗑️")

                def check(reaction, user):
                    return user == message.author and reaction.emoji == "🗑️" and reaction.message == embed_msg
                _, _ = await client.wait_for('reaction_add', check=check)
                await embed_msg.delete()
                return
            results = []
            embeds = []
            embed = Embed(title="検索結果", description=f"`検索ワード：`{input_}")
            embeds.append(embed)
            for i in range(len(results_edited)):
                index = all_names_edited.index(results_edited[i])
                result_member = message.guild.get_member_named(
                    all_names[index])
                results.append(result_member)
                embed = Embed(
                    description=f"{stamps[i]}: {result_member.name}#{result_member.discriminator}", color=0x00bfff)
                embed.set_author(name=result_member.display_name,
                                 icon_url=result_member.display_avatar.url)
                await embed_msg.add_reaction(stamps[i])
                embeds.append(embed)
            await embed_msg.edit(embeds=embeds)
            await embed_msg.add_reaction("🗑️")

            def check(reaction, user):
                return user == message.author and reaction.emoji in ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "🗑️"] and reaction.message == embed_msg

            try:
                reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await embed_msg.clear_reactions()
                await embed_msg.add_reaction("🗑️")

                def check(reaction, user):
                    return user == message.author and reaction.emoji == "🗑️" and reaction.message == embed_msg
                _, _ = await client.wait_for('reaction_add', check=check)
                await embed_msg.delete()
                return
            if reaction.emoji == "🗑️":
                await embed_msg.delete()
                return
            await embed_msg.clear_reactions()
            index_result = stamps.index(reaction.emoji)
            member = results[index_result]
        thread_names = [thread.name for thread in image_channel.threads]
        URLs = [thread.jump_url for thread in image_channel.threads]
        roleA = member.get_role(1035945116591996979)  # A部門 ビト森杯
        roleB = member.get_role(1035945267733737542)  # B部門 ビト森杯
        if bool(roleA) and bool(roleB):  # 重複エントリー警告
            embed = Embed(title="Error: 重複エントリーを検知",
                          description=member.mention, color=red)
            embed.set_author(name=f"{member.name}#{member.discriminator}",
                             icon_url=member.display_avatar.url)
            embed.add_field(name="ID", value=f"{member.id}", inline=False)
            for thread_name, URL in zip(thread_names, URLs):
                if member.display_name in thread_name:
                    embed.add_field(name="画像分析提出", value=URL, inline=False)
            await embed_msg.edit(admin.mention, embed=embed)
            await embed_msg.add_reaction("🗑️")

            def check(reaction, user):
                return user == message.author and reaction.emoji == "🗑️" and reaction.message == embed_msg
            _, _ = await client.wait_for('reaction_add', check=check)
            await embed_msg.delete()
            return
        if roleA is None and roleB is None:  # 未エントリー
            embed = Embed(description=f"{member.mention}\nビト森杯にエントリーしていません")
            embed.set_author(name=f"{member.name}#{member.discriminator}",
                             icon_url=member.display_avatar.url)
            embed.add_field(name="ID", value=f"{member.id}", inline=False)
            await embed_msg.edit(embed=embed)
            await embed_msg.add_reaction("🇦")
            await embed_msg.add_reaction("🅱️")
            await embed_msg.add_reaction("🗑️")

            def check(reaction, user):
                ab = ["🇦", "🅱️", "🗑️"]
                return user == message.author and reaction.emoji in ab and reaction.message == embed_msg

            try:
                reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await embed_msg.clear_reactions()
                await embed_msg.add_reaction("🗑️")

                def check(reaction, user):
                    return user == message.author and reaction.emoji == "🗑️" and reaction.message == embed_msg
                _, _ = await client.wait_for('reaction_add', check=check)
                await embed_msg.delete()
                return
            if reaction.emoji == "🗑️":
                await embed_msg.delete()
                return
            await embed_msg.clear_reactions()
            category = reaction.emoji
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
                embed = Embed(
                    description="登録できませんでした。\n読みがなは、ひらがな・伸ばし棒 `ー` のみで入力してください。", color=red)
                await message.channel.send(embed=embed, delete_after=5)
            await message.channel.send("処理中...", delete_after=5)
            worksheet_check = ""
            try:
                if category == "🇦":
                    entry_amount = int(worksheet.acell('J1').value) + 1
                    place_key = 0
                    worksheet.update_cell(1, 10, entry_amount)
                    role = message.guild.get_role(
                        1035945116591996979)  # A部門 ビト森杯
                elif category == "🅱️":
                    entry_amount = int(worksheet.acell('J2').value) + 1
                    place_key = 4
                    worksheet.update_cell(2, 10, entry_amount)
                    role = message.guild.get_role(
                        1035945267733737542)  # B部門 ビト森杯
                worksheet.update_cell(
                    entry_amount + 1, place_key + 1, member.display_name)
                worksheet.update_cell(
                    entry_amount + 1, place_key + 2, read.content)
                worksheet.update_cell(
                    entry_amount + 1, place_key + 3, f"{member.id}")
            except gspread.exceptions.APIError as e:
                worksheet_check = e
            await member.add_roles(role)
            embed = Embed(title=f"{category}部門 受付完了",
                          description=f"{member.mention}\nエントリー受付が完了しました。", color=green)
            embed.set_author(name=f"{member.name}#{member.discriminator}",
                             icon_url=member.display_avatar.url)
            embed.add_field(name="名前", value=member.display_name, inline=False)
            embed.add_field(name="読みがな", value=read.content, inline=False)
            await message.channel.send(embed=embed)
            notice_entry = await bot_channel.send(embed=embed)
            if bool(worksheet_check):
                embed = Embed(
                    title="データベース登録失敗", description=f"{worksheet_check}\n\nロール付与は完了しました。運営はデータベースの確認を行ってください\n\n※{member.display_name}さんのエントリー受付は完了しています。ご安心ください", color=yellow)
                await notice_entry.reply(admin.mention, embed=embed)
            embed_msg = await message.channel.send("処理中...")
            roleA = member.get_role(1035945116591996979)  # A部門 ビト森杯
            roleB = member.get_role(1035945267733737542)  # B部門 ビト森杯
        if bool(roleA):
            category = "A"
        elif bool(roleB):
            category = "🅱️部門"
        try:
            cell = worksheet.find(f'{member.id}')
        except gspread.exceptions.APIError as e:
            read = e
        else:
            if cell is None:
                embed = Embed(title="Error: DB検索結果なし",
                              description=member.mention, color=red)
                embed.set_author(name=f"{member.name}#{member.discriminator}",
                                 icon_url=member.display_avatar.url)
                embed.add_field(name="エントリー部門", value=category, inline=False)
                embed.add_field(name="ID", value=f"{member.id}", inline=False)
                for thread_name, URL in zip(thread_names, URLs):
                    if member.display_name in thread_name:
                        embed.add_field(name="画像分析提出", value=URL, inline=False)
                await embed_msg.edit(admin.mention, embed=embed)
                await embed_msg.add_reaction("🗑️")

                def check(reaction, user):
                    return user == message.author and reaction.emoji == "🗑️" and reaction.message == embed_msg
                _, _ = await client.wait_for('reaction_add', check=check)
                await embed_msg.delete()
                return
            try:
                read = worksheet.cell(cell.row, cell.col - 1).value
            except gspread.exceptions.APIError as e:
                read = f"Error: {e}"
            if read is None:
                read = "Error: DB検索結果なし"
        embed = Embed(description=member.mention)
        embed.set_author(name=f"{member.name}#{member.discriminator}",
                         icon_url=member.display_avatar.url)
        embed.add_field(name="読みがな", value=read, inline=False)
        embed.add_field(name="エントリー部門", value=category, inline=False)
        embed.add_field(name="ID", value=member.id, inline=False)
        view = View(timeout=None)
        check_mic = member.get_role(952951691047747655)  # verified
        if check_mic is None and category == "🅱️部門":
            embed.add_field(name="マイク設定確認", value="❌", inline=False)
            button = Button(
                label="verify", style=discord.ButtonStyle.success, emoji="🎙️")

            async def button_callback(interaction):
                admin = interaction.user.get_role(904368977092964352)  # ビト森杯運営
                if bool(admin):
                    await bot_channel.send(f"interaction verify: {interaction.user.display_name}\nID: {interaction.user.id}\nチャンネル：{message.channel.mention}")
                    await member.add_roles(verified)
                    await interaction.response.send_message(f"✅{member.display_name}にverifiedロールを付与しました。")
            button.callback = button_callback
            view.add_item(button)
            for thread_name, URL in zip(thread_names, URLs):
                if member.display_name in thread_name:
                    embed.add_field(name="画像分析提出", value=URL, inline=False)
            await embed_msg.edit(content="", embed=embed, view=view)
            await embed_msg.add_reaction("🗑️")

            def check(reaction, user):
                return user == message.author and reaction.emoji == "🗑️" and reaction.message == embed_msg
            _, _ = await client.wait_for('reaction_add', check=check)
            await embed_msg.delete()
            return
        if bool(check_mic):
            embed.add_field(name="マイク設定確認", value="⭕確認済み", inline=False)
        button_move = Button(
            label="メイン会場へ移動", style=discord.ButtonStyle.primary)

        async def button_move_callback(interaction):
            admin = interaction.user.get_role(904368977092964352)  # ビト森杯運営
            if bool(admin):
                try:
                    await member.move_to(main_ch)
                except discord.errors.HTTPException as e:
                    await interaction.response.send_message(f"Error: {e}")
                else:
                    await interaction.response.send_message(f"{member.display_name}がメイン会場に接続しました。", ephemeral=True)
        button_move.callback = button_move_callback
        view.add_item(button_move)
        for thread_name, URL in zip(thread_names, URLs):
            if member.display_name in thread_name:
                embed.add_field(name="画像分析提出", value=URL, inline=False)
        await embed_msg.edit(content="", embed=embed, view=view)
        await embed_msg.add_reaction("🗑️")

        def check(reaction, user):
            return user == message.author and reaction.emoji == "🗑️" and reaction.message == embed_msg
        _, _ = await client.wait_for('reaction_add', check=check)
        await embed_msg.delete()
        return

    if message.content.startswith("s.poll"):
        names = message.content.replace('s.poll', '').split()
        while len(names) != 2:
            await message.channel.send("Error: 入力方法が間違っています。\n\n`cancelと入力するとキャンセルできます`\nもう一度入力してください：")

            def check(m):
                return m.channel == message.channel and m.author == message.author

            try:
                msg2 = await client.wait_for('message', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await message.channel.send("Error: timeout")
                return
            if msg2.content == "cancel":
                await message.channel.send("キャンセルしました。")
                return
            if msg2.content.startswith("s.poll"):
                return
            names = msg2.content.split()
        embed = Embed(title="投票箱", description=f"1⃣ {names[0]}\n2⃣ {names[1]}")
        poll = await message.channel.send(embed=embed)
        await poll.add_reaction("1⃣")
        await poll.add_reaction("2⃣")
        return

    if message.content.startswith("s.role"):
        await message.delete(delay=1)
        input_id = message.content.split()
        if len(input_id) == 1:
            input_id.append(0)
        if input_id[1] == "A":
            input_id[1] = 1035945116591996979  # A部門 ビト森杯
        elif input_id[1] == "B":
            input_id[1] = 1035945267733737542  # B部門 ビト森杯
        try:
            role = message.guild.get_role(int(input_id[1]))
        except ValueError:
            role = None
        while role is None:
            await message.channel.send("Error: ロールが見つかりませんでした。\n\n`cancelと入力するとキャンセルできます`\n検索したいロールのIDを入力してください：")

            def check(m):
                return m.channel == message.channel and m.author == message.author

            try:
                msg2 = await client.wait_for('message', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await message.channel.send("Error: timeout")
                return
            if msg2.content == "cancel":
                await message.channel.send("キャンセルしました。")
                return
            if msg2.content.startswith("s.role"):
                return
            input_id[1] = msg2.content
            if input_id[1] == "A":
                input_id[1] = 1035945116591996979  # A部門 ビト森杯
            elif input_id[1] == "B":
                input_id[1] = 1035945267733737542  # B部門 ビト森杯
            try:
                role = message.guild.get_role(int(input_id[1]))
            except ValueError:
                role = None
        description = ""
        for member in role.member:
            description += f"{member.display_name}, {member.id}\n"
        embed = Embed(title=f"{role.name}", description=description)
        return

    if message.content == "s.tm":
        await message.channel.send("処理中...")
        names = worksheet.col_values(13)
        names.remove("名前")
        names.remove("名前")
        for j, category in zip([0, 8], ["A", "B"]):
            image = Image.open("tournament.png")
            draw = ImageDraw.Draw(image)
            font = ImageFont.truetype('GenEiLateGo_v2.ttc', 25)
            for i, y in zip(range(8), [45, 92, 160, 207, 276, 323, 391, 439]):
                draw.text((5, y), names[i + j], font=font, fill=(0, 0, 0))
            image.save('/tmp/out.png', 'PNG', quality=100, optimize=True)
            file = discord.File('/tmp/out.png')
            await message.channel.send(f"{category}部門 トーナメント", file=file)
        return

    if message.content == "button":
        await message.delete(delay=1)

        return

client.run("OTUyOTYyOTAyMzI1ODg2OTg2.GaOseR.nhstAXFsu7mIyenljeWbC6liMf3T2OldssKq_E")
