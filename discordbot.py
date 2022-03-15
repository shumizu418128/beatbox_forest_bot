import discord
from datetime import datetime
from asyncio import sleep
from PIL import Image
import numpy as np
import cv2
from scipy.spatial import distance
import pyocr
import pyocr.builders
intents = discord.Intents.all()  # デフォルトのIntentsオブジェクトを生成
intents.typing = False  # typingを受け取らないように
client = discord.Client(intents=intents)
print("ビト森杯bot: 起動完了")
import os
print(os.system('which tesseract-ocr'))

@client.event
async def on_member_update(before, after):
    if str(before.roles) != str(after.roles):
        id_before = [role.id for role in before.roles]
        id_after = [role.id for role in after.roles]
        channel = client.get_channel(916608669221806100)  # ビト森杯 進行bot
        if 920320926887862323 in id_after and 920320926887862323 not in id_before:  # A部門ビト森杯
            await channel.send(f"{after.mention}\nビト森杯🇦部門\nエントリーを受け付けました：{after.display_name}さん\nentry completed👍\n\n名前を変更する際は、一度エントリーをキャンセルしてください。")
        if 920320926887862323 in id_before and 920320926887862323 not in id_after:  # A部門ビト森杯
            await channel.send(f"{after.mention}\nビト森杯🇦部門\nエントリーを取り消しました❎\nentry canceled")
        if 920321241976541204 in id_after and 920321241976541204 not in id_before:  # B部門ビト森杯
            await channel.send(f"{after.mention}\nビト森杯🅱️部門\nエントリーを受け付けました：{after.display_name}さん\nentry completed👍\n\n名前を変更する際は、一度エントリーをキャンセルしてください。")
        if 920321241976541204 in id_before and 920321241976541204 not in id_after:  # B部門ビト森杯
            await channel.send(f"{after.mention}\nビト森杯🅱️部門\nエントリーを取り消しました❎\nentry canceled")
        return

@client.event
async def on_raw_reaction_add(payload):
    emoji_list = ["⭕", "❌"]
    if payload.emoji.name in emoji_list:
        roles = payload.member.roles
        for role in roles:
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
        return

