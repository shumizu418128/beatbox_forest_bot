# -*- coding: utf-8 -*-
import asyncio
import re
from difflib import get_close_matches

import discord
import gspread_asyncio
from discord import Embed
from discord.ui import Button, InputText, Modal, View
from neologdn import normalize
from oauth2client.service_account import ServiceAccountCredentials
from PIL import Image, ImageDraw, ImageFont

intents = discord.Intents.all()  # デフォルトのIntentsオブジェクトを生成
intents.typing = False  # typingを受け取らないように
client = discord.Bot(intents=intents)
re_hiragana = re.compile(r'^[ぁ-ゞ　 ー]+$')
green = 0x00ff00
yellow = 0xffff00
red = 0xff0000
blue = 0x00bfff
ox_list = ["⭕", "❌"]
print(f"ビト森杯bot (Local): {discord.__version__}")


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
        worksheet = await workbook.worksheet('botデータベース（参加者）')
        materials = {"A": {"role": roleA, "number": 0},
                     "B": {"role": roleB, "number": 1},
                     "LOOP": {"role": roleLOOP, "number": 2}}
        material = materials[self.custom_id]
        # DB更新
        await interaction.user.add_roles(material["role"])
        entry_amount = await worksheet.acell(
            f'N{material["number"] + 1}')
        entry_amount = int(entry_amount.value) + 1
        # amount更新
        await worksheet.update_cell(material["number"] + 1, 14, str(entry_amount))
        # 名前
        await worksheet.update_cell(entry_amount + 1, material["number"] * 4 + 1, interaction.user.display_name)
        # 読みがな
        await worksheet.update_cell(entry_amount + 1, material["number"] * 4 + 2, self.children[0].value)
        # id
        await worksheet.update_cell(entry_amount + 1, material["number"] * 4 + 3, str(interaction.user.id))
        return


class sponsor_modal(Modal):
    def __init__(self) -> None:
        super().__init__(title="スポンサー申請", custom_id="modal_sponsor")
        self.add_item(InputText(label="支援額をご記入ください", placeholder="例：1000円"))
        self.add_item(InputText(label="ご希望の支払い方法をご記入ください",
                      placeholder="例：paypay, amazonギフト券"))
        self.add_item(InputText(label="匿名支援を希望しますか？（はい or いいえ）",
                      value="いいえ", placeholder="はい or いいえ"))
        self.add_item(
            InputText(label="ジャッジ参加を希望しますか？（はい or いいえ）", placeholder="はい or いいえ"))
        self.add_item(InputText(label="備考欄", placeholder="スポンサーのご協力、ありがとうございます。",
                      style=discord.InputTextStyle.long, required=False))

    async def callback(self, interaction):
        await interaction.response.defer(invisible=False)
        embed1 = Embed(title="ご協力ありがとうございます！",
                       description="入力内容変更のご希望やご質問は、いつでもこのチャンネルにご記入ください。\n\n入力内容", color=green)
        embed1.set_author(name=f"{interaction.user.display_name}さん",
                          icon_url=interaction.user.display_avatar.url)
        embed1.add_field(
            name="支援金額", value=self.children[0].value, inline=False)
        embed1.add_field(
            name="支払方法", value=self.children[1].value, inline=False)
        embed1.add_field(name="匿名", value=self.children[2].value, inline=False)
        embed1.add_field(
            name="ジャッジ参加", value=self.children[3].value, inline=False)
        if bool(self.children[4].value):
            embed1.add_field(
                name="備考", value=self.children[4].value, inline=False)
        embed2 = Embed(
            title="お支払いについて", description="送金先は種田芽衣子Mayco#2589になります。\n\n頂いたお金はスポンサー代表・種田芽衣子氏により管理され、全額賞金として活用されます。", color=blue)
        admin = interaction.guild.get_role(904368977092964352)  # ビト森杯運営
        await interaction.followup.send(f"{admin.mention}\n{interaction.user.mention}", embeds=[embed1, embed2])
        # DBアクセス準備
        gc = gspread_asyncio.AsyncioGspreadClientManager(get_credits)
        agc = await gc.authorize()
        workbook = await agc.open_by_key('1WcwdGVf7NRKerM1pnZu9kIsgA0VYy5TddyGdKHBzAu4')
        worksheet = await workbook.worksheet('botデータベース（スポンサー様）')
        amount = await worksheet.acell('I1')
        amount = int(amount.value) + 1
        # amount更新
        await worksheet.update_cell(1, 9, str(amount))
        # discordアカウント名
        await worksheet.update_cell(amount + 1, 1, str(interaction.user))
        # 金額
        await worksheet.update_cell(amount + 1, 2, self.children[0].value)
        # 支払い手段
        await worksheet.update_cell(amount + 1, 3, self.children[1].value)
        # 匿名希望
        await worksheet.update_cell(amount + 1, 4, self.children[2].value)
        # ジャッジ参加希望
        await worksheet.update_cell(amount + 1, 5, self.children[3].value)
        # 備考
        await worksheet.update_cell(amount + 1, 6, self.children[4].value)
        # id
        await worksheet.update_cell(amount + 1, 7, str(interaction.user.id))
        return


