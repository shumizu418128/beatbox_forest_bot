import discord
from discord.ui import InputText, Modal, Button, View
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('makesomenoise-4243a19364b1.json', scope)
gc = gspread.authorize(credentials)
SPREADSHEET_KEY = '1WcwdGVf7NRKerM1pnZu9kIsgA0VYy5TddyGdKHBzAu4'
workbook = gc.open_by_key(SPREADSHEET_KEY)
worksheet = workbook.worksheet('botデータベース（さわらないでね）')
intents = discord.Intents.all()  # デフォルトのIntentsオブジェクトを生成
intents.typing = False  # typingを受け取らないように
client = discord.Bot(intents=intents)
print("ビト森杯bot: 起動完了")

class ModalA(Modal):
    def __init__(self) -> None:
        super().__init__("A部門 読みがな登録")
        self.add_item(
            InputText(label="名前の「読みがな」を、ひらがなで入力", placeholder="例： いんぴーだんす"))

    async def callback(self, interaction):
        channel = client.get_channel(916608669221806100)  # ビト森杯 進行bot
        re_hiragana = re.compile(r'^[あ-んー]+$')
        if re_hiragana.fullmatch(self.children[0].value):
            entry_amount = int(worksheet.acell('J1').value) + 1
            worksheet.update_cell(1, 10, f"{entry_amount}")
            worksheet.update_cell(entry_amount + 1, 1, f"{interaction.user.display_name}")
            worksheet.update_cell(entry_amount + 1, 2, f"{self.children[0].value}")
            worksheet.update_cell(entry_amount + 1, 3, f"{interaction.user.id}")
            embed = discord.Embed(title="🇦部門 受付完了", description="エントリー受付が完了しました。", color=0x00ff00)
            embed.add_field(name=f"`名前：`{interaction.user.display_name}", value=f"`読み：`{self.children[0].value}", inline=False)
            role = interaction.guild.get_role(920320926887862323)  # ビト森杯 A部門
            await interaction.user.add_roles(role)
            await interaction.response.send_message("🇦部門 受付完了", ephemeral=True)  # 全ての作業が終わってから送信する！
            await channel.send(f"{interaction.user.mention}", embed=embed)
        else:
            embed = discord.Embed(title="Error", description=f"🇦部門 登録できませんでした。\n読みがなは、ひらがな・伸ばし棒 `ー` のみで入力してください。\n\n入力内容：{self.children[0].value}", color=0xff0000)
            await channel.send(interaction.user.mention, embed=embed)
            await interaction.response.send_message(interaction.user.mention, embed=embed, ephemeral=True)

class ModalB(Modal):
    def __init__(self) -> None:
        super().__init__("B部門 読みがな登録")
        self.add_item(
            InputText(label="名前の「読みがな」を、ひらがなで入力", placeholder="例： いんぴーだんす"))

    async def callback(self, interaction):
        channel = client.get_channel(916608669221806100)  # ビト森杯 進行bot
        re_hiragana = re.compile(r'^[あ-んー]+$')
        if re_hiragana.fullmatch(self.children[0].value):
            entry_amount = int(worksheet.acell('J2').value) + 1
            worksheet.update_cell(2, 10, f"{entry_amount}")
            worksheet.update_cell(entry_amount + 1, 5, f"{interaction.user.display_name}")
            worksheet.update_cell(entry_amount + 1, 6, f"{self.children[0].value}")
            worksheet.update_cell(entry_amount + 1, 7, f"{interaction.user.id}")
            embed = discord.Embed(title="🅱️部門 受付完了", description="エントリー受付が完了しました。", color=0x00ff00)
            embed.add_field(name=f"`名前：`{interaction.user.display_name}", value=f"`読み：`{self.children[0].value}", inline=False)
            role = interaction.guild.get_role(920321241976541204)  # ビト森杯 B部門
            await interaction.user.add_roles(role)
            await interaction.response.send_message("🅱️部門 受付完了", ephemeral=True)  # 全ての作業が終わってから送信する！
            await channel.send(f"{interaction.user.mention}", embed=embed)
        else:
            embed = discord.Embed(title="Error", description=f"🅱️部門 登録できませんでした。\n読みがなは、ひらがな・伸ばし棒 `ー` のみで入力してください。\n\n入力内容：{self.children[0].value}", color=0xff0000)
            await channel.send(interaction.user.mention, embed=embed)
            await interaction.response.send_message(interaction.user.mention, embed=embed, ephemeral=True)

@client.event
async def on_raw_reaction_add(payload):
    emoji_list = ["⭕", "❌"]
    if payload.emoji.name in emoji_list:
        for role in payload.member.roles:
            if role.id == 904368977092964352:  # ビト森杯運営
                channel = payload.message.guild.get_channel(payload.channel_id)
                message = channel.get_partial_message(payload.message_id)
                contents = [(j) for j in message.content.split()]
                member = message.guild.get_member(int(contents[1]))
                if payload.emoji.name == emoji_list[0]:
                    verified = payload.message.guild.get_role(952951691047747655)  # verified
                    await member.add_roles(verified)
                    embed = discord.Embed(title="確認完了", description="🙇‍♂️ご協力ありがとうございました！🙇‍♂️", color=0x00ff00)
                elif payload.emoji.name == emoji_list[1]:
                    embed = discord.Embed(title="確認結果", description="問題が見つかりました。", color=0xff0000)
                await message.channel.send(embed=embed)

