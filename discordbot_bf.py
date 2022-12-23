# -*- coding: utf-8 -*-
import asyncio
import re
from difflib import get_close_matches

import discord
import gspread_asyncio
from discord import Embed, SelectOption
from discord.ui import Button, InputText, Modal, View, Select
from neologdn import normalize
from oauth2client.service_account import ServiceAccountCredentials
from PIL import Image, ImageDraw, ImageFont

intents = discord.Intents.all()  # デフォルトのIntentsオブジェクトを生成
intents.typing = False  # typingを受け取らないように
client = discord.Bot(intents=intents)
re_hiragana = re.compile(r'^[ぁ-ゞ　 ー]+$')
print("ビト森杯bot (Local): 起動完了")
green = 0x00ff00
yellow = 0xffff00
red = 0xff0000
blue = 0x00bfff


def get_credits():
    return ServiceAccountCredentials.from_json_keyfile_name(
        "makesomenoise-4243a19364b1.json",
        ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive',
         'https://www.googleapis.com/auth/spreadsheets'])


class entry_modal(Modal):
    def __init__(self, name: str, category: str) -> None:
        super().__init__(title=f"{category}部門 読みがな登録", custom_id=category)
        self.add_item(
            InputText(label=f"あなたの名前（{name}）の「読みがな」を、ひらがなで入力", placeholder="ひらがなで入力"))

    # self → children[0].value(ユーザー入力内容), custom_id, title
    async def callback(self, interaction):
        await interaction.response.defer(ephemeral=True, invisible=False)
        bot_channel = client.get_channel(1035946838487994449)  # ビト森杯 進行bot
        roleA = bot_channel.guild.get_role(1035945116591996979)  # A部門 ビト森杯
        roleB = bot_channel.guild.get_role(1035945267733737542)  # B部門 ビト森杯
        roleLOOP = bot_channel.guild.get_role(
            1036149651847524393)  # LOOP部門 ビト森杯
        # ひらがな判定・応答
        if not re_hiragana.fullmatch(self.children[0].value):
            embed = Embed(
                title="Error", description=f"{self.custom_id}部門 登録できませんでした。\n読みがなは、ひらがな・伸ばし棒 `ー` のみで入力してください。\n\n入力内容：{self.children[0].value}", color=red)
            await bot_channel.send(interaction.user.mention, embed=embed)
            embed.set_footer(text="bot制作: tari3210#9924")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        embed = Embed(title=f"{self.custom_id}部門 受付完了",
                      description="ご参加ありがとうごさいます！", color=green)
        embed.add_field(name=f"`名前：`{interaction.user.display_name}",
                        value=f"`読み：`{self.children[0].value}", inline=False)
        await bot_channel.send(interaction.user.mention, embed=embed)
        embed.set_footer(text="bot制作: tari3210#9924")
        await interaction.followup.send(embed=embed, ephemeral=True)
        # DBアクセス準備
        gc = gspread_asyncio.AsyncioGspreadClientManager(get_credits)
        agc = await gc.authorize()
        workbook = await agc.open_by_key('1WcwdGVf7NRKerM1pnZu9kIsgA0VYy5TddyGdKHBzAu4')
        worksheet = await workbook.worksheet('botデータベース（さわらないでね）')
        materials = {"A": {"role": roleA, "number": 0},
                     "B": {"role": roleB, "number": 1},
                     "LOOP": {"role": roleLOOP, "number": 2}}
        material = materials[self.custom_id]
        # DB更新
        await interaction.user.add_roles(material["role"])
        entry_amount = await worksheet.acell(
            f'N{material["number"] + 1}')
        entry_amount = int(entry_amount.value) + 1
        await worksheet.update_cell(
            material["number"] + 1, 14, f"{entry_amount}")
        await worksheet.update_cell(
            entry_amount + 1, material["number"] * 4 + 1, interaction.user.display_name)
        await worksheet.update_cell(
            entry_amount + 1, material["number"] * 4 + 2, self.children[0].value)
        await worksheet.update_cell(
            entry_amount + 1, material["number"] * 4 + 3, f"{interaction.user.id}")