@client.event
async def on_message(message):
    if message.content.startswith("contact:"):
        input_ = [j for j in message.content.split()]
        name = message.guild.get_member(int(input_[1]))
        if name is None:
            await message.channel.send("Error: ID検索結果なし")
            return
        await message.channel.send(f"{name.mention}\nご用件をこのチャンネルにご記入ください。\nplease write your inquiry here.")
        roles = name.roles
        for role in roles:
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
        author = message.author.roles
        for role in author:
            if role.id == 904368977092964352:  # ビト森杯運営
                input_ = message.content[9:]  # s.cancel をカット
                try:
                    name = message.guild.get_member(int(input_))
                except ValueError:
                    name = message.guild.get_member_named(input_)
                if name is None:
                    await message.channel.send("検索結果なし")
                    return
                roles = name.roles
                for role in roles:
                    if role.id == 920320926887862323:  # A部門 ビト森杯
                        roleA = message.guild.get_role(920320926887862323)  # A部門 ビト森杯
                        await name.remove_roles(roleA)
                        await message.channel.send("%sさんのビト森杯 🇦部門エントリーを取り消しました。" % (name.display_name))
                        return
                    if role.id == 920321241976541204:  # B部門 ビト森杯
                        roleB = message.guild.get_role(920321241976541204)  # B部門 ビト森杯
                        await name.remove_roles(roleB)
                        await message.channel.send("%sさんのビト森杯 🅱️部門エントリーを取り消しました。" % (name.display_name))
                        return
                await message.channel.send("%sさんはビト森杯にエントリーしていません" % (name.display_name))
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

    if message.content.startswith("s.entry"):
        await message.delete(delay=1)
        input_ = message.content[8:]  # s.entry をカット
        try:
            name = message.guild.get_member(int(input_))
        except ValueError:
            name = message.guild.get_member_named(input_)
        if name is None:
            await message.channel.send("検索結果なし")
            return
        roles = name.roles
        for role in roles:
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

    if message.content.startswith("手動チェックに切替:") and message.channel.id == 952946795573571654:  # 画像提出
        await message.delete(delay=1)
        contents = [(j) for j in message.content.split()]
        member = message.guild.get_member(int(contents[1]))
        admin = message.guild.get_role(904368977092964352)
        await message.channel.send(f"{member.author}\nbotでの画像分析ができない画像のため、運営による手動チェックに切り替えます。\nしばらくお待ちください。\n\n{admin.mention}")
        await message.add_reaction("⭕")
        await message.add_reaction("❌")
        return

    if len(message.attachments) != 2 and message.channel.id == 952946795573571654:  # 画像提出
        await message.delete(delay=1)
        await message.channel.send(f"{message.author.mention}\nError: 画像を2枚同時に投稿してください。")
        if len(message.attachments) == 1:
            await message.channel.send("画像1枚では、すべての設定項目が画像内に収まりません。")
        return

    if len(message.attachments) == 2 and message.channel.id == 952946795573571654:  # 画像提出
        # 初期設定
        try:
            channel = await message.channel.create_thread(name=f"{message.author.display_name} 分析ログ", message=message)
        except AttributeError:
            return
        pyocr.tesseract.TESSERACT_CMD = '/app/.apt/usr/share/tesseract-ocr'
        tools = pyocr.get_available_tools()
        tool = tools[0]
        langs = tool.get_available_languages()
        lang = langs[1]
        file_names = []
        error_msg = []
        error_code = 0
        for a in message.attachments:
            if a.content_type == "image/jpeg" or a.content_type == "image/png":
                if a.height < a.width:
                    await channel.send(f"手動チェックに切替: {message.author.id}")
                    return
                dt_now = datetime.now()
                name = "/tmp/" + dt_now.strftime("%H.%M.%S.png")
                await a.save(name)
                file_names.append(name)
                await sleep(1)
            else:
                await channel.send("Error: jpg, jpeg, png画像を投稿してください。")
                return
        await channel.send("attachments save: finish")
        # 設定オン座標調査
        xy_list = []
        img0 = cv2.imread(file_names[0])
        img1 = cv2.imread(file_names[1])
        imgs = {"file0": img0, "file1": img1}
        for i in range(2):
            h, w, c = imgs[f"file{i}"].shape  # 高さ、幅
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
        await channel.send("coordinate detection: finish")
        # ワード検出
        all_text = ""
        for i in range(2):
            text1 = tool.image_to_string(Image.open(
                file_names[i]), lang=lang, builder=pyocr.builders.TextBuilder(tesseract_layout=12))
            text2 = tool.image_to_string(Image.open(
                file_names[i]), lang=lang, builder=pyocr.builders.TextBuilder(tesseract_layout=6))
            all_text += text1 + text2
        if "troubleshooting" in all_text:
            await channel.send(f"手動チェックに切替: {message.author.id}")
            return
        word_list = ["自動検出", "感度", "ノイズ抑制", "エコー除去", "ノイズ低減", "音量調節の自動化", "高度音声検出"]
        if "ノイズ抑制" not in all_text:  # ノイズ抑制は認識精度低 「マイクからのバックグラウンドノイズ」で代用
            error_msg.append("・例外検知（問題なし）: ノイズ抑制検知失敗")
            word_list[2] = "バックグラウンドノイズ"
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
        await channel.send("word detection: finish")
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
                        if i == 1:
                            for xy in xy_1:
                                if distance.euclidean(place_text, (xy)) < 200:
                                    error_msg.append("・例外検知（問題なし）: モバイルボイスオーバーレイ")
                                    xy_1.remove(xy)
                                    break
                        continue
        for xy in xy_0:
            error_code += 1
            cv2.circle(img0, (xy), 65, (0, 0, 255), 20)
        for xy in xy_1:
            error_code += 1
            cv2.circle(img1, (xy), 65, (0, 0, 255), 20)
        if len(xy_0) > 0 or len(xy_1) > 0:
            error_msg.append("・丸で囲われた設定をOFFにしてください。")
        await channel.send("setting check: finish")
        # 結果通知
        files = []
        if error_code == 0:
            color = 0x00ff00
            description = "問題なし\n\n🙇‍♂️ご協力ありがとうございました！🙇‍♂️\n※以下のエラーログの内容にかかわらず、提出内容に問題はありません。ご安心ください。\n"
        else:
            color = 0xff0000
            description = "以下の問題が見つかりました。\n"
            cv2.imwrite(file_names[0], img0)
            files.append(discord.File(file_names[0]))
            cv2.imwrite(file_names[1], img1)
            files.append(discord.File(file_names[1]))
        embed = discord.Embed(
            title="分析結果", description=description, color=color)
        value = "なし"
        if len(error_msg) > 0:
            error_msg = str(error_msg)[1:-1]
            error_msg = error_msg.replace(',', '\n')
            value = '\n' + error_msg.replace('\'', '')
        embed.add_field(name="エラーログ", value=value, inline=False)
        await channel.send(content=f"{message.author.mention}", embed=embed, files=files)
        return

client.run("OTUyOTYyOTAyMzI1ODg2OTg2.Yi9p3Q.bisIxDqKOMlESDLe1GBnvNseOBQ")