@client.event
async def on_message(message):
    if message.content.startswith("contact:"):
        input_ = [j for j in message.content.split()]
        name = message.guild.get_member(int(input_[1]))
        if name is None:
            await message.channel.send("Error: ID検索結果なし")
            return
        await message.channel.send(f"{name.mention}\nご用件をこのチャンネルにご記入ください。\nplease write your inquiry here.")
        for role in name.roles:
            if role.id == 920320926887862323:  # A部門 ビト森杯
                await message.channel.send("%sさんはビト森杯 🇦部門エントリー済み" % (name.display_name))
                return
            if role.id == 920321241976541204:  # B部門 ビト森杯
                await message.channel.send("%sさんはビト森杯 🅱️部門エントリー済み" % (name.display_name))
                return
        await message.channel.send("%sさんはビト森杯にエントリーしていません" % (name.display_name))
        return

    if message.content.startswith("s.cancel"):
        await message.delete(delay=1)
        for role in message.author.roles:
            if role.id == 904368977092964352:  # ビト森杯運営
                input_ = message.content[9:]  # s.cancel をカット
                try:
                    member = message.guild.get_member(int(input_))
                except ValueError:
                    member = message.guild.get_member_named(input_)
                if member is None:
                    await message.channel.send("Error: 検索結果なし")
                    return
                cell = worksheet.find(f'{member.id}')
                if cell is not None:
                    worksheet.update_cell(cell.row, cell.col, '')
                    worksheet.update_cell(cell.row, cell.col - 1, '')
                    worksheet.update_cell(cell.row, cell.col - 2, '')
                    await message.channel.send(f"DB削除完了 `{cell.row}, {cell.col}`")
                bot_channel = client.get_channel(916608669221806100)  # ビト森杯 進行bot
                for role in member.roles:
                    if role.id == 920320926887862323:  # A部門 ビト森杯
                        roleA = message.guild.get_role(920320926887862323)  # A部門 ビト森杯
                        await member.remove_roles(roleA)
                        await message.channel.send("%sさんのビト森杯 🇦部門エントリーを取り消しました。" % (member.display_name))
                        await bot_channel.send("%sさんのビト森杯 🇦部門エントリーを取り消しました。" % (member.display_name))
                        return
                    if role.id == 920321241976541204:  # B部門 ビト森杯
                        roleB = message.guild.get_role(920321241976541204)  # B部門 ビト森杯
                        await member.remove_roles(roleB)
                        await message.channel.send("%sさんのビト森杯 🅱️部門エントリーを取り消しました。" % (member.display_name))
                        await bot_channel.send("%sさんのビト森杯 🅱️部門エントリーを取り消しました。" % (member.display_name))
                        return
                await message.channel.send("%sさんはビト森杯にエントリーしていません" % (member.display_name))
                return
        await message.channel.send(f"{message.author.mention}\nError: s.cancelはビト森杯運営専用コマンドです\n\n{message.content}")
        return

    if message.content.startswith("s.entry"):  # s.entryA or B と記入する
        await message.delete(delay=1)
        input_ = message.content[9:]  # s.entryA or B をカット
        if message.content.startswith("s.entryA"):
            entry_amount = int(worksheet.acell('J1').value) + 1
            place_key = 0
            category = "🇦"
            worksheet.update_cell(1, 10, f"{entry_amount}")
            role = message.guild.get_role(920320926887862323)  # A部門 ビト森杯
        elif message.content.startswith("s.entryB"):
            entry_amount = int(worksheet.acell('J2').value) + 1
            place_key = 4
            category = "🅱️"
            worksheet.update_cell(2, 10, f"{entry_amount}")
            role = message.guild.get_role(920321241976541204)  # B部門 ビト森杯
        else:
            await message.channel.send("Error: 入力方法が間違っています。")
            return
        try:
            name = message.guild.get_member(int(input_))
        except ValueError:
            name = message.guild.get_member_named(input_)
        if name is None:
            await message.channel.send("Error: 検索結果なし")
            return
        await message.channel.send("名前の読みかたを入力してください：")
        def check(m):
            return m.channel == message.channel and m.author == message.author
        read = await client.wait_for('message', check=check)
        worksheet.update_cell(entry_amount + 1, place_key + 1, f"{name.display_name}")
        worksheet.update_cell(entry_amount + 1, place_key + 2, f"{read.content}")
        worksheet.update_cell(entry_amount + 1, place_key + 3, f"{name.id}")
        await name.add_roles(role)
        embed = discord.Embed(title=f"{category}部門 エントリー完了", description=f"`名前：`{name.display_name}\n`読み：`{read.content}")
        await message.channel.send(embed=embed)
        return

    if message.content.startswith("s.poll"):
        names = [(j) for j in message.content.split()]
        names.remove("s.poll")
        if len(names) != 2:
            await message.channel.send("Error: 入力方法が間違っています。")
            return
        embed = discord.Embed(title="投票箱", description="1⃣ %s\n2⃣ %s" % (names[0], names[1]))
        poll = await message.channel.send(embed=embed)
        await poll.add_reaction("1⃣")
        await poll.add_reaction("2⃣")
        return

    if message.content.startswith("s.check"):
        await message.delete(delay=1)
        input_ = message.content[8:]  # s.check をカット
        try:
            name = message.guild.get_member(int(input_))
        except ValueError:
            name = message.guild.get_member_named(input_)
        if name is None:
            await message.channel.send("Error: 検索結果なし")
            return
        cell = worksheet.find(f'{name.id}')
        if cell is not None:
            await message.channel.send(f"DB登録：`{cell.row}, {cell.col}`")
        for role in name.roles:
            if role.id == 920320926887862323:  # A部門 ビト森杯
                await message.channel.send("%sさんはビト森杯 🇦部門エントリー済み" % (name.display_name))
                return
            if role.id == 920321241976541204:  # B部門 ビト森杯
                await message.channel.send("%sさんはビト森杯 🅱️部門エントリー済み" % (name.display_name))
                return
        await message.channel.send("%sさんはビト森杯にエントリーしていません" % (name.display_name))
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
        DBidA_str = worksheet.col_values(3)
        DBidA_str.remove("id")
        DBidB_str = worksheet.col_values(7)
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
        await message.channel.send("見つかったエラー：")
        for e in error:
            await message.channel.send(e)
        await message.channel.send("---finish---")
        return

    if message.content == "s.nn":
        idA_str = worksheet.col_values(3)
        idA_str.remove("id")
        idB_str = worksheet.col_values(7)
        idB_str.remove("id")
        idA = [int(id) for id in idA_str]
        idB = [int(id) for id in idB_str]
        nameA = worksheet.col_values(1)
        nameA.remove("A部門 参加者名 (display_name)")
        nameB = worksheet.col_values(5)
        nameB.remove("B部門 参加者名 (display_name)")
        if len(idA) != len(nameA) or len(idB) != len(nameB):
            if len(idA) != len(nameA):
                await message.channel.send("Error: 🇦部門DBデータ破損")
            if len(idB) != len(nameB):
                await message.channel.send("Error: 🅱️部門DBデータ破損")
            return
        for i in range(len(idA)):
            member = message.guild.get_member(idA[i])
            if member.display_name != nameA[i]:
                await message.channel.send(f"登録名: {nameA[i]}\n現在の名前: {member.display_name}")
                await member.edit(nick=nameA[i])
        for i in range(len(idB)):
            member = message.guild.get_member(idB[i])
            if member.display_name != nameB[i]:
                await message.channel.send(f"登録名: {nameB[i]}\n現在の名前: {member.display_name}")
                await member.edit(nick=nameB[i])
        await message.channel.send("---処理終了---")
        return

    if message.content.startswith("s.read"):
        input_ = message.content[7:]  # s.read をカット
        try:
            member = message.guild.get_member(int(input_))
        except ValueError:
            member = message.guild.get_member_named(input_)
        if member is None:
            await message.channel.send("Error: 検索結果なし")
            return
        cell = worksheet.find(f'{member.id}')
        if cell is None:
            await message.channel.send("Error: DB検索結果なし")
            return
        read = worksheet.cell(cell.row - 1, cell.col).value
        await message.channel.send(f"名前：{member.display_name}\n読み：{read}")
        return

    if len(message.attachments) != 2 and message.channel.id == 952946795573571654:  # 画像提出
        await message.delete(delay=1)
        await message.channel.send(f"{message.author.mention}\nError: 画像を2枚同時に投稿してください。")
        if len(message.attachments) == 1:
            await message.channel.send("画像1枚では、すべての設定項目が画像内に収まりません。")
        return

    if message.content == "button":
        await message.delete()
        buttonA = Button(label="Entry", style=discord.ButtonStyle.primary, emoji="🇦")
        buttonB = Button(label="Entry", style=discord.ButtonStyle.red, emoji="🅱️")
        async def buttonA_callback(interaction):
            await interaction.response.send_modal(ModalA())
        async def buttonB_callback(interaction):
            await interaction.response.send_modal(ModalB())
        buttonA.callback = buttonA_callback
        buttonB.callback = buttonB_callback
        view = View()
        view.add_item(buttonA)
        view.add_item(buttonB)
        await message.channel.send(view=view, timeout=None)
        return

client.run("OTUyOTYyOTAyMzI1ODg2OTg2.Yi9p3Q.bisIxDqKOMlESDLe1GBnvNseOBQ")
