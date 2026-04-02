import asyncio
import logging
import random
import re
import time
import contextlib
import urllib.request
import json as _json
from telethon import TelegramClient, events
from telethon import functions, types
from telethon.errors import RPCError, UserAdminInvalidError, ChatAdminRequiredError, UserNotParticipantError

API_ID = 0  # 替换为你的 Telegram API ID（从 https://my.telegram.org 获取）
API_HASH = "your_api_hash_here"  # 替换为你的 API Hash
SESSION = "/opt/tg-auto-heart/tg_hub"  # Session 文件路径，可自定义
TARGET_CHAT_ID = -100XXXXXXXXXX  # 替换为你的目标群组 ID（负数）

CONTROL_USER_IDS = {123456789}  # 替换为允许操作机器人的管理员 Telegram 用户 ID

KICK_TRIGGER_TEXTS = {",踢"}
UNMUTE_TRIGGER_TEXTS = {"解禁"}
UNBAN_TRIGGER_TEXTS = {"解除拉黑"}
PRAISE_TRIGGER_TEXTS = {"真棒"}
STATUS_TRIGGER_TEXTS = {"状态"}

DELETE_DELAY_SECONDS = 30
SUMMARY_DELETE_SECONDS = 60
AI_API_BASE = "https://your-ai-api-endpoint/anthropic"  # 替换为你的 AI API 地址
AI_API_KEY  = "your_ai_api_key_here"  # 替换为你的 AI API Key
AI_MODEL    = "claude-3-5-haiku-20241022"
SUMMARY_PATTERN = re.compile(r"^总结最近\s*(\d+)\s*条$")
MIN_TEMP_MUTE_SECONDS = 30
MAX_TEMP_MUTE_SECONDS = 366 * 24 * 3600
ADMIN_LOG_FALLBACK_LIMIT = 100

MUTE_FOREVER_PATTERN = re.compile(r"^禁言\s*(永久|永久禁言)$")
MUTE_PATTERN = re.compile(r"^禁言\s*(\d+)\s*(秒钟|秒|分钟|分|小时|时|天)$")
ID_COMMAND_PATTERN = re.compile(r"^(\d{5,})\s+(.+)$")
USERNAME_COMMAND_PATTERN = re.compile(r"^@([A-Za-z0-9_]{5,})\s+(.+)$")
UNIT_SECONDS = {"秒钟": 1, "秒": 1, "分钟": 60, "分": 60, "小时": 3600, "时": 3600, "天": 86400}

