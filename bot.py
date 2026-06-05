import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
from datetime import datetime, timedelta, timezone
import os
import random
from flask import Flask
from threading import Thread
import traceback
import asyncio




# ======================================
# メッセージ受信
# ======================================




intents = discord.Intents.default()

intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is running"

def run_web():
    app.run(host="0.0.0.0", port=10000)

def keep_alive():
    t = Thread(target=run_web)
    t.start()
tree = bot.tree

@tree.command(name="ms", description="メッセージ送信")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    target_channel="送信先",
    message="送信内容",
    user="メンションユーザー",
    role="メンションロール"
)
async def ms(
    interaction: discord.Interaction,
    target_channel: discord.TextChannel | discord.Thread,
    message: str,
    user: discord.Member = None,
    role: discord.Role = None
):

    parts = []

    # ユーザーメンション
    if user:
        parts.append(user.mention)

    # ロールメンション
    if role:
        parts.append(role.mention)

    # 本文
    message = message.replace("\\n", "\n")
    parts.append(message)
    
    send_text = "\n".join(parts)
    
    await target_channel.send(
        send_text,
        allowed_mentions=discord.AllowedMentions(
            everyone=True,
            roles=True,
            users=True
        )
    )

    await interaction.response.send_message(
        "送信しましたえ。",
        ephemeral=True
    )

BACKUP_CHANNEL_ID = 1490323490601959554


JOB_CONFIG = {
    "🛒業務：シグなる": {
        "channel_id": 1503009789901541376,
        "user_id": 1369075224426844202
    },

    "🛒業務：くらげ": {
        "channel_id": 1503014097317396600,
        "user_id": 1109819930246918225
    },
    
    "🛒業務：海": {
        "channel_id": 1503014172282065020,
        "user_id": 431434357085962240
    },
    
    "🛒業務：そうた": {
        "channel_id": 1503014230872293516,
        "user_id": 1094592548208656474
    },
    
    "🛒業務：眠斗": {
        "channel_id": 1503009358936805446,
        "user_id": 800345977864192031
    },
    
    "🛒業務：アップル": {
        "channel_id": 1503014297033511005,
        "user_id": 713999033835847680
    },
    
    "🛒業務：ピンキー": {
        "channel_id": 1503014470849531964,
        "user_id": 1016648308934066238
    },
    
    "🛒業務：いろは": {
        "channel_id": 1503014564709531771,
        "user_id": 1116671861267365949
    },
    
    "🛒業務：鏡花": {
        "channel_id": 1503014658544505024,
        "user_id": 646666452916633621
    },
    
    "🛒業務：はる": {
        "channel_id": 1503014717768204429,
        "user_id": 890903179577921536
    },
    
    "🛒業務：四ノ宮": {
        "channel_id": 1503014780250751107,
        "user_id": 627113213313417216
    },
    
    "🛒業務：しまかぜ": {
        "channel_id": 1503014984328810508,
        "user_id": 1122462469659578398
    },
    
    "🛒業務：ららららい": {
        "channel_id": 1507722681951453346,
        "user_id": 604640387042115605
    },
    
    "🛒業務：欠員": {
        "channel_id": 1503014919707299980,
        "user_id": 1369075224426844202
    },
}


# ------------------------
# JST
# ------------------------
JST = timezone(timedelta(hours=9))

# ------------------------
# データ
# ------------------------
def load_data():
    try:
        with open("data.json","r",encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_data(new_data):

    global data
    global backup_needed

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)

    # 保存後に再読込
    data = load_data()

    # バックアップ予約
    backup_needed = True


data = load_data()

backup_needed = False
last_backup_time = None


if "_global" not in data:
    data["_global"] = {}

if "shop_profit" not in data["_global"]:
    data["_global"]["shop_profit"] = 0

def init_user(user):
    uid=str(user.id)
    if uid not in data:
        data[uid]={}

    data[uid]["name"] = user.display_name

    defaults={
        "name":user.display_name,
        "is_working":False,
        "start_time":None,
        "total_time":0,
        "history":[],
        "pay":0,

        # ★追加
        "sales":0,        # ←未受取売上
        "total_sales":0,  # ←総売上

        "items":{},

        "ai_memory": [],
        "profile": {}
    }

    for k,v in defaults.items():
        if k not in data[uid]:
            data[uid][k]=v

def yen(n):
    return f"{int(n):,}円"

async def send_backup():

    global last_backup_time
    global backup_needed

    try:

        channel = bot.get_channel(BACKUP_CHANNEL_ID)

        if not channel:
            print("バックアップch取得失敗")
            return

        now = datetime.now(JST)

        filename = (
            f"【決算データバックアップ】"
            f"{now.strftime('%m月%d日%H時%M分')}.json"
        )

        await channel.send(
            content=(
                f"📦 データバックアップ\n"
                f"{now.strftime('%m.%d.%H:%M')}"
            ),
            file=discord.File(
                "data.json",
                filename=filename
            )
        )

        last_backup_time = now
        backup_needed = False

        print("バックアップ送信完了")

    except Exception as e:
        print("バックアップ失敗:", e)

async def refresh_job_panel(member_id):

    uid = str(member_id)

    panel = job_panels.get(uid)
    if not panel:
        return

    try:
        channel = bot.get_channel(panel["channel_id"])
        if not channel:
            return

        msg = await channel.fetch_message(panel["message_id"])

        member = await bot.fetch_user(int(uid))  # 安定取得

        view = JobView(member)

        await msg.edit(embed=view.build_embed(), view=view)

    except Exception as e:
        print("JOB更新失敗:", uid, e)
        
async def refresh_all_panels():

    global panel_messages

    remove_list = []

    for panel in panel_messages:

        try:
            channel = bot.get_channel(panel["channel_id"])

            if not channel:
                continue

            msg = await channel.fetch_message(panel["message_id"])

            await msg.edit(
                embed=work_view.embed(),
                view=work_view
            )

        except Exception as e:
            print("勤務パネル更新失敗:", e)
            remove_list.append(panel)

    for r in remove_list:
        if r in panel_messages:
            panel_messages.remove(r)

    save_panels()