# 問い合わせで表示する3種類のボタン
async def get_view_contact():
    button_call_admin = Button(
        label="問い合わせ", style=discord.ButtonStyle.primary, custom_id="call_admin")  # 青
    button_cancel = Button(
        label="ビト森杯エントリーキャンセル", style=discord.ButtonStyle.red, custom_id="cancel")
    button_sponsor = Button(
        label="スポンサー支援希望", style=discord.ButtonStyle.green, custom_id="button_sponsor")

    async def button_cancel_callback(interaction):
        contact = client.get_channel(1035964918198960128)  # 問い合わせ
        admin = interaction.guild.get_role(904368977092964352)  # ビト森杯運営
        roleA = interaction.user.get_role(1035945116591996979)  # A部門 ビト森杯
        roleB = interaction.user.get_role(1035945267733737542)  # B部門 ビト森杯
        roleLOOP = interaction.user.get_role(
            1036149651847524393)  # LOOP部門 ビト森杯
        # Loopボタンの絵文字
        loop_emoji = await interaction.guild.fetch_emoji(885778461879320586)
        if all([roleA is None, roleB is None, roleLOOP is None]):
            await interaction.response.send_message(f"{interaction.user.mention}はビト森杯にエントリーしていません")
            return
        embed = Embed(title="ビト森杯エントリーを取り消します",
                      description="⭕ `OK`\n❌ 中止", color=yellow)
        notice = await interaction.followup.send(embed=embed)
        await notice.add_reaction("⭕")
        await notice.add_reaction("❌")

        def check(reaction, user):
            return user == interaction.user and reaction.emoji in ox_list and reaction.message == notice

        try:
            reaction, _ = await client.wait_for('reaction_add', timeout=10.0, check=check)
        except asyncio.TimeoutError:
            await notice.clear_reactions()
            await notice.reply("Error: Timeout\nもう1度お試しください")
            return
        await notice.clear_reactions()
        if reaction.emoji == "❌":
            await notice.delete(delay=1)
            return
        await interaction.channel.send("処理中...")
        # DBアクセス準備
        gc = gspread_asyncio.AsyncioGspreadClientManager(get_credits)
        agc = await gc.authorize()
        workbook = await agc.open_by_key('1WcwdGVf7NRKerM1pnZu9kIsgA0VYy5TddyGdKHBzAu4')
        worksheet = await workbook.worksheet('botデータベース（参加者）')
        for _ in range(bool(roleA) + bool(roleB) + bool(roleLOOP)):
            cell = await worksheet.find(f'{interaction.user.id}')
            if bool(cell):
                await worksheet.update_cell(cell.row, cell.col, '')
                await worksheet.update_cell(cell.row, cell.col - 1, '')
                await worksheet.update_cell(cell.row, cell.col - 2, '')
            else:
                await interaction.channel.send(f"{admin.mention}\nError: DB登録なし\nしばらくお待ちください")
                return
        roles = ""
        if bool(roleA):
            await interaction.user.remove_roles(roleA)
            roles += "🇦部門 "
        if bool(roleB):
            await interaction.user.remove_roles(roleB)
            roles += "🅱️部門 "
        if bool(roleLOOP):
            await interaction.user.remove_roles(roleLOOP)
            roles += f"{str(loop_emoji)}LOOP部門"
        embed = Embed(title="キャンセル完了",
                      description=f"以下の部門エントリーを取り消しました。\n{roles}", color=green)
        await interaction.channel.send(embed=embed)
        await contact.send(interaction.user.mention, embed=embed)
        return

    async def button_call_admin_callback(interaction):
        contact = client.get_channel(1035964918198960128)  # 問い合わせ
        admin = interaction.user.get_role(904368977092964352)  # ビト森杯運営
        await contact.set_permissions(interaction.user, send_messages_in_threads=True)
        embed = Embed(title="このチャンネルにご用件をご記入ください",
                      description="運営メンバーが対応します", color=blue)
        await interaction.response.send_message(f"{admin.mention} {interaction.user.mention}", embed=embed)
        return

    async def button_sponsor_callback(interaction):
        roleA = interaction.user.get_role(1035945116591996979)  # A部門 ビト森杯
        roleB = interaction.user.get_role(1035945267733737542)  # B部門 ビト森杯
        roleLOOP = interaction.user.get_role(
            1036149651847524393)  # LOOP部門 ビト森杯
        if all([roleA is None, roleB is None, roleLOOP is None]):
            await interaction.response.send_modal(sponsor_modal())
            return
        await interaction.response.send_message("申し訳ありません。ビト森杯出場者の方からのスポンサー支援は辞退させていただいております。\n賭博法に抵触する恐れがあるためです。")

    button_cancel.callback = button_cancel_callback
    button_call_admin.callback = button_call_admin_callback
    button_sponsor.callback = button_sponsor_callback
    view = View(timeout=None)
    view.add_item(button_cancel)
    view.add_item(button_call_admin)
    view.add_item(button_sponsor)
    return view


