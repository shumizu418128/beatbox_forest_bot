import asyncio
import re
from difflib import get_close_matches

import discord
import gspread
from discord import Embed
from discord.ui import Button, InputText, Modal, View
from neologdn import normalize
from oauth2client.service_account import ServiceAccountCredentials

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
re_hiragana = re.compile(r'^[あ-んー　 ]+$')
print('ビト森杯bot: 起動完了')


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
                worksheet.update_cell(
                    entry_amount + 1, 1, f"{interaction.user.display_name}")
                worksheet.update_cell(
                    entry_amount + 1, 2, f"{self.children[0].value}")
                worksheet.update_cell(
                    entry_amount + 1, 3, f"{interaction.user.id}")
            except gspread.exceptions.APIError:
                embed = Embed(
                    title="Error", description="🇦部門 登録できませんでした。\n\nアクセス過多によるエラーです。\nお手数ですが、しばらく時間をおいてからもう一度お試しください。", color=0xff0000)
                await channel.send(interaction.user.mention, embed=embed)
                embed.set_footer(text="made by tari3210#9924")
                await interaction.response.send_message(interaction.user.mention, embed=embed, ephemeral=True)
                return
            role = interaction.guild.get_role(920320926887862323)  # A部門 ビト森杯
            await interaction.user.add_roles(role)
            embed = Embed(title="🇦部門 受付完了",
                          description="エントリー受付が完了しました。", color=0x00ff00)
            embed.add_field(name=f"`名前：`{interaction.user.display_name}",
                            value=f"`読み：`{self.children[0].value}", inline=False)
            await channel.send(f"{interaction.user.mention}", embed=embed)
            embed.set_footer(text="made by tari3210#9924")
            # 全ての作業が終わってから送信する！
            await interaction.response.send_message("🇦部門 受付完了", ephemeral=True)
        else:
            embed = Embed(
                title="Error", description=f"🇦部門 登録できませんでした。\n読みがなは、ひらがな・伸ばし棒 `ー` のみで入力してください。\n\n入力内容：{self.children[0].value}", color=0xff0000)
            await channel.send(interaction.user.mention, embed=embed)
            embed.set_footer(text="made by tari3210#9924")
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
                worksheet.update_cell(
                    entry_amount + 1, 5, f"{interaction.user.display_name}")
                worksheet.update_cell(
                    entry_amount + 1, 6, f"{self.children[0].value}")
                worksheet.update_cell(
                    entry_amount + 1, 7, f"{interaction.user.id}")
            except gspread.exceptions.APIError:
                embed = Embed(
                    title="Error", description="🅱️部門 登録できませんでした。\n\nアクセス過多によるエラーです。\nお手数ですが、しばらく時間をおいてからもう一度お試しください。", color=0xff0000)
                await channel.send(interaction.user.mention, embed=embed)
                embed.set_footer(text="made by tari3210#9924")
                await interaction.response.send_message(interaction.user.mention, embed=embed, ephemeral=True)
                return
            role = interaction.guild.get_role(920321241976541204)  # B部門 ビト森杯
            await interaction.user.add_roles(role)
            embed = Embed(title="🅱️部門 受付完了",
                          description="エントリー受付が完了しました。", color=0x00ff00)
            embed.add_field(name=f"`名前：`{interaction.user.display_name}",
                            value=f"`読み：`{self.children[0].value}", inline=False)
            await channel.send(f"{interaction.user.mention}", embed=embed)
            embed.set_footer(text="made by tari3210#9924")
            # 全ての作業が終わってから送信する！
            await interaction.response.send_message("🅱️部門 受付完了", ephemeral=True)
        else:
            embed = Embed(
                title="Error", description=f"🅱️部門 登録できませんでした。\n読みがなは、ひらがな・伸ばし棒 `ー` のみで入力してください。\n\n入力内容：{self.children[0].value}", color=0xff0000)
            await channel.send(interaction.user.mention, embed=embed)
            embed.set_footer(text="made by tari3210#9924")
            await interaction.response.send_message(interaction.user.mention, embed=embed, ephemeral=True)