# ------------------------
# 京都ねぎらい
# ------------------------
def get_kyoto_message(seconds):
    minutes = seconds // 60

    if minutes < 60:
        msgs = [
            "あらあら、そないな短さでお仕事言わはるん？笑わせんといておくれやす。",
            "それで働いたつもりでいてはるんどす？うちは認められへんわぁ。",
            "そないな時間で退勤やなんて、えらい気楽なお仕事どすなぁ。",
            "それ、出勤言うんやったら世の中ゆるすぎますえ？",
            "ちょっと席温めただけやのに、よう退勤押せましたなぁ。",
            "あんさんの中ではこれで働いたことになるんどす？不思議やわぁ。",
            "そら記録にも残したらあきませんえ、恥ずかしいさかい。",
            "ほんのご挨拶程度の出勤どしたなぁ、かわいらしいこと。",
            "それで給料出る思うてはるんやったら、だいぶおめでたいどすなぁ。",
            "まぁ…次はもうちょっと“お仕事”してから押しとくれやす。"
        ]

    elif 60 <= minutes <= 70:
        msgs = [
            "義務だけはちゃんと果たしはったんやねぇ、それだけはえらいどすなぁ。",
            "最低限だけやって帰らはるん、ほんま要領よろしおすなぁ。",
            "きっちり義務時間、抜かりあらしまへんなぁ。",
            "それ以上は働かへんいう強い意志、見習いたいくらいやわぁ。",
            "まぁ決まりだけ守っとけば文句言われへんもんなぁ、賢いこと。",
            "あえてそれ以上はやらへんの、なかなかしたたかどすなぁ。",
            "義務ピッタリで帰るん、逆に感心してしまいますえ。",
            "その“ギリギリ精神”、よう貫いてはるわぁ。",
            "必要以上はせぇへん、ええスタイル持ってはりますなぁ。",
            "ほんま、損せぇへん働き方、ようご存じどすなぁ。",
            "義務やんなぁ"
        ]

    elif 70 < minutes < 110:
        msgs = [
            "ちょっとだけ頑張らはったんやねぇ、その中途半端さがまたよろしおすなぁ。",
            "義務よりちょい上、なんとも言えへん働きぶりどすなぁ。",
            "あとちょっと頑張ればええのに、そこ止まりなんがあんさんらしいわぁ。",
            "中途半端にようやらはりましたなぁ、ほんま絶妙どす。",
            "その微妙な頑張り、評価に困りますわぁ。",
            "頑張ったんかサボったんか、よう分からんええラインどすなぁ。",
            "なんとも言えへん時間やけど…まぁお疲れさんどす。",
            "そこまで来たらもうちょい行けたんと違います？ふふ。",
            "ええとこで止めはりましたなぁ、計算してはるんやろか。",
            "まぁ…“ちょっと頑張った感”は出てますえ。"
        ]

    elif 110 <= minutes < 120:
        msgs = [
            "まぁ、落ち着いたええ働き方どしたなぁ。",
            "無理せんと、自分のペース守ってはるんやねぇ。",
            "安定してはりますなぁ、いつも通りいう感じで。",
            "ほどよいところで収めはるん、上手いことしはりますなぁ。",
            "力入れすぎへんの、あんさんらしくてよろしおすなぁ。",
            "ええ感じに働かはりましたなぁ、ぼちぼちはやるんやねぇ。",
            "きっちりしすぎへん感じ、余裕あってええどすなぁ。",
            "そこそこ頑張ったんと違います？認めときますわぁ。",
            "まぁ、ええ塩梅いうところどすやろか。",
            "肩の力抜いてはるん、見てて安心しますえ。",
        ]

    elif 120 <= minutes < 180:
        msgs =[
            "ようここまできっちりやらはりましたなぁ、見ていて安心できる働きぶりどしたえ。",
            "しっかりと役目果たしてはりますやん、ほんまに立派なお働きぶりどすなぁ。",
            "長い時間こなしてはって、ええ仕事してはりますなぁ、お疲れさまどす。",
            "ここまで任せて大丈夫や思えるお人は、なかなかおりまへんえ、頼もしいことどす。",
            "気ぃ抜かんとようやらはりましたなぁ、その姿勢、感心させてもろてますえ。",
            "見ていて気持ちのええ働き方で、周りにもええ影響、広がっていきますやろなぁ",
            "崩れんと最後までようやってはりましたなぁ、見てて安心どしたえ。",
            "淡々とやってはるけど、その安定した働きぶり、なかなか出来るもんやありまへんえ。",
            "こうしてしっかり積み重ねてはるのが、よう伝わってきますなぁ。",
            "無駄のない動きでよう働いてはりますなぁ、見ていて安心できるお人どす。"
        ]

    else:
        msgs = [
            "ほんまによう頑張らはりましたなぁ、そのお働きぶりには思わず頭が下がりますえ、ここまできっちりやらはる方はなかなかおりまへん。",
            "ここまでしっかり立って売り続けはるなんて、並大抵のことやあらしまへん、その安定した姿勢に感服いたしますえ。",
            "あんさんにはほんま頭上がりまへんわぁ、任された場を崩さず守り通してはるあたり、見事としか言いようがあらしまへん。",
            "これほどまでにきっちり務めてくれはるなんて、ありがたいことどす、その姿だけで場が締まりますえ。",
            "無駄のない動きでしっかり売ってはる様子、ほんま見事どした、誇ってよろしおすと言いたなる出来どす。",
            "ほんま立派なお人やわぁ、ここまで安定してやってくれはる方には感謝してもし足りまへんえ。",
            "ここまで崩れずにやり続けてくれる人、そうそうおりまへん、その一貫した働きぶりに感心しきりどす。",
            "目立たんようでいて、きっちり結果を出してはるその働き方、ほんまに見事で心打たれますえ。",
            "あんさんがおってくれて、どれだけ助かってることか、その場に立ってはるだけで安心感が違いますえ。",
            "ここまで隙なくやってはる働きぶり、まさに理想的どすなぁ、思わず見入ってしまうほどの出来どした。"
        ]

    return random.choice(msgs)

# ------------------------
# UTC→JST変換関数
# ------------------------
def to_jst(dt):
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(JST)

# ------------------------
# ★過去データ補正
# ------------------------
def fix_to_jst():
    changed = False

    for uid, u in data.items():
        st = u.get("start_time")
        if st:
            try:
                dt = to_jst(datetime.fromisoformat(st))
                u["start_time"] = dt.isoformat()
                changed = True
            except:
                pass

        for h in u.get("history", []):
            for key in ["start", "end"]:
                t = h.get(key)
                if t:
                    try:
                        dt = to_jst(datetime.fromisoformat(t))
                        h[key] = dt.isoformat()
                        changed = True
                    except:
                        pass

    if changed:
        save_data(data)

# ------------------------
# ステータス更新
# ------------------------
def get_working_count():
    return sum(1 for u in data.values() if u.get("is_working"))

@tasks.loop(minutes=1)
async def auto_backup():

    global last_backup_time
    global backup_needed

    now = datetime.now(JST)

    # 初回起動時
    if last_backup_time is None:
        await send_backup()
        return

    diff = (now - last_backup_time).total_seconds()

    # 1時間経過 or データ更新
    if diff >= 3600 or backup_needed:
        await send_backup()


@tasks.loop(seconds=15)

async def update_status():
    count = get_working_count()

    if count > 0:
        await bot.change_presence(
            status=discord.Status.online,
            activity=discord.Game(f"開店中({count}人)")
        )
    else:
        await bot.change_presence(
            status=discord.Status.idle,
            activity=discord.Game("閉店中")
        )

async def update(self, interaction):
    text = "【注文中】\n"

    for k, v in self.cart.items():
        text += f"{k} ×{v}\n"

    text += f"\n💰合計：{yen(self.calc_total())}"

    try:
        await interaction.message.edit(
            content=text,
            view=self   # ← ここ重要（再生成禁止）
        )
    except:
        await interaction.response.edit_message(
            content=text,
            view=self
        )