# エントリーボタン3種類
async def get_view_entry():
    contact = client.get_channel(1035964918198960128)  # 問い合わせ
    # Loopボタンの絵文字
    loop_emoji = await contact.guild.fetch_emoji(885778461879320586)
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
            embed = Embed(
                title="Error", description="すでに🇦部門にエントリーしています。", color=red)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if bool(roleB) and interaction.custom_id != "LOOP":
            embed = Embed(
                title="Error", description="すでに🅱️部門にエントリーしています。", color=red)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if bool(roleLOOP) and interaction.custom_id == "LOOP":
            embed = Embed(
                title="Error", description=f"すでに{loop_emoji}LOOP部門にエントリーしています。", color=red)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if interaction.custom_id == "LOOP" and interaction.user.is_on_mobile():
            embed = Embed(
                title="Error", description=f"{loop_emoji}LOOP部門は、PCからのみエントリー可能です。\nYou must access from PC to entry LOOP category", color=red)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if interaction.locale == "ja":
            await interaction.response.send_modal(entry_modal(name=interaction.user.display_name, category=interaction.custom_id))
            return
        thread = await find_contact(interaction.user.id, interaction.locale)
        if "ja" in thread.name:
            await interaction.response.send_modal(entry_modal(name=interaction.user.display_name, category=interaction.custom_id))
            return
        # 海外エントリーの処理
        if interaction.locale == "zh-TW":
            embed = Embed(title="contact required",
                          description=f"錯誤：請點一下 {thread.mention} 聯係我們\nお手数ですが {thread.mention} までお問い合わせください。", color=red)
        elif interaction.locale == "zh-CN":
            embed = Embed(title="contact required",
                          description=f"错误：请点击 {thread.mention} 联系我们\nお手数ですが {thread.mention} までお問い合わせください。", color=red)
        elif interaction.locale == "ko":
            embed = Embed(title="contact required",
                          description=f"문의는 {thread.mention} 로 보내주세요\nお手数ですが {thread.mention} までお問い合わせください。", color=red)
        else:
            embed = Embed(title="contact required",
                          description=f"please contact us via {thread.mention}\nお手数ですが {thread.mention} までお問い合わせください。", color=red)
        await interaction.response.send_message(embed=embed, ephemeral=True)

        embed = Embed(title=f"{interaction.custom_id}部門 海外エントリー",
                      description="Please hold on, the moderator will be here soon\n請稍候片刻, 正與管理員對接\n대회 운영자가 대응합니다. 잠시 기다려주십시오\n\n`あなたは海外からのアクセスと判定されました。\n日本語のサポートをご希望の場合、このチャンネルに`\n\n **日本語希望** \n\n`とご記入ください。`", color=blue)
        embed.set_footer(text=f"言語コード: {interaction.locale}")
        # f"{admin.mention}\n{interaction.user.mention}",
        await thread.send(embed=embed)

        def check(m):
            return m.channel == thread and m.content == "日本語希望"

        _ = await client.wait_for('message', check=check)
        await thread.edit(name=f"{interaction.user.id}_ja")
        view = View(timeout=None)
        view.add_item(buttonA)
        view.add_item(buttonB)
        view.add_item(buttonLOOP)
        embed = Embed(
            title="大変失礼しました", description="今後、日本語モードで対応いたします。\n\n以下のボタンからエントリーできます。", color=blue)
        await thread.send(embed=embed, view=view)
        return

    buttonA.callback = button_callback
    buttonB.callback = button_callback
    buttonLOOP.callback = button_callback
    view = View(timeout=None)
    view.add_item(buttonA)
    view.add_item(buttonB)
    view.add_item(buttonLOOP)
    return view