@client.event
async def on_member_update(before, after):
    if before.display_name != after.display_name:
        roleA = after.get_role(920320926887862323)  # A部門 ビト森杯
        roleB = after.get_role(920321241976541204)  # B部門 ビト森杯
        admin = after.guild.get_role(904368977092964352)  # ビト森杯運営
        channel = client.get_channel(916608669221806100)  # ビト森杯 進行bot
        bot_channel = client.get_channel(897784178958008322)  # bot用チャット
        if roleA is None and roleB is None:
            return
        if bool(roleA) and bool(roleB):
            await channel.send(f"{admin.mention}\nError: AB重複エントリー検知\n\n{after.display_name} {after.id}")
            await bot_channel.send(f"Error: AB重複エントリー検知\n\n{after.display_name} {after.id}")
            category = "重複エントリー"
        elif bool(roleA):
            category = "🇦部門"
        elif bool(roleB):
            category = "🅱️部門"
        try:
            cell = worksheet.find(f'{after.id}')
        except gspread.exceptions.APIError as e:
            await channel.send(f"{admin.mention}\nError: {e}\nニックネーム変更検知\n\nbefore: {before.display_name}\nafter: {after.display_name}\nid: {after.id}\n{category}")
            await bot_channel.send(f"Error: {e}\nニックネーム変更検知\n\nbefore: {before.display_name}\nafter: {after.display_name}\nid: {after.id}\n{category}")
            return
        if cell is None:
            await channel.send(f"{admin.mention}\nError: ニックネーム変更・データベース破損検知\n\nbefore: {before.display_name}\nafter: {after.display_name}\nid: {after.id}\n{category}")
            await bot_channel.send(f"Error: ニックネーム変更・データベース破損検知\n\nbefore: {before.display_name}\nafter: {after.display_name}\nid: {after.id}\n{category}")
            return
        try:
            right_name = worksheet.cell(cell.row, cell.col - 2).value
        except gspread.exceptions.APIError as e:
            await channel.send(f"{admin.mention}\nError: {e}\nニックネーム変更検知\n\nbefore: {before.display_name}\nafter: {after.display_name}\nid: {after.id}\n{category}")
            await bot_channel.send(f"Error: {e}\nニックネーム変更検知\n\nbefore: {before.display_name}\nafter: {after.display_name}\nid: {after.id}\n{category}")
            return
        if after.display_name != right_name:
            await after.edit(nick=right_name)
            await channel.send(f"{after.mention}\nエントリー後のニックネーム変更は禁止されています\nchanging nickname after entry is prohibited")
        await bot_channel.send(f"ニックネーム変更検知\n\nbefore: {before.display_name}\nafter: {after.display_name}\nid: {after.id}\n{category}")
        return