logging.basicConfig(level=logging.ERROR, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("tg-auto-heart")

PRAISE_TEMPLATES = [
    "{name}今天的表现太亮眼了，节奏稳、反应快，真的让人忍不住点赞。",
    "{name}这波发挥特别漂亮，思路清晰又有分寸，真的很让人佩服。",
    "{name}你一出手就很有水平，细节拿捏到位，气场都跟着稳起来了。",
    "{name}你的状态真的很好，做事干净利落，看着就让人特别舒服。",
    "{name}这次表现非常加分，判断准、执行快，妥妥是高光时刻。",
    "{name}你真的很会处理事情，既稳又准，难怪大家都会对你刮目相看。",
    "{name}今天这波操作太丝滑了，效率和效果都在线，确实很厉害。",
    "{name}你的能力很有说服力，不张扬但很能打，越看越觉得强。",
    "{name}这次真的被你秀到了，反应速度和执行力都属于优秀级别。",
    "{name}你身上那种稳稳拿下的感觉太强了，真的让人很有安全感。",
    "{name}你的表现让人眼前一亮，既有脑子也有行动力，真的很棒。",
    "{name}这次完成得相当漂亮，细节到位、节奏舒服，完全就是实力证明。",
    "{name}你真的很靠谱，关键时刻顶得上去，这种稳定感特别难得。",
    "{name}你这波太争气了，既有判断也有执行，想不夸你都很难。",
    "{name}看到{name}这次发挥，真的会觉得优秀的人就是会一直发光。",
    "{name}你的节奏感太好了，什么时候该出手、怎么出手都很有分寸。",
    "{name}这次真的做得很漂亮，不只是完成了，而且完成得很有质感。",
    "{name}你这种稳定又高效的状态，真的属于越看越让人欣赏的类型。",
    "{name}今天这份表现特别能打，思路成熟，动作也非常利落。",
    "{name}你总能把事情处理得很顺，能力在线不说，感觉也特别舒服。",
    "{name}这次的表现很高级，不浮夸但很有效，一看就是有实力的人。",
    "{name}你是真的优秀，关键时候的判断和执行都透着一种稳准狠。",
    "{name}这波拿捏得非常好，既聪明又沉着，真的让人很想给你鼓掌。",
    "{name}你的发挥非常出彩，节奏、判断、落点都让人觉得很专业。",
    "{name}今天的你真的太加分了，整个人都透着一种可靠又利落的感觉。",
    "{name}你这种从容又有实力的状态，真的特别容易让人产生信任感。",
    "{name}这次你表现得很惊艳，不抢戏却很关键，完全是高质量输出。",
    "{name}你做事真的很漂亮，既有效率又有细节，想不注意到都难。",
    "{name}今天你把优秀这件事表现得很具体，整个过程都很顺很稳。",
    "{name}你的能力感真的很强，一出手就知道是有东西的人。",
    "{name}这次发挥太稳了，思路在线、动作在线，结果也特别漂亮。",
    "{name}看到你的这波表现，真的会让人觉得你是又聪明又能做的人。",
    "{name}你真的很会拿结果，过程稳当，细节漂亮，让人很服气。",
    "{name}今天这份表现特别提气，既利落又可靠，真的很值得夸。",
    "{name}你的发挥很有质感，不只是完成任务，而是完成得特别漂亮。",
    "{name}这次你处理得特别好，判断准确，动作果断，真的很加分。",
    "{name}你这种稳中带强的感觉太好了，看似低调，实际非常能打。",
    "{name}今天你的表现真的很亮，既自然又高级，让人一眼就记住。",
    "{name}这波完全是实力发言，细节、节奏、结果都让人很满意。",
    "{name}你真的很值得被夸，能力强、状态稳，关键时刻还特别顶。",
    "{name}这次表现很漂亮，整套动作一气呵成，给人的感觉就是专业。",
    "{name}你今天真的超有存在感，而且是那种靠实力赢来的存在感。",
    "{name}你的节奏控制得太好了，稳稳推进，最后还特别漂亮地收住。",
    "{name}你这种又稳又强的发挥，真的很容易让人默默记住并欣赏。",
    "{name}这次做得非常漂亮，判断不拖泥带水，执行也特别有劲。",
    "{name}你一认真起来真的很强，那种靠谱和利落感太有魅力了。",
    "{name}这波表现完全值得高分，细节在线、气质在线、结果也在线。",
    "{name}今天必须夸夸{name}，状态好、手感热、发挥也是真的很顶。",
    "{name}你这种不声不响把事情做好的人，往往才最让人佩服。",
    "{name}这次真的是高质量发挥，整个人都散发着一种很强的稳定感。"
]

async def delete_later(client, message_id: int, delay_seconds: int = DELETE_DELAY_SECONDS):
    try:
        await asyncio.sleep(delay_seconds)
        await client.delete_messages(TARGET_CHAT_ID, message_id)
    except Exception:
        pass

async def send_temp_reply(client, reply_to_msg_id: int, text: str):
    try:
        sent = await client.send_message(entity=TARGET_CHAT_ID, message=text, reply_to=reply_to_msg_id)
        if sent and getattr(sent, "id", None):
            asyncio.create_task(delete_later(client, sent.id))
    except Exception:
        logger.exception("send_temp_reply_error")


def normalize_text(text: str) -> str:
    return (text or "").strip().replace(" ", "")


def parse_target_command(raw_text: str):
    stripped = (raw_text or "").strip()
    m = ID_COMMAND_PATTERN.match(stripped)
    if m:
        return {"type": "id", "value": int(m.group(1)), "command": normalize_text(m.group(2))}
    m = USERNAME_COMMAND_PATTERN.match(stripped)
    if m:
        return {"type": "username", "value": m.group(1), "command": normalize_text(m.group(2))}
    return None


def parse_mute_seconds(text: str):
    normalized = normalize_text(text)
    if MUTE_FOREVER_PATTERN.match(normalized):
        return 0
    m = MUTE_PATTERN.match(normalized)
    if not m:
        return None
    return int(m.group(1)) * UNIT_SECONDS[m.group(2)]


def format_duration_text(seconds: int) -> str:
    if seconds == 0:
        return "永久"
    if seconds % 86400 == 0:
        return f"{seconds // 86400}天"
    if seconds % 3600 == 0:
        return f"{seconds // 3600}小时"
    if seconds % 60 == 0:
        return f"{seconds // 60}分钟"
    return f"{seconds}秒"


def display_name_from_user(user) -> str:
    if not user:
        return "该用户"
    username = getattr(user, "username", None)
    if username:
        return f"@{username}"
    first_name = (getattr(user, "first_name", None) or "").strip()
    last_name = (getattr(user, "last_name", None) or "").strip()
    full_name = (first_name + " " + last_name).strip()
    if full_name:
        return full_name
    uid = getattr(user, "id", None)
    return f"用户{uid}" if uid else "该用户"


def explain_error(exc: Exception, target_name: str | None = None) -> str:
    prefix = f"{target_name} " if target_name else ""
    if isinstance(exc, UserAdminInvalidError):
        return f"❌ 操作失败：{prefix}无法处理管理员"
    if isinstance(exc, ChatAdminRequiredError):
        return "❌ 操作失败：机器人权限不足"
    if isinstance(exc, UserNotParticipantError):
        return f"❌ 操作失败：{prefix}不是群成员"
    if isinstance(exc, RPCError):
        name = exc.__class__.__name__
        if "Admin" in name:
            return f"❌ 操作失败：{prefix}权限不足或目标为管理员"
        if "Participant" in name or "UserNotParticipant" in name:
            return f"❌ 操作失败：{prefix}不是群成员"
        if "Banned" in name:
            return f"❌ 操作失败：{prefix}封禁状态异常"
        return f"❌ 操作失败：{name}"
    return f"❌ 操作失败：{exc.__class__.__name__}"


def build_praise_text(name: str) -> str:
    return f"✨ {random.choice(PRAISE_TEMPLATES).format(name=name)}"


async def resolve_target_from_reply(client, trigger_msg):
    reply = await trigger_msg.get_reply_message()
    if not reply or not getattr(reply, "sender_id", None):
        return None, None, None, None, None
    participant = await client.get_input_entity(reply.sender_id)
    channel = await client.get_input_entity(TARGET_CHAT_ID)
    user = await reply.get_sender()
    return reply.id, participant, channel, user, reply.sender_id


async def resolve_target_from_id(client, target_user_id: int):
    participant = await client.get_input_entity(target_user_id)
    channel = await client.get_input_entity(TARGET_CHAT_ID)
    user = await client.get_entity(target_user_id)
    return None, participant, channel, user, target_user_id


async def resolve_target_from_username(client, username: str):
    entity = await client.get_entity(username)
    participant = await client.get_input_entity(entity.id)
    channel = await client.get_input_entity(TARGET_CHAT_ID)
    return None, participant, channel, entity, entity.id


async def resolve_target_from_admin_log(client, target_user_id: int):
    channel = await client.get_input_entity(TARGET_CHAT_ID)
    async for entry in client.iter_admin_log(
        channel,
        limit=ADMIN_LOG_FALLBACK_LIMIT,
        join=True,
        leave=True,
        invite=True,
        restrict=True,
        unrestrict=True,
        ban=True,
        unban=True,
        promote=True,
        demote=True,
    ):
        users = []
        if getattr(entry, "user", None):
            users.append(entry.user)
        if getattr(entry, "old", None) and getattr(entry.old, "participant", None):
            p = entry.old.participant
            if getattr(p, "user_id", None) == target_user_id:
                user = await client.get_entity(target_user_id)
                participant = await client.get_input_entity(target_user_id)
                return None, participant, channel, user, target_user_id
        if getattr(entry, "new", None) and getattr(entry.new, "participant", None):
            p = entry.new.participant
            if getattr(p, "user_id", None) == target_user_id:
                user = await client.get_entity(target_user_id)
                participant = await client.get_input_entity(target_user_id)
                return None, participant, channel, user, target_user_id
        for user in users:
            if getattr(user, "id", None) == target_user_id:
                participant = await client.get_input_entity(target_user_id)
                return None, participant, channel, user, target_user_id
    raise ValueError(f"Could not find admin-log entity for user_id={target_user_id} in target chat")


async def resolve_target(client, trigger_msg, target_spec):
    if not target_spec:
        return await resolve_target_from_reply(client, trigger_msg)
    if target_spec["type"] == "id":
        try:
            return await resolve_target_from_id(client, target_spec["value"])
        except Exception:
            logger.warning("resolve_target_from_id_failed_admin_log user_id=%s", target_spec["value"])
            return await resolve_target_from_admin_log(client, target_spec["value"])
    if target_spec["type"] == "username":
        return await resolve_target_from_username(client, target_spec["value"])
    return await resolve_target_from_reply(client, trigger_msg)


async def cleanup_trigger_message(client, trigger_msg_id: int | None):
    if trigger_msg_id:
        asyncio.create_task(delete_later(client, trigger_msg_id))


async def delete_participant_history_background(client, channel, participant):
    try:
        await client(functions.channels.DeleteParticipantHistoryRequest(channel=channel, participant=participant))
    except Exception:
        logger.exception("delete_participant_history_background_error")


def fallback_target_label(target_spec):
    if not target_spec:
        return None
    if target_spec["type"] == "id":
        return f"用户{target_spec['value']}"
    if target_spec["type"] == "username":
        return f"@{target_spec['value']}"
    return None


async def kick_and_purge(client, trigger_msg, target_spec):
    try:
        reply_to_id, participant, channel, user, uid = await resolve_target(client, trigger_msg, target_spec)
    except Exception as e:
        logger.exception("kick_resolve_error")
        await cleanup_trigger_message(client, trigger_msg.id)
        await send_temp_reply(client, trigger_msg.id, explain_error(e, fallback_target_label(target_spec)))
        return
    if not participant:
        await send_temp_reply(client, trigger_msg.id, "❌ 操作失败：请先回复目标消息或提供正确用户ID/@用户名")
        return
    target_name = display_name_from_user(user) if user else f"用户{uid}"
    try:
        await client(functions.channels.EditBannedRequest(
            channel=channel,
            participant=participant,
            banned_rights=types.ChatBannedRights(until_date=None, view_messages=True),
        ))
        await cleanup_trigger_message(client, trigger_msg.id)
        await send_temp_reply(client, reply_to_id or trigger_msg.id, f"🚫 已封禁并踢出 {target_name}")
        asyncio.create_task(delete_participant_history_background(client, channel, participant))
    except Exception as e:
        logger.exception("kick_error")
        await cleanup_trigger_message(client, trigger_msg.id)
        await send_temp_reply(client, trigger_msg.id, explain_error(e, target_name))


async def mute_user(client, trigger_msg, mute_seconds: int, target_spec):
    try:
        reply_to_id, participant, channel, user, uid = await resolve_target(client, trigger_msg, target_spec)
    except Exception as e:
        logger.exception("mute_resolve_error")
        await cleanup_trigger_message(client, trigger_msg.id)
        await send_temp_reply(client, trigger_msg.id, explain_error(e, fallback_target_label(target_spec)))
        return
    if not participant:
        await send_temp_reply(client, trigger_msg.id, "❌ 操作失败：请先回复目标消息或提供正确用户ID/@用户名")
        return
    target_name = display_name_from_user(user) if user else f"用户{uid}"
    adjusted = False
    if mute_seconds != 0 and mute_seconds < MIN_TEMP_MUTE_SECONDS:
        mute_seconds = MIN_TEMP_MUTE_SECONDS
        adjusted = True
    if mute_seconds > MAX_TEMP_MUTE_SECONDS:
        await cleanup_trigger_message(client, trigger_msg.id)
        await send_temp_reply(client, trigger_msg.id, "❌ 操作失败：临时禁言最长不能超过366天，请使用禁言永久")
        return
    until_date = None if mute_seconds == 0 else int(time.time()) + mute_seconds
    try:
        await client(functions.channels.EditBannedRequest(
            channel=channel,
            participant=participant,
            banned_rights=types.ChatBannedRights(
                until_date=until_date,
                send_messages=True,
                send_media=True,
                send_stickers=True,
                send_gifs=True,
                send_games=True,
                send_inline=True,
                embed_links=True,
                send_polls=True,
                change_info=False,
                invite_users=False,
                pin_messages=False,
            ),
        ))
        await cleanup_trigger_message(client, trigger_msg.id)
        msg = f"✅ 已禁言 {target_name} {format_duration_text(mute_seconds)}"
        if adjusted:
            msg += "（已自动调整为最短30秒）"
        await send_temp_reply(client, reply_to_id or trigger_msg.id, msg)
    except Exception as e:
        logger.exception("mute_error")
        await cleanup_trigger_message(client, trigger_msg.id)
        await send_temp_reply(client, trigger_msg.id, explain_error(e, target_name))


async def fully_unrestrict_user(client, trigger_msg, target_spec):
    try:
        reply_to_id, participant, channel, user, uid = await resolve_target(client, trigger_msg, target_spec)
    except Exception as e:
        logger.exception("unrestrict_resolve_error")
        await cleanup_trigger_message(client, trigger_msg.id)
        await send_temp_reply(client, trigger_msg.id, explain_error(e, fallback_target_label(target_spec)))
        return
    if not participant:
        await send_temp_reply(client, trigger_msg.id, "❌ 操作失败：请先回复目标消息或提供正确用户ID/@用户名")
        return
    target_name = display_name_from_user(user) if user else f"用户{uid}"
    try:
        await client(functions.channels.EditBannedRequest(
            channel=channel,
            participant=participant,
            banned_rights=types.ChatBannedRights(
                until_date=None,
                view_messages=False,
                send_messages=False,
                send_media=False,
                send_stickers=False,
                send_gifs=False,
                send_games=False,
                send_inline=False,
                embed_links=False,
                send_polls=False,
                change_info=False,
                invite_users=False,
                pin_messages=False,
            ),
        ))
        await cleanup_trigger_message(client, trigger_msg.id)
        await send_temp_reply(client, reply_to_id or trigger_msg.id, f"✅ 已解禁 {target_name}")
    except Exception as e:
        logger.exception("unrestrict_error")
        await cleanup_trigger_message(client, trigger_msg.id)
        await send_temp_reply(client, trigger_msg.id, explain_error(e, target_name))


async def praise_user(client, trigger_msg, target_spec):
    try:
        reply_to_id, participant, channel, user, uid = await resolve_target(client, trigger_msg, target_spec)
    except Exception as e:
        logger.exception("praise_resolve_error")
        await cleanup_trigger_message(client, trigger_msg.id)
        await send_temp_reply(client, trigger_msg.id, explain_error(e, fallback_target_label(target_spec)))
        return
    if not user:
        await send_temp_reply(client, trigger_msg.id, "❌ 操作失败：请先回复目标消息或提供正确用户ID/@用户名")
        return
    target_name = display_name_from_user(user)
    await cleanup_trigger_message(client, trigger_msg.id)
    await send_temp_reply(client, reply_to_id or trigger_msg.id, build_praise_text(target_name))



async def summarize_recent_messages(client, trigger_msg, count: int):
    try:
        messages = await client.get_messages(TARGET_CHAT_ID, limit=count)
        lines = []
        for m in reversed(messages):
            if not m or not m.raw_text:
                continue
            sender = ""
            try:
                u = await m.get_sender()
                if u:
                    fn = (getattr(u, "first_name", None) or "").strip()
                    ln = (getattr(u, "last_name", None) or "").strip()
                    sender = (fn + " " + ln).strip() or "uid{}".format(m.sender_id)
            except Exception:
                sender = "uid{}".format(m.sender_id)
            lines.append("{}: {}".format(sender, m.raw_text.strip()))

        if not lines:
            await send_temp_reply(client, trigger_msg.id, "❌ 没有找到可总结的消息")
            return

        chat_text = "\n".join(lines)
        prompt = "以下是群聊最近 {} 条消息，请用中文简洁总结大家主要聊了什么内容，分点列出核心话题，不要逐条翻译：\n\n{}".format(count, chat_text)

        payload = _json.dumps({
            "model": AI_MODEL,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}]
        }).encode("utf-8")

        req = urllib.request.Request(
            AI_API_BASE + "/v1/messages",
            data=payload,
            headers={
                "x-api-key": AI_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = _json.loads(resp.read().decode("utf-8"))

        text_blocks = [b["text"] for b in result.get("content", []) if b.get("type") == "text"]
        if not text_blocks:
            raise ValueError("API returned no text block: " + str(result))
        summary = text_blocks[0].strip()
        reply_text = "📋 最近 {} 条消息总结：\n\n{}".format(count, summary)

        sent = await client.send_message(entity=TARGET_CHAT_ID, message=reply_text, reply_to=trigger_msg.id)
        asyncio.create_task(delete_later(client, trigger_msg.id, 5))
        if sent and getattr(sent, "id", None):
            asyncio.create_task(delete_later(client, sent.id, SUMMARY_DELETE_SECONDS))

    except Exception:
        logger.exception("summarize_error")
        await send_temp_reply(client, trigger_msg.id, "❌ 总结失败，请稍后重试")

async def handle_control_command(client, msg):
    try:
        raw_text = (msg.raw_text or "").strip()
        text = normalize_text(raw_text)
        target_spec = parse_target_command(raw_text)
        effective_text = target_spec["command"] if target_spec else text
        m_summary = SUMMARY_PATTERN.match(effective_text)
        if m_summary:
            count = int(m_summary.group(1))
            count = max(1, min(count, 500))
            asyncio.create_task(summarize_recent_messages(client, msg, count))
            return
        if effective_text in STATUS_TRIGGER_TEXTS:
            await send_temp_reply(client, msg.id, "✅ 机器人运行正常（极速模式）")
            asyncio.create_task(cleanup_trigger_message(client, msg.id))
            return
        if target_spec is None and not msg.reply_to_msg_id:
            return
        if effective_text in KICK_TRIGGER_TEXTS:
            await kick_and_purge(client, msg, target_spec)
            return
        if effective_text in PRAISE_TRIGGER_TEXTS:
            await praise_user(client, msg, target_spec)
            return
        mute_seconds = parse_mute_seconds(effective_text)
        if mute_seconds is not None:
            await mute_user(client, msg, mute_seconds, target_spec)
            return
        if effective_text in UNMUTE_TRIGGER_TEXTS or effective_text in UNBAN_TRIGGER_TEXTS:
            await fully_unrestrict_user(client, msg, target_spec)
            return
    except Exception as e:
        logger.exception("handle_control_command_error")
        await send_temp_reply(client, msg.id, explain_error(e))


async def main():
    client = TelegramClient(SESSION, API_ID, API_HASH, sequential_updates=False, catch_up=False)
    await client.start()
    me = await client.get_me()
    me_id = getattr(me, "id", None)

    logger.error("tg-auto-heart started in polling mode random 1-5s")

    processed_ids = set()

    while True:
        try:
            messages = await client.get_messages(TARGET_CHAT_ID, limit=30)
            for msg in reversed(messages):
                if not msg:
                    continue
                mid = getattr(msg, "id", None)
                if not mid or mid in processed_ids:
                    continue
                if msg.chat_id != TARGET_CHAT_ID:
                    continue
                if msg.sender_id == me_id:
                    continue
                if msg.sender_id not in CONTROL_USER_IDS:
                    continue
                processed_ids.add(mid)
                asyncio.create_task(handle_control_command(client, msg))

            if len(processed_ids) > 5000:
                processed_ids = set(sorted(processed_ids)[-2000:])
        except Exception:
            logger.exception("poll_loop_error")

        await asyncio.sleep(random.uniform(1, 5))


if __name__ == "__main__":
    asyncio.run(main())