# 問い合わせページ命名規則 {id}_{locale}
# 問い合わせthreadを検索 localeがあれば作成もする
async def find_contact(member_id: int, *locale: str):
    contact = client.get_channel(1035964918198960128)  # 問い合わせ
    threads = contact.threads
    thread_names = [thread.name.split("_")[0] for thread in threads]
    if str(member_id) in thread_names:
        index = thread_names.index(str(member_id))
        return threads[index]
    if bool(locale):
        # ※localeがtupleになってしまっているので[0]で取り出す
        thread = await contact.create_thread(name=f"{member_id}_{locale[0]}")
        return thread
    return None


# 新規問い合わせを作成
async def new_contact(member_id: int, locale: str):
    announce = client.get_channel(1035965200341401600)  # ビト森杯お知らせ
    contact = client.get_channel(1035964918198960128)  # 問い合わせ
    admin = contact.guild.get_role(904368977092964352)  # ビト森杯運営
    # Loopボタンの絵文字
    loop_emoji = await contact.guild.fetch_emoji(885778461879320586)
    member = contact.guild.get_member(member_id)
    roleA = member.get_role(1035945116591996979)  # A部門 ビト森杯
    roleB = member.get_role(1035945267733737542)  # B部門 ビト森杯
    roleLOOP = member.get_role(1036149651847524393)  # LOOP部門 ビト森杯
    thread = await find_contact(member_id)
    if thread is None:
        thread = await contact.create_thread(name=f"{member_id}_{locale}")
    await contact.set_permissions(member, send_messages_in_threads=False)
    locale = thread.name.split("_")[1]
    category = ""
    if bool(roleA):
        category += "🇦部門 "
    elif bool(roleB):
        category += "🅱️部門 "
    if bool(roleLOOP):
        category += f"{str(loop_emoji)}LOOP部門"
    if category == "":
        category = "なし"
    embed = Embed(description=f"{member_id}", color=blue)
    embed.set_author(
        name=f"contact from {member.display_name}", icon_url=member.display_avatar.url)
    embed.add_field(name="エントリー部門", value=category, inline=False)
    if category != "なし":
        # DBアクセス準備
        gc = gspread_asyncio.AsyncioGspreadClientManager(get_credits)
        agc = await gc.authorize()
        workbook = await agc.open_by_key('1WcwdGVf7NRKerM1pnZu9kIsgA0VYy5TddyGdKHBzAu4')
        worksheet = await workbook.worksheet('botデータベース（参加者）')
        cell = await worksheet.find(f'{member.id}')
        if cell is None:
            await thread.send(f"{admin.mention}\nError: DB cell検索結果なし", embed=embed)
        else:
            read = await worksheet.cell(cell.row, cell.col - 1).value
            if read is None:
                await thread.send(f"{admin.mention}\nError: DB検索結果なし cell空欄", embed=embed)
            else:
                embed.add_field(name="読みがな", value=read, inline=False)
                await thread.send(embed=embed)

    if locale != "ja":
        embed = Embed(title="please write your inquiry here",
                      description="請把疑問寫在這裡\n문의 내용을 이 채널에 기입해주세요\n\n`あなたは海外からのアクセスと判定されました。\n日本語のサポートをご希望の場合、このチャンネルに`\n\n **日本語希望** \n\n`とご記入ください。`", color=blue)
        embed.set_footer(text=f"言語コード: {locale}")
        await thread.send(embed=embed)  # f"{admin.mention}\n{member.mention}",
        await contact.set_permissions(member, send_messages_in_threads=True)

        def check(m):
            return m.channel == thread and m.content == "日本語希望"

        _ = await client.wait_for('message', check=check)
        await thread.edit(name=f"{member_id}_ja")
        embed = Embed(title="大変失礼しました",
                      description="今後、日本語モードで対応いたします。", color=blue)
        await thread.send(embed=embed)
        await asyncio.sleep(2)

    embed = Embed(title="お問い合わせの前に",
                  description=f"ビト森杯の情報は\n{announce.mention}\nまたは\nビト森ホームページ\nhttps://bitomori.jimdofree.com/ \nに掲載されています。\n\nこれらの内容をご確認の上、ご質問がありましたら下の問い合わせボタンを押してください。", color=yellow)
    view = await get_view_contact()
    await thread.send(embed=embed, view=view)
    return