@client.event
async def on_message(message):
    if message.author.id == 952962902325886986:  # ビト森杯bot
        return

    if message.content == "s.test":
        await message.channel.send(f"ビト森杯: {client.latency}")
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
            embed = Embed(description=f"{member.mention}\nビト森杯にエントリーしていません")
            embed.set_author(name=f"{member.name}#{member.discriminator}",
                             icon_url=member.display_avatar.url)
            embed.add_field(name="ID", value=f"{member.id}", inline=False)
            await message.channel.send(embed=embed)
        elif bool(roleA) and bool(roleB):
            embed = Embed(title="Error: 重複エントリーを検知",
                          description=member.mention, color=0xff0000)
            embed.set_author(name=f"{member.name}#{member.discriminator}",
                             icon_url=member.display_avatar.url)
            embed.add_field(name="ID", value=f"{member.id}", inline=False)
            await message.channel.send(f"{admin.mention}", embed=embed)
        else:
            if bool(roleA):
                category = "🇦 ※マイク設定確認不要"
            elif bool(roleB):
                category = "🅱️部門"
            try:
                cell = worksheet.find(f'{member.id}')
            except gspread.exceptions.APIError as e:
                await message.channel.send(f"Error: {e}")
                return
            if cell is None:
                embed = Embed(title="Error: DB検索結果なし",
                              description=member.mention, color=0xff0000)
                embed.set_author(
                    name=f"{member.name}#{member.discriminator}", icon_url=member.display_avatar.url)
                embed.add_field(name="エントリー部門", value=category, inline=False)
                embed.add_field(name="ID", value=f"{member.id}", inline=False)
                check_mic = member.get_role(952951691047747655)  # verified
                if check_mic is None and category == "🅱️部門":
                    embed.add_field(name="マイク設定確認", value="❌", inline=False)
                elif bool(check_mic) and category == "🅱️部門":
                    embed.add_field(
                        name="マイク設定確認", value="⭕確認済み", inline=False)
                await message.channel.send(f"{admin.mention}", embed=embed)
            else:
                try:
                    read = worksheet.cell(cell.row, cell.col - 1).value
                except gspread.exceptions.APIError as e:
                    read = f"Error: {e}"
                if read is None:
                    read = "Error: DB検索結果なし"
                check_mic = member.get_role(952951691047747655)  # verified
                embed = Embed(description=member.mention)
                embed.set_author(
                    name=f"{member.name}#{member.discriminator}", icon_url=member.display_avatar.url)
                embed.add_field(name="読みがな", value=read, inline=False)
                embed.add_field(name="エントリー部門", value=category, inline=False)
                embed.add_field(name="ID", value=f"{member.id}", inline=False)
                if check_mic is None and category == "🅱️部門":
                    embed.add_field(name="マイク設定確認", value="❌", inline=False)
                elif bool(check_mic):
                    embed.add_field(
                        name="マイク設定確認", value="⭕確認済み", inline=False)
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
            await message.channel.send(f"{member.display_name}はビト森杯にエントリーしていません")
            return
        notice = await message.channel.send(f"{member.display_name}のビト森杯エントリーを取り消します。\n\n⭕ `OK`\n❌ 中止")
        await notice.add_reaction("⭕")
        await notice.add_reaction("❌")

        def check(reaction, user):
            return user == message.author and reaction.emoji in emoji_list and reaction.message == notice

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
        channel = client.get_channel(916608669221806100)  # ビト森杯 進行bot
        if bool(roleA):
            await member.remove_roles(roleA)
            await message.channel.send(f"{member.display_name}のビト森杯 🇦部門エントリーを取り消しました。")
            await channel.send(f"{member.display_name}のビト森杯 🇦部門エントリーを取り消しました。")
        elif bool(roleB):
            await member.remove_roles(roleB)
            await message.channel.send(f"{member.display_name}のビト森杯 🅱️部門エントリーを取り消しました。")
            await channel.send(f"{member.display_name}のビト森杯 🅱️部門エントリーを取り消しました。")
        return

    if message.content.startswith("s.s") and not message.content.startswith("s.start") and not message.content.startswith("s.stage"):
        await message.delete(delay=1)
        admin = message.guild.get_role(904368977092964352)  # ビト森杯運営
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
                if not mem.bot and mem.id not in [332886651107934219, 826371622084542474]:
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
        roleA = member.get_role(920320926887862323)  # A部門 ビト森杯
        roleB = member.get_role(920321241976541204)  # B部門 ビト森杯
        if bool(roleA) and bool(roleB):  # 重複エントリー警告
            embed = Embed(title="Error: 重複エントリーを検知",
                          description=member.mention, color=0xff0000)
            embed.set_author(name=f"{member.name}#{member.discriminator}",
                             icon_url=member.display_avatar.url)
            embed.add_field(name="ID", value=f"{member.id}", inline=False)
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
                    description="登録できませんでした。\n読みがなは、ひらがな・伸ばし棒 `ー` のみで入力してください。", color=0xff0000)
                await message.channel.send(embed=embed, delete_after=5)
            await message.channel.send("処理中...", delete_after=5)
            try:
                if category == "🇦":
                    entry_amount = int(worksheet.acell('J1').value) + 1
                    place_key = 0
                    worksheet.update_cell(1, 10, entry_amount)
                    role = message.guild.get_role(
                        920320926887862323)  # A部門 ビト森杯
                elif category == "🅱️":
                    entry_amount = int(worksheet.acell('J2').value) + 1
                    place_key = 4
                    worksheet.update_cell(2, 10, entry_amount)
                    role = message.guild.get_role(
                        920321241976541204)  # B部門 ビト森杯
                worksheet.update_cell(
                    entry_amount + 1, place_key + 1, member.display_name)
                worksheet.update_cell(
                    entry_amount + 1, place_key + 2, read.content)
                worksheet.update_cell(
                    entry_amount + 1, place_key + 3, f"{member.id}")
            except gspread.exceptions.APIError as e:
                await message.channel.send(f"Error: {e}")
                return
            await member.add_roles(role)
            embed = Embed(title=f"{category}部門 受付完了",
                          description=f"{member.mention}\nエントリー受付が完了しました。", color=0x00ff00)
            embed.set_author(name=f"{member.name}#{member.discriminator}",
                             icon_url=member.display_avatar.url)
            embed.add_field(name="名前", value=member.display_name, inline=False)
            embed.add_field(name="読みがな", value=read.content, inline=False)
            await message.channel.send(embed=embed)
            channel = client.get_channel(916608669221806100)  # ビト森杯 進行bot
            await channel.send(embed=embed)
            embed_msg = await message.channel.send("処理中...")
            roleA = member.get_role(920320926887862323)  # A部門 ビト森杯
            roleB = member.get_role(920321241976541204)  # B部門 ビト森杯
        if bool(roleA):
            category = "🇦 ※マイク設定確認不要"
        elif bool(roleB):
            category = "🅱️部門"
        try:
            cell = worksheet.find(f'{member.id}')
        except gspread.exceptions.APIError as e:
            read = f"Error: {e}"
        else:
            if cell is None:
                embed = Embed(title="Error: DB検索結果なし",
                              description=member.mention, color=0xff0000)
                embed.set_author(name=f"{member.name}#{member.discriminator}",
                                 icon_url=member.display_avatar.url)
                embed.add_field(name="エントリー部門", value=category, inline=False)
                embed.add_field(name="ID", value=f"{member.id}", inline=False)
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
        check_mic = member.get_role(952951691047747655)  # verified
        embed = Embed(description=member.mention)
        embed.set_author(name=f"{member.name}#{member.discriminator}",
                         icon_url=member.display_avatar.url)
        embed.add_field(name="読みがな", value=read, inline=False)
        embed.add_field(name="エントリー部門", value=category, inline=False)
        embed.add_field(name="ID", value=member.id, inline=False)
        view = View(timeout=None)
        if check_mic is None and category == "🅱️部門":
            embed.add_field(name="マイク設定確認", value="❌", inline=False)
            button = Button(
                label="verify", style=discord.ButtonStyle.success, emoji="🎙️")

            async def button_callback(interaction):
                admin = interaction.user.get_role(904368977092964352)  # ビト森杯運営
                if bool(admin):
                    bot_channel = client.get_channel(
                        897784178958008322)  # bot用チャット
                    await bot_channel.send(f"interaction verify: {interaction.user.display_name}\nID: {interaction.user.id}\nチャンネル：{message.channel.mention}")
                    verified = message.guild.get_role(
                        952951691047747655)  # verified
                    await member.add_roles(verified)
                    await interaction.response.send_message(f"✅{member.display_name}にverifiedロールを付与しました。")
            button.callback = button_callback
            view.add_item(button)
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
                main_ch = client.get_channel(910861846888722432)  # メイン会場
                try:
                    await member.move_to(main_ch)
                except discord.errors.HTTPException as e:
                    await interaction.response.send_message(f"Error: {e}")
                else:
                    await interaction.response.send_message(f"{member.display_name}がメイン会場に接続しました。", ephemeral=True)
        button_move.callback = button_move_callback
        view.add_item(button_move)
        await embed_msg.edit(content="", embed=embed, view=view)
        await embed_msg.add_reaction("🗑️")

        def check(reaction, user):
            return user == message.author and reaction.emoji == "🗑️" and reaction.message == embed_msg
        _, _ = await client.wait_for('reaction_add', check=check)
        await embed_msg.delete()
        return

    if message.content.startswith("s.poll"):
        names = [(j) for j in message.content.replace('s.poll', '').split()]
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
            names = [(j) for j in msg2.content.split()]
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
            input_id[1] = 920320926887862323  # A部門 ビト森杯
        elif input_id[1] == "B":
            input_id[1] = 920321241976541204  # B部門 ビト森杯
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
                input_id[1] = 920320926887862323  # A部門 ビト森杯
            elif input_id[1] == "B":
                input_id[1] = 920321241976541204  # B部門 ビト森杯
            try:
                role = message.guild.get_role(int(input_id[1]))
            except ValueError:
                role = None
        role_member = role.members
        for member in role_member:
            await message.channel.send(f"{member.display_name}, {member.id}")
        await message.channel.send("---finish---")
        return

    if message.content == "button":
        if message.channel.id != 904367725416153118:  # ビト森杯 参加
            return
        await message.delete()
        buttonA = Button(
            label="Entry", style=discord.ButtonStyle.primary, emoji="🇦")
        buttonB = Button(
            label="Entry", style=discord.ButtonStyle.red, emoji="🅱️")
        bot_channel = client.get_channel(897784178958008322)  # bot用チャット

        async def buttonA_callback(interaction):
            roleA = interaction.user.get_role(920320926887862323)  # A部門 ビト森杯
            await bot_channel.send(f"interaction🇦: {interaction.user.display_name}\nID: {interaction.user.id}")
            if bool(roleA):
                await interaction.response.send_message("Error: すでに🇦部門にエントリーしています。", ephemeral=True)
                return
            await interaction.response.send_modal(ModalA(interaction.user.display_name))

        async def buttonB_callback(interaction):
            roleB = interaction.user.get_role(920321241976541204)  # B部門 ビト森杯
            await bot_channel.send(f"interaction🅱️: {interaction.user.display_name}\nID: {interaction.user.id}")
            if bool(roleB):
                await interaction.response.send_message("Error: すでに🅱️部門にエントリーしています。", ephemeral=True)
                return
            await interaction.response.send_modal(ModalB(interaction.user.display_name))
        buttonA.callback = buttonA_callback
        buttonB.callback = buttonB_callback
        view = View(timeout=None)
        view.add_item(buttonA)
        view.add_item(buttonB)
        await message.channel.send(view=view)
        return

client.run("OTUyOTYyOTAyMzI1ODg2OTg2.GaOseR.nhstAXFsu7mIyenljeWbC6liMf3T2OldssKq_E")