async def find_contact(member_id: int, create: bool):  # 問い合わせthreadを作り、threadオブジェクトを返す
    contact = client.get_channel(1035964918198960128)  # 問い合わせ
    for thread in contact.threads:
        if str(member_id) == thread.name:
            return thread
    if create is True:
        thread = await contact.create_thread(name=f"{member_id}")
    return thread
    return None


async def get_view(*, change_contact=False, call_admin=False):
    button_call_admin = Button(
        label="運営メンバーに問い合わせる", style=discord.ButtonStyle.green)
    button_change_contact = Button(
        label="別の問い合わせをする", style=discord.ButtonStyle.primary)

    async def button_call_admin_callback(interaction):
        admin = interaction.user.get_role(904368977092964352)  # ビト森杯運営
        embed = Embed(title="運営メンバーが対応します", description="ご用件をこのチャンネルにご記入ください")
        await interaction.response.send_message(f"{admin.mention} {interaction.user.mention}", embed=embed)
        return

    async def button_change_contact_callback(interaction):
        await interaction.response.send_message("処理中...", ephemeral=True)
        await new_contact(interaction.user.id)
        return

    button_change_contact.callback = button_change_contact_callback
    button_call_admin.callback = button_call_admin_callback
    view = View(timeout=None)
    if change_contact:
        view.add_item(button_change_contact)
    if call_admin:
        view.add_item(button_call_admin)
    return view


