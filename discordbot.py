import discord
intents = discord.Intents.all()  # デフォルトのIntentsオブジェクトを生成
intents.typing = False  # typingを受け取らないように
client = discord.Client(intents=intents)
print("ビト森杯bot main: 起動完了")

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

client.run("OTUyOTYyOTAyMzI1ODg2OTg2.Yi9p3Q.bisIxDqKOMlESDLe1GBnvNseOBQ")