# ------------------------
# メニュー（そのまま）
# ------------------------
MENU = {}
def build_status(self):
    text = "【現在の条件】\n"

    for k, v in self.filters.items():
        if v is None:
            continue

        if v is True:
            v = "あり"
        elif v is False:
            v = "なし"

        text += f"{k}: {v}\n"

    if text == "【現在の条件】\n":
        text += "なし"

    return text
# ------------------------
# 効能付きメニュー（検索用）
# ------------------------
SEARCH_MENU = {}
def format_effects(eff):
    text = ""
    for k, v in eff.items():
        if k in ["体力","アーマー","満腹","水分","ストレス"]:
            if v == 0:
                continue
        if k == "移動上昇":
            v = "有" if v else "無"
        text += f"{k}:{v} "
    return text.strip()

def search_items(filters, strict=False):
    results = []

    for shop, items in SEARCH_MENU.items():
        for name, eff in items.items():

            ok = True

            # 店舗名
            if filters.get("shop"):
                if filters["shop"] not in shop:
                    continue

            # 商品名
            if filters.get("name"):
                if filters["name"] not in name:
                    continue

            # 数値系チェック
            for key in ["体力","アーマー","満腹","水分","ストレス"]:
                val = eff.get(key, 0)

                # UI検索（「あり」）
                if filters.get(key) is True:
                    if val == 0:
                        ok = False
                        break

                # strict検索（完全一致）
                elif strict and key in filters:
                    if val != filters[key]:
                        ok = False
                        break

                # 通常検索（0は除外）
                if not strict and key in filters:
                    if val == 0:
                        ok = False
                        break

            if not ok:
                continue

            if "金額" in filters:
                if eff.get("金額") != filters["金額"]:
                    continue

            # 使用速度
            if filters.get("使用速度"):
                if eff.get("使用速度") != filters["使用速度"]:
                    continue

            # 移動上昇
            if filters.get("移動上昇") is not None:
                if eff.get("移動上昇") != filters["移動上昇"]:
                    continue

            results.append((shop, name, eff))

    return results

CATEGORY_LIST=list(MENU.items())

def split_menu(page):
    return dict(CATEGORY_LIST[:4] if page==0 else CATEGORY_LIST[4:])

# ------------------------
# 注文UI
# ------------------------
class AmountModal(discord.ui.Modal):
    def __init__(self, view, item):
        super().__init__(title=f"{item} 数量")
        self.view_ref = view
        self.item = item

        self.amount = discord.ui.TextInput(label="数量", default="1")
        self.add_item(self.amount)

    async def on_submit(self, interaction):
        try:
            qty = int(self.amount.value)
            if qty <= 0:
                raise ValueError()
        except:
            await interaction.response.send_message("数字入れて", ephemeral=True)
            return

        self.view_ref.cart[self.item] = qty

        text = "【注文中】\n"
        for k, v in self.view_ref.cart.items():
            text += f"{k} ×{v}\n"

        text += f"\n💰合計：{yen(self.view_ref.calc_total())}"
        
        await interaction.response.edit_message(
            content=text,
            view=self.view_ref
        )
        

class CategorySelect(discord.ui.Select):
    def __init__(self, view, cat, items):
        options=[
            discord.SelectOption(label=k, description=yen(v["price"]))
            for k,v in items.items()
        ]
        super().__init__(placeholder=f"▼ {cat}", options=options)
        self.view_ref=view

    async def callback(self, interaction):
        await interaction.response.send_modal(
            AmountModal(self.view_ref, self.values[0])
        )

class RemoveButton(discord.ui.Button):
    def __init__(self, item, view):
        super().__init__(label=f"❌ {item}", style=discord.ButtonStyle.danger)
        self.item=item
        self.view_ref=view

    async def callback(self, interaction):
        self.view_ref.cart.pop(self.item,None)
        await self.view_ref.update(interaction)

class OrderView(discord.ui.View):
    def __init__(self, page=0, cart=None):
        super().__init__(timeout=None)
        self.page=page
        self.cart=cart or {}

        for cat, items in split_menu(page).items():
            self.add_item(CategorySelect(self,cat,items))

        for i,item in enumerate(self.cart.keys()):
            if i>=3: break
            self.add_item(RemoveButton(item,self))

        if page>0:
            self.add_item(discord.ui.Button(label="←戻る",style=discord.ButtonStyle.secondary,custom_id="prev"))

        if page<1:
            self.add_item(discord.ui.Button(label="次へ→",style=discord.ButtonStyle.secondary,custom_id="next"))

        self.add_item(discord.ui.Button(label="確定",style=discord.ButtonStyle.success,custom_id="confirm"))

    def calc_total(self):
        total=0
        for cat in MENU:
            for item,qty in self.cart.items():
                if item in MENU[cat]:
                    total+=MENU[cat][item]["price"]*qty
        return total

    async def update(self, interaction):
        text = "【注文中】\n"
        
        for k, v in self.cart.items():
            text += f"{k} ×{v}\n"
            
        text += f"\n💰合計：{yen(self.calc_total())}"

        # Modal対策（ここが重要）
        try:
            await interaction.response.edit_message(
                content=text,
                view=OrderView(self.page, self.cart)
            )
        except:
            await interaction.message.edit(
                content=text,
                view=OrderView(self.page, self.cart)
            )

    async def interaction_check(self,interaction):
        cid=interaction.data.get("custom_id")

        if cid=="next":
            await interaction.response.edit_message(view=OrderView(1,self.cart))
            return False

        if cid=="prev":
            await interaction.response.edit_message(view=OrderView(0,self.cart))
            return False

        if cid=="confirm":
            await interaction.response.defer(ephemeral=True)

            uid=str(interaction.user.id)
            init_user(interaction.user)

            total=0
            cost=0
            worker=0
            text=""
           
            now = datetime.now(JST)
            day = now.strftime("%Y-%m-%d")
            
            
            for cat in MENU:
                for item,qty in self.cart.items():
                    if item in MENU[cat]:
                        d=MENU[cat][item]
                        
                        total += d["price"] * qty
                        cost  += d["cost"] * qty
                        
                        profit_raw = (d["price"] - d["cost"]) * qty
                        worker += int((d["price"] - d["cost"]) * 0.6) * qty
                        
                        text += f"{item} ×{qty}\n"
                        
                        # ★移動販売ログ（商品別）
                        if d.get("mobile"):
                            if "mobile_log" not in data[uid]:
                                data[uid]["mobile_log"] = {}
                                
                            if day not in data[uid]["mobile_log"]:
                                data[uid]["mobile_log"][day] = {}
                                
                            if item not in data[uid]["mobile_log"][day]:
                                data[uid]["mobile_log"][day][item] = {
                                    "qty":0,
                                    "sales":0
                                    }
                                    
                            data[uid]["mobile_log"][day][item]["qty"] += qty
                            data[uid]["mobile_log"][day][item]["sales"] += profit_raw


            profit=total-cost-worker

            data["_global"]["shop_profit"] += profit

            data[uid]["sales"] += (total-cost)        # 未受取
            data[uid]["total_sales"] += (total-cost)  # 総売上
            data[uid]["pay"] += worker

            for item,qty in self.cart.items():
                data[uid]["items"][item]=data[uid]["items"].get(item,0)+qty

            save_data(data)

            await refresh_job_panel(interaction.user.id)

            ch=discord.utils.get(interaction.guild.text_channels,name="💹売上報告")
            if ch:
                await ch.send(
                    f"```\n📊売上報告\n販売者:{interaction.user.display_name}\n{text}\n"
                    f"請求:{yen(total)}\n原価:{yen(cost)}\n利益:{yen(profit)}\n給料:{yen(worker)}\n```"
                )

            self.cart={}

            await interaction.edit_original_response(
                content="✅ 注文を確定しました\n\n🛒 カートをリセットしました",
                view=OrderView(self.page,self.cart)
            )

            return False

        return True