async def new_contact(member_id: int):  # 新規問い合わせを作成
    thread = await find_contact(member_id, create=True)
    admin = thread.guild.get_role(904368977092964352)  # ビト森杯運営
    member = thread.guild.get_member(member_id)
    emoji_list = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣"]
    embed = Embed(title="お問い合わせ",
                  description="質問内容に近いものを、以下からお選びください\n", color=blue)
    embed.set_author(name=member.display_name,
                     icon_url=member.display_avatar.url)
    embed.description += "\n1️⃣ ビト森杯 詳細情報・ルール"
    embed.description += "\n2️⃣ エントリー・キャンセルについて"
    embed.description += "\n3️⃣ 当日について、運営に連絡したい"
    embed.description += "\n4️⃣ スポンサー協力・賞金・賞品"
    embed.description += "\n5️⃣ 事前マイクチェック (開催日前日に公開)"
    embed.description += "\n6️⃣ その他・ここに無い内容について知りたい"
    panel = await thread.send(member.mention, embed=embed)
    for i in range(6):
        await panel.add_reaction(emoji_list[i])

    def check(reaction, user):
        return user == member and reaction.emoji in emoji_list and reaction.message == panel

    reaction, _ = await client.wait_for('reaction_add', check=check)
    await panel.clear_reactions()

    topics = {"1️⃣": "ビト森杯 詳細情報・ルール",
              "2️⃣": "エントリー・キャンセルについて",
              "3️⃣": "当日について、運営に連絡したい",
              "4️⃣": "スポンサー協力・賞金・賞品",
              "5️⃣": "事前マイクチェック (開催日前日に公開)",
              "6️⃣": "その他"}
    # stamp_number = {"4️⃣": 4, "5️⃣": 3}
    questions_list = {"1️⃣": "1️⃣ A, B部門 elimination, battleのルール\n2️⃣ LOOP部門 showcaseのルール\n3️⃣ 開催日、開催時間、スケジュール\n4️⃣ 賞金・賞品\n5️⃣ 開催場所、中継配信\n6️⃣ マイクの使用・顔出し\n7️⃣ A, B部門の違い",
                      "2️⃣": "1️⃣ エントリー方法・締切\n2️⃣ 複数部門エントリー\n3️⃣ A, B部門の違い\n4️⃣ エントリー状況確認・変更・キャンセル\n5️⃣ 海外からのエントリー",
                      "3️⃣": "1️⃣ elimination, showcase 順番の希望\n2️⃣ 当日の集合時間に遅れる可能性がある",
                      "4️⃣": "1️⃣ スポンサー協力したい(賞金)\n2️⃣ スポンサー協力したい(賞品)\n3️⃣ 資金管理について\n4️⃣ 賞品について",
                      "5️⃣": "1️⃣ 事前マイクチェックとは\n2️⃣ 事前マイクチェックのやり方\n3️⃣ 分析結果に誤りがある・botが動かない"}

    if reaction.emoji == "6️⃣":
        embed = Embed(title="運営メンバーが対応します", description="ご用件をこのチャンネルにご記入ください")
        view = await get_view(change_contact=True)
        await thread.send(f"{admin.mention} {member.mention}", embed=embed, view=view)
        return
    embed = Embed(title=topics[reaction.emoji],
                  description=questions_list[reaction.emoji])
    await panel.edit(embed=embed)

    if reaction.emoji == "1️⃣":
        options1 = [SelectOption(label="A, B部門 elimination, battleのルール", emoji="1️⃣"),
                    SelectOption(label="LOOP部門 showcaseのルール", emoji="2️⃣"),
                    SelectOption(label="開催日、開催時間、スケジュール", emoji="3️⃣"),
                    SelectOption(label="賞金・賞品", emoji="4️⃣"),
                    SelectOption(label="開催場所、中継配信", emoji="5️⃣"),
                    SelectOption(label="マイクの使用・顔出し", emoji="6️⃣"),
                    SelectOption(label="A, B部門の違い", emoji="7️⃣")]
        option1_answers = {"A, B部門 elimination, battleのルール": "eliminationは、1人1分です。\n下記の基準で得点化し、順位を決定、上位8人が決勝トーナメントへ進出します。\n```・正確さ 5点\n・オリジナリティ 5点\n・構成 5点\nボーナスポイント 5点\n計20点```battleは、1分2ラウンド x 2名で、延長は無し。\nオーディエンス票(1票)と審査員2名(2票) 計3票で勝敗を決定します。",
                           "LOOP部門 showcaseのルール": "未定",
                           "開催日、開催時間、スケジュール": "以下のURLからご確認ください。\n※時間は前後する可能性があります。",
                           "賞金・賞品": "以下のURLからご確認ください。",
                           "開催場所、中継配信": "Discordサーバー「あつまれ！ビートボックスの森」で開催します。\n配信はこちらのチャンネルにて行います。\nhttps://www.youtube.com/channel/UCrBlxDIuyUKXlUWiYF9GKyQ",
                           "マイクの使用・顔出し": "マイクに関してルールはありません。ただし、必ずDiscordのノイズキャンセリング機能をOFFにしてください。\n顔出しは不要です。Discordのカメラ機能を使用しても、当日配信には映りません。",
                           "A, B部門の違い": "A部門: 大会出場経験あり\nB部門: 大会出場経験なし\n```大会出場経験とは、オフラインもしくはオンラインで開催されたもののうち、「審査員による審査を勝ち上がった経験」を指します。\n※大会の規模は考慮しません。\n\n大会出場経験の例\n・狼煙の予選通過\n・小規模オンライン大会予選通過\n\n大会出場経験と見なされない例\n・ビト森で毎週土曜開催「battle stadium」(審査が無いイベント)\n・BoiceLess Festival初戦敗退 (審査を勝ち上がっていない)```"}
        select1 = Select(placeholder="ここをクリック", options=options1)

        async def select1_callback(interaction):
            embed = Embed(
                title=select1.values[0], description=option1_answers[select1.values[0]])
            await interaction.response.send_message(embed=embed, ephemeral=True)
        select1.callback = select1_callback
        view = await get_view(change_contact=True, call_admin=True)
        view.add_item(select1)
        await panel.edit(view=view)
        return
    if reaction.emoji == "2️⃣":
        gc = gspread_asyncio.AsyncioGspreadClientManager(get_credits)
        agc = await gc.authorize()
        workbook = await agc.open_by_key('1WcwdGVf7NRKerM1pnZu9kIsgA0VYy5TddyGdKHBzAu4')
        worksheet = await workbook.worksheet('botデータベース（さわらないでね）')
        options2 = [SelectOption(label="エントリー方法・締切", emoji="1️⃣"),
                    SelectOption(label="複数部門エントリー", emoji="2️⃣"),
                    SelectOption(label="A, B部門の違い", emoji="3️⃣"),
                    SelectOption(label="エントリー状況確認・変更・キャンセル", emoji="4️⃣"),
                    SelectOption(label="海外からのエントリー", emoji="5️⃣")]
        option2_answers = {"エントリー方法・締切": "以下のURLからご確認ください。",
                           "複数部門エントリー": "以下の組み合わせのみ可能です。```・A部門, LOOP部門 重複エントリー\n・B部門, LOOP部門 重複エントリー```これ以外の組み合わせはできません。",
                           "A, B部門の違い": "A部門: 大会出場経験あり\nB部門: 大会出場経験なし\n```大会出場経験とは、オフラインもしくはオンラインで開催されたもののうち、「審査員による審査を勝ち上がった経験」を指します。\n※大会の規模は考慮しません。\n\n大会出場経験の例\n・狼煙の予選通過\n・小規模オンライン大会予選通過\n\n大会出場経験と見なされない例\n・ビト森で毎週土曜開催「battle stadium」(審査が無いイベント)\n・BoiceLess Festival初戦敗退 (審査を勝ち上がっていない)```",
                           "海外からのエントリー": "エントリー前にお伝えすることがありますので、エントリーボタンを押すと自動で問い合わせシステムに接続されます。"}
        select2 = Select(placeholder="ここをクリック", options=options2)
        async def select2_callback(interaction):
            if select2.values[0] != "エントリー状況確認・変更・キャンセル":
                embed = Embed(
                    title=select2.values[0], description=option2_answers[select2.values[0]])
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True, invisible=False)
            embed = Embed(description=f"{interaction.user.mention}")
            embed.set_author(name=f"{interaction.user.name}#{interaction.user.discriminator}",
                             icon_url=interaction.user.display_avatar.url)
            roleA = interaction.user.get_role(1035945116591996979)  # A部門 ビト森杯
            roleB = interaction.user.get_role(1035945267733737542)  # B部門 ビト森杯
            roleLOOP = interaction.user.get_role(1036149651847524393)  # LOOP部門 ビト森杯
            check_entry = [bool(roleA), bool(roleB), bool(roleLOOP)]
            if any(check_entry):
                category = ""
                for role, name in zip(check_entry, ["A", "B", "LOOP"]):
                    if role:
                        category += f"{name} "
                embed.add_field(name="エントリー部門", value=category, inline=False)
                cell = await worksheet.find(f'{interaction.user.id}')
                read = await worksheet.cell(cell.row, cell.col - 1).value
                embed.add_field(name="読みがな", value=read, inline=False)
            else:
                embed.description += "\nビト森杯にエントリーしていません"
            embed.add_field(name="ID", value=interaction.user.id, inline=False)
            await interaction.followup.send_message(embed=embed)
        select2.callback = select2_callback
        view = await get_view(change_contact=True, call_admin=True)
        view.add_item(select2)
        await panel.edit(view=view)
        return