async def contact_button():
    button = Button(
        label="お問い合わせはこちら contact us", style=discord.ButtonStyle.primary, custom_id="contact")

    async def button_callback(interaction):
        thread = await find_contact(interaction.user.id, interaction.locale)
        await interaction.response.send_message(f"あなた専用のお問い合わせチャンネルを作成しました\n{thread.jump_url}", ephemeral=True)
        await new_contact(interaction.user.id, interaction.locale)

    button.callback = button_callback
    view = View(timeout=None)
    view.add_item(button)
    return view


# ニックネーム一致確認
async def name_check(member_id: int):
    # DBアクセス準備
    bot_channel = client.get_channel(1035946838487994449)  # ビト森杯 進行bot
    member = bot_channel.guild.get_member(member_id)
    admin = bot_channel.guild.get_role(904368977092964352)  # ビト森杯運営
    roleA = member.get_role(1035945116591996979)  # A部門 ビト森杯
    roleB = member.get_role(1035945267733737542)  # B部門 ビト森杯
    roleLOOP = member.get_role(1036149651847524393)  # LOOP部門 ビト森杯
    if all([roleA is None, roleB is None, roleLOOP is None]):
        return
    gc = gspread_asyncio.AsyncioGspreadClientManager(get_credits)
    agc = await gc.authorize()
    workbook = await agc.open_by_key('1WcwdGVf7NRKerM1pnZu9kIsgA0VYy5TddyGdKHBzAu4')
    worksheet = await workbook.worksheet('botデータベース（参加者）')
    if bool(roleA) and bool(roleB):
        embed = Embed(
            title="AB重複エントリー検知", description=f"{member.display_name}\n{member.id}", color=red)
        await bot_channel.send(admin.mention, embed=embed)
    cell = await worksheet.find(f'{member.id}')
    if cell is None:
        embed = Embed(title="ニックネーム変更・DB破損検知", description="自動修正失敗", color=red)
        embed.add_field(name=member.display_name, value=member.id)
        await bot_channel.send(admin.mention, embed=embed)
        return
    right_name = await worksheet.cell(cell.row, cell.col - 2).value
    if member.display_name != right_name:
        await member.edit(nick=right_name)
        embed = Embed(
            title="WARNING ニックネーム変更検知", description="エントリー後のニックネーム変更は禁止されています。元のニックネームに自動修正しました。\nchanging nickname after entry is prohibited", color=red)
        await bot_channel.send(member.mention, embed=embed)
    return


@client.event
async def on_member_update(before, after):
    if before.display_name != after.display_name:
        await name_check(after.id)


@client.event
async def on_user_update(before, after):
    if before.display_name != after.display_name:
        await name_check(after.id)


@client.event
async def on_interaction(interaction):
    if interaction.channel.id == 930446820839157820:  # バトスタ参加
        return
    bot_test_channel = client.get_channel(897784178958008322)  # bot用チャット
    interaction_type = "button"
    if interaction.type == discord.InteractionType.modal_submit:
        interaction_type = "modal"
    embed = Embed(title=f"interaction: {interaction_type}",
                  description=f"```custom_id: {interaction.custom_id}\nmember_id: {interaction.user.id}\nchannel: {interaction.channel.name}```{interaction.channel.jump_url}", color=blue)
    embed.set_author(name=interaction.user.display_name,
                     icon_url=interaction.user.display_avatar.url)
    await bot_test_channel.send(embed=embed)