# ------------------------
# 勤務UI
# ------------------------
class WorkView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def embed(self):
        working=[]
        for uid,u in data.items():
            if u.get("is_working"):
                name = u.get("name") or "不明"
                st = u.get("start_time")

                if st:
                    try:
                        t = to_jst(datetime.fromisoformat(st)).strftime("%H:%M")
                        working.append(f"{name}({t}~)")
                    except:
                        working.append(f"{name}(??:??~)")
                else:
                    working.append(f"{name}(??:??~)")

        return discord.Embed(
            title="📋勤務パネル",
            description="\n".join(working) if working else "出勤者なし"
        )

    @discord.ui.button(label="出勤", style=discord.ButtonStyle.success, custom_id="start")
    async def start(self, interaction, button):
        init_user(interaction.user)
        uid = str(interaction.user.id)
        now = datetime.now(timezone.utc).astimezone(JST)

        data[uid]["is_working"] = True
        data[uid]["start_time"] = now.isoformat()

        # 出勤履歴を即追加
        data[uid]["history"].append({
            "start": now.isoformat(),
            "end": None
        })

        save_data(data)

        # ★ jobパネル更新
        await refresh_job_panel(interaction.user.id)
        

        await interaction.response.defer()

        await refresh_all_panels()

        await interaction.edit_original_response(
            embed=self.embed(),
            view=self
        )

        await update_status()

    @discord.ui.button(label="退勤",style=discord.ButtonStyle.danger,custom_id="end")
    async def end(self,interaction,button):
        init_user(interaction.user)
        uid=str(interaction.user.id)

        start = to_jst(datetime.fromisoformat(data[uid]["start_time"]))
        now = datetime.now(timezone.utc).astimezone(JST)

        diff=(now-start).total_seconds()

        message = get_kyoto_message(diff)

        data[uid]["total_time"]+=diff
        if data[uid]["history"]:

           data[uid]["history"][-1]["end"] = now.isoformat()

        data[uid]["is_working"]=False
        data[uid]["start_time"]=None
        save_data(data)

        await refresh_job_panel(interaction.user.id)
        

        await interaction.response.defer()

        await refresh_all_panels()

        await interaction.edit_original_response(
            embed=self.embed(),
            view=self
        )

        await interaction.followup.send(
            message,
            ephemeral=True
        )

    @discord.ui.button(label="オーダー",style=discord.ButtonStyle.primary,custom_id="order")
    async def order(self,interaction,button):
        await interaction.response.send_message("注文👇",view=OrderView(),ephemeral=True)
    

# ------------------------
# コマンド
# ------------------------
work_view = None