@client.event
async def on_member_update(before, after):
    gc = gspread_asyncio.AsyncioGspreadClientManager(get_credits)
    agc = await gc.authorize()
    workbook = await agc.open_by_key('1WcwdGVf7NRKerM1pnZu9kIsgA0VYy5TddyGdKHBzAu4')
    worksheet = await workbook.worksheet('botデータベース（さわらないでね）')
    roleA = after.get_role(1035945116591996979)  # A部門 ビト森杯
    roleB = after.get_role(1035945267733737542)  # B部門 ビト森杯
    roleLOOP = after.get_role(1036149651847524393)  # LOOP部門 ビト森杯
    admin = after.guild.get_role(904368977092964352)  # ビト森杯運営
    bot_channel = client.get_channel(1035946838487994449)  # ビト森杯 進行bot
    bot_test_channel = client.get_channel(897784178958008322)  # bot用チャット
    if before.display_name != after.display_name:
        if all([roleA is None, roleB is None, roleLOOP is None]):
            return
        if bool(roleA) and bool(roleB):
            embed = Embed(
                title="AB重複エントリー検知", description=f"{after.display_name}\n{after.id}", color=red)
            await bot_channel.send(admin.mention, embed=embed)
            await bot_test_channel.send(embed=embed)
            cell = await worksheet.find(f'{after.id}')
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
        right_name = await worksheet.cell(cell.row, cell.col - 2).value
        if after.display_name != right_name:
            await after.edit(nick=right_name)
            embed = Embed(
                title="WARNING", description="エントリー後のニックネーム変更は禁止されています\nchanging nickname after entry is prohibited", color=red)
            await bot_channel.send(after.mention, embed=embed)
        embed = Embed(title="ニックネーム変更検知", description=f"{after.id}", color=red)
        embed.add_field(name="before", value=before.display_name, inline=False)
        embed.add_field(name="after", value=after.display_name, inline=False)
        await bot_test_channel.send(embed=embed)
        return


