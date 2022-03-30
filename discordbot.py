import shutil
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
print("ビト森杯bot-画像分析: 起動完了")
shutil.copyfile("tessdata/jpn.traineddata", "/app/vendor/tessdata/jpn.traineddata")

@client.event
async def on_message(message):
    if len(message.attachments) == 2 and message.channel.id == 952946795573571654:  # 画像提出
        # 初期設定
        try:
            channel = await message.channel.create_thread(name=f"{message.author.display_name} 分析ログ", message=message)
        except AttributeError:
            return
        embed = discord.Embed(title="分析中...", description="0% 完了")
        status = await channel.send(embed=embed)
    #    pyocr.tesseract.TESSERACT_CMD = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
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
                    notice = await channel.send(f"{message.author.mention}\nbotでの画像分析ができない画像のため、運営による手動チェックに切り替えます。\nしばらくお待ちください。\n\n{admin.mention}")
                    await notice.add_reaction("⭕")
                    await notice.add_reaction("❌")
                    return
                dt_now = datetime.now()
                name = "/tmp/" + dt_now.strftime("%H.%M.%S.png")  # "/tmp/" +
                await a.save(name)
                file_names.append(name)
                await sleep(1)
            else:
                await channel.send("Error: jpg, jpeg, png画像を投稿してください。")
                return
        embed = discord.Embed(title="分析中...", description="20% 完了")
        await status.edit(embed=embed)
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
        embed = discord.Embed(title="分析中...", description="40% 完了")
        await status.edit(embed=embed)
        # モバイルボイスオーバーレイ検出
        """for i in range(2):
            text_box1 = tool.image_to_string(Image.open(
                file_names[i]), lang=lang, builder=pyocr.builders.WordBoxBuilder(tesseract_layout=12))
            text_box2 = tool.image_to_string(Image.open(
                file_names[i]), lang=lang, builder=pyocr.builders.WordBoxBuilder(tesseract_layout=6))
            text_box_list = [text_box1, text_box2]
            for text_box in text_box_list:
                for texts in text_box:
                    print('setting check now')
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
                                    break"""
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
        embed = discord.Embed(title="分析中...", description="60% 完了")
        await status.edit(embed=embed)
        # ワード検出
        if "モバイルボイスオーバーレイ" in all_text:
            error_msg.append("・例外検知: モバイルボイスオーバーレイがオンになっている場合、正しい結果が出力されません。お手数ですが、オフにして再提出をお願いします。")
        if "troubleshooting" in all_text:
            await channel.send("word found: troubleshooting")
            notice = await channel.send(f"{message.author.mention}\nbotでの画像分析ができない画像のため、運営による手動チェックに切り替えます。\nしばらくお待ちください。\n\n{admin.mention}")
            await notice.add_reaction("⭕")
            await notice.add_reaction("❌")
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
        embed = discord.Embed(title="分析中...", description="80% 完了")
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
        embed = discord.Embed(title="分析中...", description="100% 完了")
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
            contact = client.get_channel(920620259810086922)  # お問い合わせ
            description = f"以下の問題が見つかりました。\n内容に誤りがあると思われる場合、お手数ですが{contact.mention}までご連絡ください。\n\n"
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