PANEL_FILE = "panels.json"
def load_panels():
    try:
        with open(PANEL_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_panels():
    with open(PANEL_FILE, "w") as f:
        json.dump(panel_messages, f)

panel_messages = load_panels()

# job固定パネル保存
JOB_PANEL_FILE = "job_panels.json"

def load_job_panels():
    try:
        with open(JOB_PANEL_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_job_panels():
    with open(JOB_PANEL_FILE, "w") as f:
        json.dump(job_panels, f)

    print("保存完了")
    print(job_panels)

job_panels = load_job_panels()

# Bonus保存
pending_bonus = {}

# owner固定パネル
OWNER_FILE = "owner_panel.json"

def load_owner_panel():
    try:
        with open(OWNER_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_owner_panel(channel_id, message_id):
    with open(OWNER_FILE, "w") as f:
        json.dump({
            "channel_id": channel_id,
            "message_id": message_id
        }, f)

async def refresh_owner_panel():

    global data

    data = load_data()

    panel = load_owner_panel()

    if not panel:
        return

    try:
        channel = bot.get_channel(panel["channel_id"])

        if not channel:
            return

        msg = await channel.fetch_message(panel["message_id"])

        # ------------------------
        # 金額計算
        # ------------------------
        shop_profit = data.get("_global", {}).get("shop_profit", 0)

        total_pay = sum(
            u.get("pay", 0)
            for uid, u in data.items()
            if uid != "_global"
        )

        vault_total = shop_profit + total_pay

        embed = discord.Embed(
            color=0x2b2d31
        )

        embed.description = (
            f"🏦 **ジョブ金庫**\n"
            f"💰 ジョブ金庫残高\n"
            f"```yaml\n"
            f"${vault_total:,}\n"
            f"```\n"

            f"🧾 従業員給料\n"
            f"```yaml\n"
            f"${total_pay:,}\n"
            f"```\n"

            f"📈 店舗総利益\n"
            f"```yaml\n"
            f"${shop_profit:,}\n"
            f"```"
        )

        await msg.edit(
            embed=embed,
            view=OwnerRefreshView()
        )

    except Exception as e:
        print("OWNER更新失敗:", e)


@tasks.loop(seconds=15)
async def auto_refresh_panels():

    await refresh_owner_panel()
    await refresh_everything()
    

            
async def refresh_everything():

    # OWNER
    await refresh_owner_panel()

    # JOB（全員更新）
    for uid, panel in list(job_panels.items()):

        try:
            channel = bot.get_channel(panel["channel_id"])
            if not channel:
                continue

            msg = await channel.fetch_message(panel["message_id"])

            member = channel.guild.get_member(int(uid))
            if not member:
                continue

            view = JobView(member)

            await msg.edit(
                embed=view.build_embed(),
                view=view
            )

        except:
            continue

    # 勤務パネル
    await refresh_all_panels()

@tree.command(name="panel")
async def panel(interaction):

    await interaction.response.send_message(
        embed=work_view.embed(),
        view=work_view
    )

    msg = await interaction.original_response()

    panel_messages.append({
        "channel_id": msg.channel.id,
        "message_id": msg.id
    })
    
    save_panels()

# =========================
# 勤務パネル全削除→再生成
# =========================
    await delete_all_work_panels()

    for config in JOB_CONFIG.values():
        channel = bot.get_channel(config["channel_id"])
        if not channel:
            continue

        panel_msg = await channel.send(
            embed=work_view.embed(),
            view=work_view
        )

        panel_messages.append({
            "channel_id": channel.id,
            "message_id": panel_msg.id
        })
    save_panels()

@tree.command(name="time")
async def time(interaction, member:discord.Member):
    uid = str(member.id)
    u = data.get(uid, {})

    total = u.get("total_time", 0)
    h = int(total // 3600)
    m = int((total % 3600) // 60)

    history = u.get("history", [])

    text = f"⏱ {member.display_name}\n合計：{h}時間{m}分\n\n"

    if history:
        text += "【出退勤履歴】\n"
        for hst in history[-20:]:
            try:
                start = to_jst(datetime.fromisoformat(hst.get("start"))).strftime("%Y/%m/%d %H:%M")
                end = to_jst(datetime.fromisoformat(hst.get("end"))).strftime("%Y/%m/%d %H:%M")
                text += f"{start} → {end}\n"
            except:
                text += f"{hst.get('start','?')} → {hst.get('end','?')}\n"
    else:
        text += "履歴なし"

    await interaction.response.send_message(text, ephemeral=True)

@tree.command(name="paying")
async def paying(interaction,member:discord.Member):
    u=data.get(str(member.id),{})
    await interaction.response.send_message(
        f"給料:{yen(u.get('pay',0))}\n"
        f"売上:{yen(u.get('sales',0))}\n"
        f"総売上:{yen(u.get('total_sales',0))}",
        ephemeral=True
    )

@tree.command(name="payall")
async def payall(interaction):
    total = sum(u.get("pay",0) for u in data.values())
    await interaction.response.send_message(
        f"全員の給料合計：{yen(total)}",
        ephemeral=True
    )

@tree.command(name="profit")
async def profit(interaction):
    total = data.get("_global", {}).get("shop_profit", 0)

    await interaction.response.send_message(
        f"🏪店の利益：{yen(total)}",
        ephemeral=True
    )

@tree.command(name="mobilesales")
async def mobilesales(interaction):
    result = {}

    for u in data.values():
        for day, items in u.get("mobile_log", {}).items():

            if day not in result:
                result[day] = {}

            for item, log in items.items():
                if item not in result[day]:
                    result[day][item] = {"qty":0,"sales":0}

                result[day][item]["qty"] += log["qty"]
                result[day][item]["sales"] += log["sales"]

    text = "📦移動販売売上（商品別）\n\n"

    for day in sorted(result.keys()):
        text += f"【{day}】\n"

        total_qty = 0
        total_sales = 0

        for item, log in result[day].items():
            text += f"{item}：{log['qty']}個 / {yen(log['sales'])}\n"
            total_qty += log["qty"]
            total_sales += log["sales"]

        text += f"▶ 合計：{total_qty}個 / {yen(total_sales)}\n\n"

    await interaction.response.send_message(text, ephemeral=True)

@tree.command(name="edittime")
async def edittime(interaction,member:discord.Member,minutes:int):
    init_user(member)
    uid=str(member.id)
    data[uid]["total_time"]=max(0,data[uid]["total_time"]+minutes*60)
    save_data(data)
    await refresh_job_panel(member.id)
    await interaction.response.send_message("OK",ephemeral=True)

@tree.command(name="editpaying")
async def editpaying(interaction,member:discord.Member,target:str,amount:int):
    init_user(member)
    uid=str(member.id)

    if target=="給料":
        data[uid]["pay"] += amount   # ←max削除
    elif target=="売上":
        data[uid]["sales"] += amount  # ←max削除

    save_data(data)
    await refresh_job_panel(member.id)
    
    await interaction.response.send_message("OK",ephemeral=True)

@tree.command(name="editprofit")
async def editprofit(interaction, amount: int):
    data["_global"]["shop_profit"] += amount
    save_data(data)

    await interaction.response.send_message(
        f"OK（現在：{yen(data['_global']['shop_profit'])}）",
        ephemeral=True
    )

@tree.command(name="resettime")
async def resettime(interaction,member:discord.Member):
    init_user(member)
    uid=str(member.id)
    data[uid]["total_time"]=0
    data[uid]["history"]=[]
    save_data(data)
    await refresh_job_panel(member.id)
    await interaction.response.send_message("OK",ephemeral=True)

@tree.command(name="resetpaying")
async def resetpaying(interaction,member:discord.Member):
    init_user(member)
    uid=str(member.id)

    data[uid]["pay"]=0
    data[uid]["sales"]=0

    save_data(data)
    await refresh_job_panel(member.id)
    
    await interaction.response.send_message("OK",ephemeral=True)

@tree.command(name="backup")
async def backup(interaction):
    try:
        await interaction.response.send_message(
            "📦 バックアップファイル👇",
            file=discord.File("data.json"),
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(f"エラー: {e}", ephemeral=True)

@tree.command(name="buy")
async def buy(interaction):

    # ------------------------
    # 分類
    # ------------------------
    regular_cats = ["全日メニュー", "曜日限定メニュー", "チル限定メニュー","販売停止メニュー"]
    limited_cats = ["季節限定メニュー", "特別販売メニュー"]

    regular_items = {}
    limited_items = {}

    # ------------------------
    # 初期化
    # ------------------------
    for cat, items in MENU.items():
        for item, data_item in items.items():

            # 移動・イベント除外
            if data_item.get("mobile") or data_item.get("event"):
                continue

            if cat in regular_cats:
                regular_items[item] = 0
            elif cat in limited_cats:
                limited_items[item] = 0

    # ------------------------
    # 集計
    # ------------------------
    for u in data.values():
        for item, qty in u.get("items", {}).items():

            if item in regular_items:
                regular_items[item] += qty

            if item in limited_items:
                limited_items[item] += qty

    # ------------------------
    # ランキング生成関数
    # ------------------------
    def build_ranking(title, items_dict):
        ranking = sorted(items_dict.items(), key=lambda x: x[1], reverse=True)

        text = f"📊【{title}】\n\n"

        prev_qty = None
        rank = 0
        display_rank = 0

        for item, qty in ranking:
            rank += 1
            if qty != prev_qty:
                display_rank = rank
                prev_qty = qty

            text += f"{display_rank}位：{item} ×{qty}個\n"

        return text

    # ------------------------
    # 出力
    # ------------------------
    text = ""
    text += build_ranking("常設商品ランキング", regular_items)
    text += "\n"
    text += build_ranking("限定商品ランキング", limited_items)

    await interaction.response.send_message(text, ephemeral=True)


class SearchView(discord.ui.View):

    def __init__(self, page=0, filters=None):
        super().__init__(timeout=None)
        self.page = page
        self.filters = filters or {}

        if page == 0:
            self.add_item(self.make_select("体力", row=0))
            self.add_item(self.make_select("アーマー", row=1))
            self.add_item(self.make_select("満腹", row=2))
            self.add_item(self.make_select("水分", row=3))

            self.add_item(discord.ui.Button(label="次へ→", style=discord.ButtonStyle.secondary, custom_id="next"))

        else:
            self.add_item(self.make_select("ストレス", row=0))
            self.add_item(self.make_speed(row=1))
            self.add_item(self.make_move(row=2))

            self.add_item(discord.ui.Button(label="←戻る", style=discord.ButtonStyle.secondary, custom_id="prev"))

        self.add_item(discord.ui.Button(label="検索", style=discord.ButtonStyle.success, custom_id="search_btn"))
    def build_status(self):
        text = "【現在の条件】\n"

        if not self.filters:
            text += "なし"
            return text

        for k, v in self.filters.items():
            if v is None:
                continue

            if v is True:
                v = "あり"
            elif v is False:
                v = "なし"

            text += f"{k}: {v}\n"

        return text


    def make_select(self, key, row):
        select = discord.ui.Select(
            placeholder=key,
            options=[
                discord.SelectOption(label="指定なし"),
                discord.SelectOption(label="あり")
            ],
            row=row
        )

        async def callback(interaction):
            self.filters[key] = (select.values[0] == "あり")

            new_view = SearchView(self.page, self.filters)
            await interaction.response.edit_message(
                content=self.build_status(),   # ←追加
                view=new_view
            )

        select.callback = callback
        return select

    def make_speed(self, row):
        select = discord.ui.Select(
            placeholder="使用速度",
            options=[
                discord.SelectOption(label="普"),
                discord.SelectOption(label="早"),
                discord.SelectOption(label="遅")
            ],
            row=row
        )

        async def callback(interaction):
            self.filters["使用速度"] = select.values[0]
            await interaction.response.edit_message(
                content=self.build_status(),
                view=SearchView(self.page, self.filters),
            )

        select.callback = callback
        return select

    def make_move(self, row):
        select = discord.ui.Select(
            placeholder="移動上昇",
            options=[
                discord.SelectOption(label="有"),
                discord.SelectOption(label="無")
            ],
            row=row
        )

        async def callback(interaction):
            self.filters["移動上昇"] = (select.values[0] == "有")
            await interaction.response.edit_message(
                content=self.build_status(),
                view=SearchView(self.page, self.filters)
            )

        select.callback = callback
        return select

    async def interaction_check(self, interaction):
        cid = interaction.data.get("custom_id")

        if cid == "next":
            await interaction.response.edit_message(view=SearchView(1, self.filters))
            return False

        if cid == "prev":
            await interaction.response.edit_message(view=SearchView(0, self.filters))
            return False

        if cid == "search_btn":
            await interaction.response.defer(ephemeral=True)

            filters = dict(self.filters)
            results = search_items(filters)
            
            new_view = SearchView(page=0, filters={})
            
            await interaction.edit_original_response(
                content=new_view.build_status(),
                view=new_view
            )
            
            self.filters.clear()
            
            if not results:
                await interaction.followup.send("該当なし", ephemeral=True)
                return False
                
            embeds = []
            
            for shop, name, eff in results:
                embed = discord.Embed(title=f"◆【{shop}】{name}")
                
                text = ""
                # ★金額
                if eff.get("金額") is not None:
                    text += f"金額：{yen(eff.get('金額'))}\n"

                # 数値系（ループ）
                for key in ["体力", "アーマー", "満腹", "水分", "ストレス"]:
                    val = eff.get(key, 0)
                    if val != 0:
                        text += f"{key}：{val}\n"

                # 使用速度（外）
                if eff.get("使用速度"):
                    text += f"使用速度：{eff.get('使用速度')}\n"

                # 移動上昇（外）
                if eff.get("移動上昇") is not None:
                    text += f"移動上昇：{'有' if eff.get('移動上昇') else '無'}\n"
                    
                embed.description = text if text else "効果なし"
                embeds.append(embed)

            for i in range(0, len(embeds), 10):
                await interaction.followup.send(
                    content=f"{i//10+1}ページ目",
                    embeds=embeds[i:i+10],
                    ephemeral=True
                )

            return False

        return True




@tree.command(name="searchmenu1") 
async def searchmenu1(interaction):
    await interaction.response.send_message( 
        "条件を選択して確定", 
        view=SearchView(), 
        ephemeral=True 
    )
        
@tree.command(name="searchmenu2")
async def searchmenu2(
    interaction,
    店舗名: str = None,
    商品名: str = None,
    金額: int = None,
    体力: int = None,
    アーマー: int = None,
    満腹: int = None,
    水分: int = None,
    ストレス: int = None,
    使用速度: str = None,
    移動上昇: str = None
):

    filters = {}

    if 店舗名:
        filters["shop"] = 店舗名
    if 商品名:
        filters["name"] = 商品名
    if 金額 is not None:
        filters["金額"] = 金額

    for key, val in {
        "体力": 体力,
        "アーマー": アーマー,
        "満腹": 満腹,
        "水分": 水分,
        "ストレス": ストレス
    }.items():
        if val is not None:
            filters[key] = val

    if 使用速度:
        filters["使用速度"] = 使用速度

    if 移動上昇:
        filters["移動上昇"] = True if 移動上昇 == "有" else False

    results = search_items(filters, strict=True)

    if not results:
        await interaction.response.send_message("該当なし", ephemeral=True)
        return

    embeds = []
    
    for shop, name, eff in results:
        embed = discord.Embed(
            title=f"◆【{shop}】{name}",
            color=0x2b2d31
        )
        
        text = ""

        # ★金額
        if eff.get("金額") is not None:
            text += f"金額：{yen(eff.get('金額'))}\n"

        # ------------------------
        # 数値系（1回だけ）
        # ------------------------
        for key in ["体力", "アーマー", "満腹", "水分", "ストレス"]:
            val = eff.get(key, 0)
            if val != 0:
                text += f"{key}：{val}\n"

        # ------------------------
        # 使用速度（1回だけ）
        # ------------------------
        speed = eff.get("使用速度")
        if speed:
            text += f"使用速度：{speed}\n"

        # ------------------------
        # 移動上昇（1回だけ）
        # ------------------------
        move = eff.get("移動上昇")
        if move is not None:
            if move in [True, "True", "true", 1]:
                text += "移動上昇：有\n"
            else:
                text += "移動上昇：無\n"

        # ------------------------
        # 最終セット
        # ------------------------
        embed.description = text if text else "効果なし"
        embeds.append(embed)

    # embeds が空なら終了
    if not embeds:
        if not interaction.response.is_done():
            await interaction.response.send_message("結果が見つかりませんでした", ephemeral=True)
        else:
            await interaction.followup.send("結果が見つかりませんでした", ephemeral=True)
        return

    total = len(embeds)
    max_page = (total - 1) // 10 + 1

    # --- 最初の1回だけ response ---
    first_chunk = embeds[:10]
    
    if not interaction.response.is_done():
        await interaction.response.send_message(
            content=f"検索結果 1/{max_page}",
            embeds=first_chunk,
            ephemeral=True
        )
    else:
        await interaction.followup.send(
            content=f"検索結果 1/{max_page}",
            embeds=first_chunk,
            ephemeral=True
        )

    # --- 残りは followup ---
    for i in range(10, total, 10):
        chunk = embeds[i:i+10]
        page = i // 10 + 1
        
        await interaction.followup.send(
            content=f"検索結果 {page}/{max_page}",
            embeds=chunk,
            ephemeral=True
        )

@tree.command(name="open")
async def open_status(interaction: discord.Interaction):

    now = datetime.now(JST)

    # 7日分
    start_day = (now - timedelta(days=6)).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    # =========================
    # 全勤務データ取得
    # =========================
    works = []

    for uid, u in data.items():

        for h in u.get("history", []):

            try:
                st = to_jst(datetime.fromisoformat(h["start"]))
                en = to_jst(datetime.fromisoformat(h["end"]))
            except:
                continue

            # 範囲外
            if en < start_day:
                continue

            works.append((st, en))

    if not works:
        await interaction.response.send_message(
            "データなし",
            ephemeral=True
        )
        return

    # =========================
    # 日別ログ
    # =========================
    embeds = []

    for i in range(7):

        day_start = start_day + timedelta(days=i)
        day_end = day_start + timedelta(days=1)

        # -------------------------
        # イベント生成
        # -------------------------
        events = []

        for st, en in works:

            # 日跨ぎ対応
            s = max(st, day_start)
            e = min(en, day_end)

            if s >= e:
                continue

            # 開店
            events.append((s, +1))

            # 閉店
            events.append((e, -1))

        # -------------------------
        # ソート
        # 同時刻なら閉店を先
        # -------------------------
        events.sort(key=lambda x: (x[0], x[1]))

        text = ""

        active = 0
        segment_start = day_start

        # =========================
        # 状態遷移
        # =========================
        for t, diff in events:

            prev = active
            active += diff

            # -------------------------
            # 閉店 → 開店
            # -------------------------
            if prev == 0 and active > 0:

                if segment_start < t:

                    end_str = (
                        "00:00"
                        if t == day_end
                        else t.strftime("%H:%M")
                    )

                    text += (
                        f"🔴 【閉店】 "
                        f"{segment_start.strftime('%H:%M')}～"
                        f"{end_str}\n"
                    )

                segment_start = t

            # -------------------------
            # 開店 → 閉店
            # -------------------------
            elif prev > 0 and active == 0:

                end_str = (
                    "00:00"
                    if t == day_end
                    else t.strftime("%H:%M")
                )

                text += (
                    f"🟢 【開店】 "
                    f"{segment_start.strftime('%H:%M')}～"
                    f"{end_str}\n"
                )

                segment_start = t

        # =========================
        # 最後の区間
        # =========================

        # 営業中で終わった
        if active > 0:

            text += (
                f"🟢 【開店】 "
                f"{segment_start.strftime('%H:%M')}～"
            )

            # 今日以外は00:00まで表示
            if day_start.date() != now.date():
                text += "00:00"

            text += "\n"

        # 閉店状態で終わった
        else:

            if segment_start < day_end:

                text += (
                    f"🔴 【閉店】 "
                    f"{segment_start.strftime('%H:%M')}～"
                )

                # 今日以外
                if day_start.date() != now.date():
                    text += "00:00"

                text += "\n"

        # データなし防止
        if not text:
            text = "データなし"

        # =========================
        # Embed
        # =========================
        embed = discord.Embed(
            title=f"📊 開店ログ【{day_start.strftime('%m月%d日')}】",
            description=text,
            color=0x2b2d31
        )

        embeds.append(embed)

    # =========================
    # 送信
    # =========================
    await interaction.response.send_message(
        embeds=embeds,
        ephemeral=True
    )
@tree.command(name="owner")
async def owner(interaction: discord.Interaction):

    panel = load_owner_panel()

    # 既存確認
    if panel:

        try:
            channel = bot.get_channel(panel["channel_id"])

            if channel:
                await channel.fetch_message(panel["message_id"])

                await interaction.response.send_message(
                    "✅ OWNERパネルは既に存在します",
                    ephemeral=True
                )
                return

        except:
            pass

    embed = discord.Embed(
        description="読み込み中...",
        color=0x2b2d31
    )

    await interaction.response.send_message(
        embed=embed,
        view=OwnerRefreshView()
    )

    msg = await interaction.original_response()

    save_owner_panel(
        msg.channel.id,
        msg.id
    )

    await refresh_owner_panel()

class OwnerRefreshView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🔄 更新",
        style=discord.ButtonStyle.primary,
        custom_id="owner_refresh"
        )

    async def refresh_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.defer()

        await refresh_everything()

        panel = load_owner_panel()

        channel = bot.get_channel(panel["channel_id"])
        msg = await channel.fetch_message(panel["message_id"])

        await interaction.edit_original_response(
            embed=msg.embeds[0],
            view=self
        )


class BonusView(discord.ui.View):

    def __init__(self, target_id, amount):
        super().__init__(timeout=None)

        self.target_id = str(target_id)
        self.amount = amount

    @discord.ui.button(
        label="💰 受け取る",
        style=discord.ButtonStyle.success,
        custom_id="bonus_receive"
    )
    async def receive_bonus(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        # 対象者以外禁止
        if str(interaction.user.id) != self.target_id:
            
            await interaction.response.send_message(
                "対象者専用です",
                ephemeral=True
            )
            return

        # ボタン無効化
        button.disabled = True

        try:
            await interaction.response.edit_message(view=self)
        except:
            return

        init_user(interaction.user)
 
        uid = str(interaction.user.id)

        # 給料反映
        data[uid]["pay"] += self.amount

        save_data(data)

        # 全更新
        await refresh_everything()

        # メッセージ削除
        try:
            await interaction.message.delete()
        except:
            pass

        # 完了
        try:
            await interaction.followup.send(
                f"✅ ボーナス {yen(self.amount)} を受け取りました",
                ephemeral=True
            )
        except:
            pass


class JobView(discord.ui.View):

    def __init__(self, member: discord.Member):
        super().__init__(timeout=None)
        self.member = member

    # ------------------------
    # パネル生成
    # ------------------------
    def build_embed(self):
        
        global data
        data = load_data()
        
        uid = str(self.member.id)
        
        u = data.get(uid, {})

        # 金額
        pay = u.get("pay", 0)
        sales = u.get("sales", 0)
        total_sales = u.get("total_sales", 0)

        # 勤務時間
        total = u.get("total_time", 0)

        h = int(total // 3600)
        m = int((total % 3600) // 60)

        # 履歴
        history_text = ""

        history = u.get("history", [])

        if history:

            for hst in history[-20:]:
                
                try:
                    # 出勤時間
                    start = to_jst(
                        datetime.fromisoformat(hst["start"])
                    ).strftime("%m/%d %H:%M")

                    # 退勤時間
                    if hst.get("end"):

                       end = to_jst(
                           datetime.fromisoformat(hst["end"])
                        
                       ).strftime("%m/%d %H:%M")

                    else:
                        end = "勤務中"

                    history_text += (
                        f"🟢 出勤：{start}\n"
                        f"🔴 退勤：{end}\n\n"
                    )

                except Exception as e:
                    print(e)

        else:
            history_text = "記録なし"

        # Embed
        embed = discord.Embed(
            color=0x2b2d31
        )

        embed.description = (
            f"# 👤 {self.member.display_name}\n\n"

            f"💰 給料\n"
            f"```yaml\n"
            f"${pay:,}\n"
            f"```\n"

            f"🧾 売上\n"
            f"```yaml\n"
            f"${sales:,}\n"
            f"```\n"

            f"📈 総売上\n"
            f"```yaml\n"
            f"${total_sales:,}\n"
            f"```\n"

            f"⏰ 合計出勤時間\n"
            f"```yaml\n"
            f"{h}時間{m}分\n"
            f"```\n"

            f"📋 出退勤記録\n"
            f"```yaml\n"
            f"{history_text}"
            f"```"
        )

        return embed

    # ------------------------
    # 売上リセット
    # ------------------------
    @discord.ui.button(
        label="売上リセット",
        style=discord.ButtonStyle.danger
    )
    async def reset_pay(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        uid = str(self.member.id)

        init_user(self.member)

        data[uid]["pay"] = 0
        data[uid]["sales"] = 0

        save_data(data)

        await interaction.response.edit_message(
            embed=self.build_embed(),
            view=self
        )

    # ------------------------
    # 出勤リセット
    # ------------------------
    @discord.ui.button(
        label="出勤リセット",
        style=discord.ButtonStyle.secondary
    )
    async def reset_time(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        uid = str(self.member.id)

        init_user(self.member)

        data[uid]["total_time"] = 0
        data[uid]["history"] = []

        save_data(data)

        await interaction.response.edit_message(
            embed=self.build_embed(),
            view=self
        )


# ------------------------
# JOB コマンド
# ------------------------
@tree.command(name="job")
async def job(interaction: discord.Interaction):

    await interaction.response.defer(ephemeral=True)

    created = 0
    updated = 0

    for cfg in JOB_CONFIG.values():

        user_id = str(cfg["user_id"])
        channel = bot.get_channel(cfg["channel_id"])
        if not channel:
            continue

        member = interaction.guild.get_member(int(user_id))
        if not member:
            continue

        init_user(member)
        view = JobView(member)

        panel = job_panels.get(user_id)

        # 既存パネルがある場合は更新
        if panel:
            try:
                msg = await channel.fetch_message(panel["message_id"])
                await msg.edit(embed=view.build_embed(), view=view)
                updated += 1
                continue
            except:
                pass  # 消えてたら新規作成へ

        # 新規作成
        msg = await channel.send(embed=view.build_embed(), view=view)

        job_panels[user_id] = {
            "channel_id": channel.id,
            "message_id": msg.id
        }

        created += 1

    save_job_panels()

    await interaction.followup.send(
        f"JOB更新完了：新規 {created} / 更新 {updated}",
        ephemeral=True
    )
async def clear_all_fixed_panels():

    for config in JOB_CONFIG.values():

        channel = bot.get_channel(config["channel_id"])
        if not channel:
            continue

        try:
            async for msg in channel.history(limit=200):

                if msg.author != bot.user:
                    continue

                # ボタン付き全部削除（JOBパネル）
                if msg.components:
                    await msg.delete()
                    continue

                # embed系も全部対象
                if msg.embeds:
                    await msg.delete()
                    continue

        except Exception as e:
            print("削除失敗:", e)

    job_panels.clear()
    panel_messages.clear()

    save_job_panels()
    save_panels()

async def delete_all_job_panels():
    global job_panels

    for uid, panel in list(job_panels.items()):
        try:
            channel = bot.get_channel(panel["channel_id"])
            if not channel:
                continue

            msg = await channel.fetch_message(panel["message_id"])
            await msg.delete()
        except:
            pass

    job_panels.clear()
    save_job_panels()


async def delete_all_work_panels():
    global panel_messages

    for panel in list(panel_messages):
        try:
            channel = bot.get_channel(panel["channel_id"])
            if not channel:
                continue

            msg = await channel.fetch_message(panel["message_id"])
            await msg.delete()
        except:
            pass

    panel_messages.clear()
    save_panels()    

async def roll_dice(interaction, sides):

    result = random.randint(1, sides)

    await interaction.response.send_message(
        f"🎲 1d{sides}\n結果: {result}"
    )


@tree.command(name="1d2")
async def dice_1d2(interaction: discord.Interaction):
    await roll_dice(interaction, 2)


@tree.command(name="1d5")
async def dice_1d5(interaction: discord.Interaction):
    await roll_dice(interaction, 5)


@tree.command(name="1d10")
async def dice_1d10(interaction: discord.Interaction):
    await roll_dice(interaction, 10)


@tree.command(name="1d15")
async def dice_1d15(interaction: discord.Interaction):
    await roll_dice(interaction, 15)


@tree.command(name="1d20")
async def dice_1d20(interaction: discord.Interaction):
    await roll_dice(interaction, 20)


@tree.command(name="1d100")
async def dice_1d100(interaction: discord.Interaction):
    await roll_dice(interaction, 100)

@tree.command(name="bonus")
async def bonus(
    interaction: discord.Interaction,
    対象者: discord.Member,
    金額: int,
    備考: str
):

    embed = discord.Embed(
        title="🎁 BONUS",
        color=0xf1c40f
    )

    embed.description = (
        f"👤 対象者\n"
        f"{対象者.mention}\n\n"

        f"💰 金額\n"
        f"```yaml\n"
        f"{yen(金額)}\n"
        f"```\n"

        f"📝 備考\n"
        f"```yaml\n"
        f"{備考}\n"
        f"```"
    )

    await interaction.response.send_message(
        embed=embed,
        view=BonusView(対象者.id, 金額)
    )

@tree.command(name="clearpanel")
async def clearpanel(interaction: discord.Interaction):

    await interaction.response.send_message("全パネル削除中...", ephemeral=True)

    await clear_all_fixed_panels()

    await interaction.followup.send("削除完了", ephemeral=True)

# ------------------------
# 起動
# ------------------------
@bot.event
async def on_ready():

    global work_view

    print("TEST ON READY")
    print("ログイン完了")

    fix_to_jst()

    work_view = WorkView()

    bot.add_view(work_view)
    bot.add_view(OwnerRefreshView())
    bot.add_view(BonusView(0,0))

    await tree.sync()
    await update_status()

    if not update_status.is_running():
        update_status.start()

    if not auto_refresh_panels.is_running():
        auto_refresh_panels.start()

    if not auto_backup.is_running():
        auto_backup.start()

    print("起動OK2")

    print("===== JOB PANELS =====")
    print(job_panels)
    print("=======================")

keep_alive()


#bot.run("MTQ4NzM2NjU4MTYxNjExNTgxMg.Ge7vBK.AR7pjVIe3J5zZeIhL5tg7E0bpTKVYZQja8YKhY")
bot.run(os.getenv("TOKEN"))