@client.event
async def on_user_update(before, after):
    gc = gspread_asyncio.AsyncioGspreadClientManager(get_credits)
    agc = await gc.authorize()
    workbook = await agc.open_by_key('1WcwdGVf7NRKerM1pnZu9kIsgA0VYy5TddyGdKHBzAu4')
    worksheet = await workbook.worksheet('botデータベース（さわらないでね）')
    bot_channel = client.get_channel(1035946838487994449)  # ビト森杯 進行bot
    bot_test_channel = client.get_channel(897784178958008322)  # bot用チャット
    if before.display_name != after.display_name:
        cell = await worksheet.find(f'{after.id}')
        if cell is None:
            return
        right_name = await worksheet.cell(cell.row, cell.col - 2).value
        member = after.guild.get_member(after.id)
        if member.display_name != right_name:
            await member.edit(nick=right_name)
            embed = Embed(
                title="WARNING", description="エントリー後のニックネーム変更は禁止されています\nchanging nickname after entry is prohibited", color=red)
            await bot_channel.send(after.mention, embed=embed)
        embed = Embed(title="アカウント名変更検知", description=f"{after.id}", color=red)
        embed.add_field(name="before", value=before.display_name, inline=False)
        embed.add_field(name="after", value=after.display_name, inline=False)
        await bot_test_channel.send(embed=embed)
    return