@client.event
async def on_message(message):
    image_channel = client.get_channel(952946795573571654)  # 画像提出
    bot_channel = client.get_channel(1035946838487994449)  # ビト森杯 進行bot
    main_ch = client.get_channel(1030840789040893962)  # メイン会場
    verified = bot_channel.guild.get_role(952951691047747655)  # verified
    # Loopボタンの絵文字
    loop_emoji = await bot_channel.guild.fetch_emoji(885778461879320586)

    if message.author.id == 952962902325886986:  # ビト森杯bot
        return

    if message.content == "s.test":
        await message.channel.send(f"ビト森杯 (Local): {client.latency}")
        return

    if message.content.startswith("s.cancel"):
        await message.delete(delay=1)
        admin = message.author.get_role(904368977092964352)  # ビト森杯運営
        if admin is None:
            await message.channel.send(f"{message.author.mention}\nError: s.cancelはビト森杯運営専用コマンドです\n\n```{message.content}```")
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
            embed = Embed(
                title="Error", description=f"{member.display_name}はビト森杯にエントリーしていません", color=red)
            await message.channel.send(embed=embed)
            return
        embed = Embed(title="エントリーキャンセル",
                      description=f"{member.display_name}のビト森杯エントリーを取り消しますか？\n\n⭕ `OK`\n❌ 中止", color=yellow)
        notice = await message.channel.send(embed=embed)
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
        # DBアクセス準備
        gc = gspread_asyncio.AsyncioGspreadClientManager(get_credits)
        agc = await gc.authorize()
        workbook = await agc.open_by_key('1WcwdGVf7NRKerM1pnZu9kIsgA0VYy5TddyGdKHBzAu4')
        worksheet = await workbook.worksheet('botデータベース（参加者）')
        cell = await worksheet.find(f'{member.id}')
        if bool(cell):
            await worksheet.update_cell(cell.row, cell.col, '')
            await worksheet.update_cell(cell.row, cell.col - 1, '')
            await worksheet.update_cell(cell.row, cell.col - 2, '')
            await message.channel.send(f"DB削除完了 `{cell.row}, {cell.col}`")
        else:
            await message.channel.send("Error: DB登録なし")
        roles = ""
        if bool(roleA):
            await member.remove_roles(roleA)
            roles += "🇦部門 "
        if bool(roleB):
            await member.remove_roles(roleB)
            roles += "🅱️部門 "
        if bool(roleLOOP):
            await member.remove_roles(roleLOOP)
            roles += f"{str(loop_emoji)}LOOP部門"
        embed = Embed(title="キャンセル完了",
                      description=f"以下の部門エントリーを取り消しました。\n{roles}", color=green)
        await message.channel.send(embed=embed)
        await bot_channel.send(member.mention, embed=embed)
        return

    if message.content.startswith("s.s") and not message.content.startswith("s.start") and not message.content.startswith("s.stage"):
        """
        LOOP非対応
        """
        await message.delete(delay=1)
        input_ = message.content[4:]
        if input_ == "":
            embed = Embed(
                description="`cancelと入力するとキャンセルできます`\n検索したいワードを入力してください", color=blue)
            await message.channel.send(embed=embed)

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
        embed = Embed(title="検索中...", color=blue)
        # DBアクセス準備
        gc = gspread_asyncio.AsyncioGspreadClientManager(get_credits)
        agc = await gc.authorize()
        workbook = await agc.open_by_key('1WcwdGVf7NRKerM1pnZu9kIsgA0VYy5TddyGdKHBzAu4')
        worksheet = await workbook.worksheet('botデータベース（参加者）')
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
                embed = Embed(title="検索結果なし",
                              description=f"`検索ワード：`{input_}", color=red)
                await embed_msg.edit(embed=embed)
                await embed_msg.add_reaction("🗑️")

                def check(reaction, user):
                    return user == message.author and reaction.emoji == "🗑️" and reaction.message == embed_msg

                _, _ = await client.wait_for('reaction_add', check=check)
                await embed_msg.delete()
                return
            results = []
            embeds = []
            embed = Embed(
                title="検索結果", description=f"`検索ワード：`{input_}", color=green)
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
            embed.set_author(name=str(member),
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
            embed = Embed(
                description=f"{member.mention}\nビト森杯にエントリーしていません", color=blue)
            embed.set_author(name=str(member),
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
                embed = Embed(title=f"{member.display_name} {category}部門 手動エントリー",
                              description="`cancelと入力するとキャンセルされます`\n名前の読みかたを入力してください", color=blue)
                typing = await message.channel.send(embed=embed)

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
                role_id = 1035945116591996979  # A部門 ビト森杯
            elif category == "🅱️":
                entry_amount = int(await worksheet.acell('J2').value) + 1
                place_key = 4
                await worksheet.update_cell(2, 10, entry_amount)
                role_id = 1035945267733737542  # B部門 ビト森杯
            role = message.guild.get_role(role_id)
            await member.add_roles(role)
            await worksheet.update_cell(
                entry_amount + 1, place_key + 1, member.display_name)
            await worksheet.update_cell(
                entry_amount + 1, place_key + 2, read.content)
            await worksheet.update_cell(
                entry_amount + 1, place_key + 3, f"{member.id}")
            embed = Embed(title=f"{category}部門 受付完了",
                          description=f"{member.mention}\nエントリー受付が完了しました。", color=green)
            embed.set_author(name=str(member),
                             icon_url=member.display_avatar.url)
            embed.add_field(name="名前", value=member.display_name, inline=False)
            embed.add_field(name="読みがな", value=read.content, inline=False)
            await message.channel.send(embed=embed)
            await bot_channel.send(member.mention, embed=embed)
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
            embed.set_author(name=str(member),
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
        embed = Embed(description=member.mention, color=blue)
        embed.set_author(name=str(member),
                         icon_url=member.display_avatar.url)
        embed.add_field(name="読みがな", value=read, inline=False)
        embed.add_field(name="エントリー部門", value=category, inline=False)
        embed.add_field(name="ID", value=member.id, inline=False)
        view = View(timeout=None)
        check_mic = member.get_role(952951691047747655)  # verified
        if check_mic is None and category == "🅱️部門":
            embed.add_field(name="マイク設定確認", value="❌", inline=False)
            button = Button(
                label="verify", style=discord.ButtonStyle.success, emoji="🎙️", custom_id="mic_verify")

            async def button_callback(interaction):
                admin = interaction.user.get_role(904368977092964352)  # ビト森杯運営
                if bool(admin):
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
            label="メイン会場へ移動", style=discord.ButtonStyle.primary, custom_id="move")

        async def button_move_callback(interaction):
            admin = interaction.user.get_role(904368977092964352)  # ビト森杯運営
            if bool(admin):
                try:
                    await member.move_to(main_ch)
                except discord.errors.HTTPException as e:
                    embed = Embed(title="Error", description=e, color=red)
                    await interaction.response.send_message(embed=embed)
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
            embed = Embed(
                title="Error", description="入力方法が間違っています。\n\n`cancelと入力するとキャンセルできます`\nもう一度入力してください", color=red)
            await message.channel.send(embed=embed)

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
        embed = Embed(
            title="投票箱", description=f"1⃣ {names[0]}\n2⃣ {names[1]}", color=blue)
        poll = await message.channel.send(embed=embed)
        await poll.add_reaction("1⃣")
        await poll.add_reaction("2⃣")
        return

    if message.content == "s.tm":
        """
        LOOP非対応
        """
        # DBアクセス準備
        gc = gspread_asyncio.AsyncioGspreadClientManager(get_credits)
        agc = await gc.authorize()
        workbook = await agc.open_by_key('1WcwdGVf7NRKerM1pnZu9kIsgA0VYy5TddyGdKHBzAu4')
        worksheet = await workbook.worksheet('botデータベース（参加者）')
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
        view = await get_view_entry()
        await message.channel.send(view=view)
        return

    if message.content == "contact" or message.channel.id == 1035965200341401600:  # お知らせ
        view = await contact_button()
        await message.channel.send(view=view)
        if message.content == "contact":
            await message.delete(delay=1)

client.run("OTUyOTYyOTAyMzI1ODg2OTg2.GaOseR.nhstAXFsu7mIyenljeWbC6liMf3T2OldssKq_E")