@client.event
async def on_message(message):
    gc = gspread_asyncio.AsyncioGspreadClientManager(get_credits)
    agc = await gc.authorize()
    workbook = await agc.open_by_key('1WcwdGVf7NRKerM1pnZu9kIsgA0VYy5TddyGdKHBzAu4')
    worksheet = await workbook.worksheet('botデータベース（さわらないでね）')
    # channels
    bot_channel = client.get_channel(1035946838487994449)  # ビト森杯 進行bot
    bot_test_channel = client.get_channel(897784178958008322)  # bot用チャット
    image_channel = client.get_channel(952946795573571654)  # 画像提出
    contact = client.get_channel(1035964918198960128)  # 問い合わせ
    main_ch = client.get_channel(1030840789040893962)  # メイン会場
    # roles
    admin = bot_channel.guild.get_role(904368977092964352)  # ビト森杯運営
    roleA = bot_channel.guild.get_role(1035945116591996979)  # A部門 ビト森杯
    roleB = bot_channel.guild.get_role(1035945267733737542)  # B部門 ビト森杯
    roleLOOP = bot_channel.guild.get_role(1036149651847524393)  # LOOP部門 ビト森杯
    verified = bot_channel.guild.get_role(952951691047747655)  # verified
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
            await message.channel.send("Error: 検索結果なし\n`検索条件: 完全一致のみ`")
            return
        roleA = member.get_role(1035945116591996979)  # A部門 ビト森杯
        roleB = member.get_role(1035945267733737542)  # B部門 ビト森杯
        roleLOOP = member.get_role(1036149651847524393)  # LOOP部門 ビト森杯

        if all([roleA is None, roleB is None, roleLOOP is None]):
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
        cell = await worksheet.find(f'{member.id}')
        if bool(cell):
            await worksheet.update_cell(cell.row, cell.col, '')
            await worksheet.update_cell(cell.row, cell.col - 1, '')
            await worksheet.update_cell(cell.row, cell.col - 2, '')
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
        if bool(roleLOOP):
            await member.remove_roles(roleLOOP)
            await message.channel.send(f"{member.display_name}のビト森杯 LOOP部門エントリーを取り消しました。")
            await bot_test_channel.send(f"{member.display_name}のビト森杯 LOOP部門エントリーを取り消しました。")
        return

    if message.content.startswith("s.s") and not message.content.startswith("s.start") and not message.content.startswith("s.stage"):
        """
        LOOP非対応
        """
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
                    description=f"{stamps[i]}: {result_member.name}#{result_member.discriminator}", color=blue)
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
            if category == "🇦":
                entry_amount = int(await worksheet.acell('J1').value) + 1
                place_key = 0
                await worksheet.update_cell(1, 10, entry_amount)
                role = message.guild.get_role(
                    1035945116591996979)  # A部門 ビト森杯
            elif category == "🅱️":
                entry_amount = int(await worksheet.acell('J2').value) + 1
                place_key = 4
                await worksheet.update_cell(2, 10, entry_amount)
                role = message.guild.get_role(
                    1035945267733737542)  # B部門 ビト森杯
            await worksheet.update_cell(
                entry_amount + 1, place_key + 1, member.display_name)
            await worksheet.update_cell(
                entry_amount + 1, place_key + 2, read.content)
            await worksheet.update_cell(
                entry_amount + 1, place_key + 3, f"{member.id}")
            await member.add_roles(role)
            embed = Embed(title=f"{category}部門 受付完了",
                          description=f"{member.mention}\nエントリー受付が完了しました。", color=green)
            embed.set_author(name=f"{member.name}#{member.discriminator}",
                             icon_url=member.display_avatar.url)
            embed.add_field(name="名前", value=member.display_name, inline=False)
            embed.add_field(name="読みがな", value=read.content, inline=False)
            await message.channel.send(embed=embed)
            await bot_channel.send(embed=embed)
            embed_msg = await message.channel.send("処理中...")
            roleA = member.get_role(1035945116591996979)  # A部門 ビト森杯
            roleB = member.get_role(1035945267733737542)  # B部門 ビト森杯
        if bool(roleA):
            category = "A"
        elif bool(roleB):
            category = "🅱️部門"
        cell = await worksheet.find(f'{member.id}')
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
        read = await worksheet.cell(cell.row, cell.col - 1).value
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

    if message.content == "s.tm":
        """
        LOOP非対応
        """
        await message.channel.send("処理中...")
        names = await worksheet.col_values(13)
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

    if message.content == "entry":
        await message.delete(delay=1)
        admin = message.author.get_role(904368977092964352)  # ビト森杯運営
        if admin is None:
            return
        loop_emoji = await message.guild.fetch_emoji(885778461879320586)  # Loopボタンの絵文字
        buttonA = Button(
            label="Entry", style=discord.ButtonStyle.primary, emoji="🇦", custom_id="A")
        buttonB = Button(
            label="Entry", style=discord.ButtonStyle.red, emoji="🅱️", custom_id="B")
        buttonLOOP = Button(
            label="Entry loopstation", style=discord.ButtonStyle.green, emoji=loop_emoji, custom_id="LOOP")

        async def button_callback(interaction):
            roleA = interaction.user.get_role(920320926887862323)  # A部門 ビト森杯
            roleB = interaction.user.get_role(920321241976541204)  # B部門 ビト森杯
            roleLOOP = interaction.user.get_role(
                1036149651847524393)  # LOOP部門 ビト森杯

            if bool(roleA) and interaction.custom_id != "LOOP":
                await interaction.response.send_message("Error: すでに🇦部門にエントリーしています。", ephemeral=True)
                return
            if bool(roleB) and interaction.custom_id != "LOOP":
                await interaction.response.send_message("Error: すでに🅱️部門にエントリーしています。", ephemeral=True)
                return
            if bool(roleLOOP) and interaction.custom_id == "LOOP":
                await interaction.response.send_message("Error: すでにLOOP部門にエントリーしています。", ephemeral=True)
                return
            if interaction.locale != "ja":  # == "ja":
                await interaction.response.send_modal(entry_modal(name=interaction.user.display_name, category=interaction.custom_id))
                embed = Embed(title=f"interaction {interaction.custom_id}",
                              description=f"{interaction.user.display_name}\n{interaction.user.id}\n{interaction.locale}")
                await bot_test_channel.send(embed=embed)
                return

            await interaction.response.defer(ephemeral=True, invisible=False)
            # 問い合わせ転送
            thread = await find_contact(interaction.user.id, create=True)
            embed = Embed(title=f"{interaction.custom_id}部門エントリー",
                          description="notice for Japanese speaker:\n\nあなたのDiscord言語設定が日本語ではなかったため、海外からのアクセスと判定されました。\n日本語によるサポートをご希望の場合、`日本語希望` とご記入ください。")
            embed.add_field(name="detected language", value=interaction.locale)
            embed.set_author(name=interaction.user.display_name,
                             icon_url=interaction.user.display_avatar.url)
            await thread.send(f"{admin.mention}\n{interaction.user.mention}", embed=embed)
            # interactの返事
            if interaction.locale in ["zh-CN", "zh-TW"]:
                embed = Embed(title="contact required",
                              description=f"错误：请点击 {contact.mention} 联系我们\nお手数ですが {contact.mention}までお問い合わせください。", color=red)
            elif interaction.locale == "ko":
                embed = Embed(title="contact required",
                              description=f"문의는 {contact.mention} 로 보내주세요\nお手数ですが {contact.mention}までお問い合わせください。", color=red)
            else:
                embed = Embed(title="contact required",
                              description=f"please contact us via {contact.mention}\nお手数ですが {contact.mention}までお問い合わせください。", color=red)
            await interaction.followup.send(interaction.user.mention, embed=embed, ephemeral=True)
            # 応答時間短縮のためinteraction通知を後回しに
            embed = Embed(title=f"interaction {interaction.custom_id}",
                          description=f"{interaction.user.display_name}\n{interaction.user.id}\n{interaction.locale}")
            await bot_test_channel.send(embed=embed)
            return
        buttonA.callback = button_callback
        buttonB.callback = button_callback
        buttonLOOP.callback = button_callback
        view = View(timeout=None)
        view.add_item(buttonA)
        view.add_item(buttonB)
        view.add_item(buttonLOOP)
        await message.channel.send(view=view)
        return

    if message.content == "contact":
        await message.delete(delay=1)
        button = Button(
            label="お問い合わせはこちら", style=discord.ButtonStyle.primary)

        async def button_callback(interaction):
            thread = await find_contact(member_id=interaction.user.id, create=True)
            await interaction.response.send_message(f"あなた専用のお問い合わせチャンネルを作成しました\n{thread.jump_url}", ephemeral=True)
            await new_contact(interaction.user.id)
        button.callback = button_callback
        view = View(timeout=None)
        view.add_item(button)
        await message.channel.send(view=view)

client.run("OTUyOTYyOTAyMzI1ODg2OTg2.GaOseR.nhstAXFsu7mIyenljeWbC6liMf3T2OldssKq_E")
