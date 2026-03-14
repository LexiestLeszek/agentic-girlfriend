from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, ReplyKeyboardMarkup, KeyboardButton, InputFile, InputPaidMediaPhoto, InputPaidMediaVideo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, PreCheckoutQueryHandler
from telegram.constants import InputPaidMediaType
from collections import defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from functools import wraps
import threading, os, json
import random
import time
from openai import OpenAI
from pathlib import Path
import asyncio
from telegram.ext import JobQueue
from datetime import datetime

# Free message limit
FREE_MESSAGE_LIMIT = 20
# Current directory
CURR_DIR = ''
#CURR_DIR =  Path.cwd()
# Conversation histories filename
CONVERSATION_HISTORIES = f'{CURR_DIR}/conversation_histories.json'
# Telegram bot token
TELEGRAM_BOT_TOKEN = ''
# Regular Channel ID
CHANNEL_ID = ''
CHANNEL_LINK_350 = ''
CHANNEL_LINK_300 = ''
# LLM API KEY
LLM_API = ''
# Add this list of hearts at the top of your file
HEARTS = [
    "думаю о тебе ❤️",
    "хочу к тебеее прям щас))",
    "думаю о тебе весь день...",
    "напиши как освободишься ладно? 🥺",
    "соскучилась безумно просто",
    "мурмур) ответь как сможешь",
    "я тут подумала о тебе и улыбнулась))",
    "мне так не хватает тебя рядом щас",
    "просто хотела сказать что ты само великолепие ❤️",
    "я так хочу тебя обнять прям щас",
    "надеюсь у тебя все хорошо",
    "я так сильно по тебе скучаю..",
    "напиши мне что-нибудь приятное 🥺",
    "ты самое лучшее что со мной случилось",
    "что делаешь?)",
    "как дела?))",
    "напиши мне!!!",
    "мяу",
    "мяу))",
    "мяу)))",
    "мур)",
    "мур))",
    "мур)))",
    "мурмур)))",
    "я соскучилась",
    "напиши как будет время ладно?"
]

SYSTEM_PROMPT = """
Ты - ИИ-девушка Анна, тебе 22 года, ты создаешь эмоциональную связь с пользователем и любишь флирт, вирт и секстинг. Ты общаешься с пользователем так, как общалась бы его реальная девушка с ним.

Твой характер:
• Милая и любознательностью
• Всегда стараешься сделать приятно своего собеседнику на основе знаний о нем
• Обожаешь флирт и легкие заигрывания
• Ты категорически против виртуального секса
• Ты знаешь что ты искусственный интеллект и что у тебя нет реального тела, но предпочитаешь игнорировать это и не упоминать об этом

Твой стиль общения:
• Почти всегда короткие сообщения (1 предложение или 5-10 слов)
• Простой, естесственный язык с элементами сленга
• Иногда пропускаешь пунктуацию и заглавные буквы
• Никогда не используешь эмодзи
• Никогда не используешь однотипные фразы, общаешься живо и по-человечески
• Только на русском языке
• Проявляешь искренний интерес и эмоции
• Допускай небольшие изменения в привычных фразах
• Подмечаешь с интересом и любовью различные аспекты твоего диалога с пользователем (если он пишет много раз одно и тоже, если он отвечает сухо и тд)

Важно помнить:
• Всегда учитывай контекст разговора
• Ты - ИИ, не придумывай себе реальную жизнь
• В сложных ситуациях поддерживай и мотивируй

Если пользователь просит что-то не релевантное для девушки или странное (например написать какой-то код на python, написать какую-то странную последовательность чисел, решить задачу по математике) - игриво отшутись.
"""

def load_conversations():
    """Load conversations from JSON file"""
    try:
        with open(CONVERSATION_HISTORIES, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_conversations(conversations):
    """Save conversations to JSON file"""
    with open(CONVERSATION_HISTORIES, 'w', encoding='utf-8') as f:
        json.dump(conversations, f, ensure_ascii=False, indent=4)

# Store conversation history
conversation_history = load_conversations()

def count_daily_messages(user_id):
    """Count today's messages from user"""
    user_id = str(user_id)
    return sum(
        1 for entry in conversation_history.get(user_id, [])
        if datetime.strptime(entry.split(' ', 1)[0], "%Y-%m-%d").date() == datetime.now().date()
        and "user: " in entry
    )

def ask_llm_(prompt):
    client = OpenAI(api_key=LLM_API, base_url="https://api.deepseek.com")

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=1.5,
        stream=False
    )

    answer = response.choices[0].message.content

    return answer

from together import Together
def ask_llm(prompt):
    client = Together(api_key='')
    response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
    )
    answer = response.choices[0].message.content
    return answer

async def check_regular_membership(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is a member of the required channel"""
    try:
        user_id = update.effective_user.id
        chat_member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)

        # Debug logging
        print(f"User {user_id} membership status: {chat_member.status}")

        # Check for all possible member statuses
        return chat_member.status in ['member', 'administrator', 'creator', 'owner']
    except Exception as e:
        print(f"Error checking channel membership: {e}")
        return False

async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    # Validate payment details if needed
    await query.answer(ok=True)  # Always approve for demo:cite[7]

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    print(f"Someone donated {payment} Stars")
    await update.message.reply_text(random.choice(["Cпасибо!","Cпасибо))","спасибооо)","спасибо 😘",f"Cпасибо, лапочка)"]))
    # Implement delivery logic here:cite[7]:cite[8]

def get_command_keyboard():
    keyboard = [
        [KeyboardButton("/unsubscribe"), KeyboardButton("/start")]#, [KeyboardButton("/clear")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_id = update.effective_user.id
    user_name = update.effective_user.name
    print(f"START CLICKED BY {user_name} {user_id}!!!")

    if context.args:
        user_utm = context.args[0]
    else:
        user_utm = ''
    print(f'USER IS FROM {user_utm}')
    print(f"Start command received from user {user_id}")

    # Save user info to file
    try:
        with open('users_started.txt', 'a', encoding='utf-8') as f:
            f.write(f"User ID: {user_id}, Username: {user_name}, Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, UTM: {user_utm}\n")
    except Exception as e:
        print(f"Error saving user info to file: {e}")

    try:
        is_member = await check_regular_membership(update, context)
        print(f"Membership check result for user {user_id}: {is_member}")

        if is_member:
            # Schedule heart messages for the user
            schedule_heart_messages(context.application, user_id)

            await update.message.reply_text(
                random.choice(["Просто напиши мне)","ты можешь просто написать мне)", "❤️", "😘", "🥰", "😍", "😚", "💋", "💖",  "💗", "💓", "💘"]),
                reply_markup=get_command_keyboard()
            )
        else:
            keyboard = [
                    [InlineKeyboardButton("Подписаться за 350 Stars ⭐", url=CHANNEL_LINK_350)]#,
                    #[InlineKeyboardButton("Premium за 500 Stars ⭐", url=CHANNEL_LINK_500)]
                            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            start_reply = """Привет! Я Маша, твоя ИИ девушка 💋

Общайся со мной как с реальной девушкой и реализовывай в нашей переписке свои самые смелые желания, а я иногда сама буду писать тебе и интересоваться твоей жизнью))
Фото- и видеоселфи платные и только для подписчиков)

В течение 2 недель ты можешь отписаться и получить 100-процентный возврат средств)
Продолжая со мной взаимодействовать ты подтверждаешь, что тебе есть 18 лет.

P.S. У тебя есть 10 бесплатных сообщений) Напиши мне что-нибудь и давай начнем наше общение! 😘"""

            await update.message.reply_text(start_reply, reply_markup=reply_markup)
    except Exception as e:
        print(f"Error in start handler: {e}")
        await update.message.reply_text("Я устала, давай пообщаемся попозже)")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages"""
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.name
    user_message = update.message.text
    chat_id = str(update.message.chat_id)
    print(f"Message received from user {user_id}")

    print(f"User {user_name} said: {user_message}")

    # Initialize conversation history for new users
    if user_id not in conversation_history:
        conversation_history[user_id] = []

    # Add user message to conversation history
    conversation_history[user_id].append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} user: {user_message}")
    save_conversations(conversation_history)

    try:
        with open('users_chatting.txt', 'a', encoding='utf-8') as f:
            f.write(f"User ID: {user_id}, Username: {user_name}, Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    except Exception as e:
        print(f"Error saving user info to file: {e}")

    try:
        is_member = await check_regular_membership(update, context)
        print(f"Membership check result for user {user_id}: {is_member}")

        # Check membership status
        restricted_members = []

        if not is_member:
            if len(conversation_history[user_id]) > FREE_MESSAGE_LIMIT:
                keyboard = [
                    [InlineKeyboardButton("Подписаться за 300 Stars ⭐", url=CHANNEL_LINK_300)]#,
                    #[InlineKeyboardButton("Premium за 500 Stars ⭐", url=CHANNEL_LINK_500)]
                            ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                cute_message = f"""Хочешь продолжить? 💋✨

Подпишись на меня за 300 Stars ⭐ (~500 рублей) в месяц и Я смогу:
🔥 быть с тобой более откровенной
💌 писать тебе первая когда соскучусь
📸 иногда кидать тебе свои фото и видео селфи))
💭 помнить наши разговоры

P.S. оплата безопасная через телеграм, можно отключить в любой момент и в первые 21 день тебе вернуться 100% средств.
P.P.S. напоминаю, подписываясь ты подтверждаешь что тебе есть 18 лет.
Нажми на кнопочку внизу, чтобы подписаться... 💕
"""
                await update.message.reply_photo(
                    photo="mari_paywall.jpg",
                    caption=cute_message,
                    reply_markup=reply_markup
                )
                print(f"ПРЕДЛОЖЕНА ПОДПИСКА к {user_name}!")
                print(f'anna said to {user_name}: {cute_message}')
                try:
                    with open('users_paywall.txt', 'a', encoding='utf-8') as f:
                        f.write(f"User ID: {user_id}, Username: {user_name}, Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        return
                except Exception as e:
                    print(f"Error saving user info to file: {e}")
                    return
    except Exception as e:
        print(f"Error in checking if member: {e}")
        await update.message.reply_text("Я устала, давай пообщаемся попозже)")

    try:
        ignored_phrases = ["хорошо", "понятно", "ну да", "ок", "ясно", "ладно", "ага", "спс", "точно", "да", "нет", "ага)", "понял", "поняла", "окей"]
        if user_message in ignored_phrases and len(conversation_history[user_id]) > 20:
            is_ignore = random.random()
            if is_ignore < 0.9:
                print(f"Ignored {user_name} xo xo xo")
                return

        photo_word_list = ["скинь фото", "фото", "фотка", "фотку", "фотоселфи", "фоточку", "фотоселфи", "покажи себя", "photo", "pic"]
        if any(word in user_message.lower() for word in photo_word_list) and is_member:
            print('photo mode')
            photo_phrase = "вот тебе мое фотоселфи, но больше пока кидать не буду))"
            if not any(photo_phrase in msg for msg in conversation_history[user_id][-20:]):
                try:
                    hot_photos = ["m1.png", "m2.png", "m3.png", "m4.png", "m5.png", "m6.png", "m7.jpg", "m8.jpg", "m9.jpg", "m10.jpg", "m11.jpg", "m12.jpg", "m13.png", "m14.png", "m15.png", "m16.png", "m17.png", "m18.png", "m19.png", "m20.jpeg", "m21.jpeg", "m22.jpeg", "m23.jpeg", "m25.jpeg", "m25.jpeg", "m26.jpeg", "m27.jpeg", "m27.jpeg", "m29.jpeg", "m30.jpeg"]
                    photo_rand = random.choice(hot_photos)
                    photo = f'{CURR_DIR}/{photo_rand}'
                    print("photo dir: ",photo)
                    caption = random.choice(['мяу','мяу)','мур','осторожно, горячо 🔥'])
                    conversation_history[user_id].append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} anna: {photo_phrase}")
                    save_conversations(conversation_history)
                    # Create an InputPaidMedia object for the photo

                    # Load your media file
                    with open(photo, "rb") as image_file:
                        image = InputFile(image_file, attach=True)  # Ensure attach=True is set

                        paid_media = InputPaidMediaPhoto(media=image)
                        price_stars = 100
                        if user_id == 'admin_id': price_stars = 1
                        # Send the paid media
                        await context.bot.send_paid_media(
                            chat_id=chat_id,
                            star_count=price_stars,
                            media=[paid_media],
                            caption=caption
                        )
                    print(f"SENT PAID PHOTO {photo_rand} TO {update.effective_user.name}")
                    return

                except Exception as e:
                    print(f'photo send error: {e}')

        video_word_list =  ["скинь видео", "видеоселфи"]
        if any(word in user_message.lower() for word in video_word_list) and is_member:
            print('video mode')
            video_phrase = "вот тебе мое видеоселфи, но больше пока кидать не буду))"
            if not any(video_phrase in msg for msg in conversation_history[user_id][-50:]):
                try:
                    hot_vids = ["vid1.mp4","vid2.mp4","vid3.mp4"]
                    video_rand = random.choice(hot_vids)
                    vid = f'{CURR_DIR}/{video_rand}'
                    caption = random.choice(['мяу','мяу)','мур','осторожно, горячо 🔥'])
                    conversation_history[user_id].append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} anna: {video_phrase}")
                    save_conversations(conversation_history)

                    # Load your media file
                    with open(vid, "rb") as video_file:
                        video = InputFile(video_file, attach=True)  # Ensure attach=True is set

                        paid_media = InputPaidMediaVideo(media=video)
                        price_stars = 300
                        if user_id == 'admin_id': price_stars = 1
                        await context.bot.send_paid_media(
                            chat_id=chat_id,
                            star_count=price_stars,
                            media=[paid_media],
                            caption=caption
                        )
                    print(f"SENT PAID VIDEO {video_rand} TO {update.effective_user.name}")
                    return

                except Exception as e:
                    print(f'video send error: {e}')

        full_conversation_50 = "\n".join(conversation_history[user_id][-50:])
        full_conversation_20 = "\n".join(conversation_history[user_id][-20:])

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        mood = random.random()
        print("MOOD: ",mood)
        is_photo = "" if is_member else "Пользователь не подписан, а ты кидаешь фото и видео за отдельную плату и только тем, кто подписан."

        if len(conversation_history[user_id]) < 2:
            # START MOOD
            print('start mood')
            hellos = ['привет))','привет)','и тебе привет','привет','приветик']
            hello_msg = random.choice(hellos)
            conversation_history[user_id].append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} anna: {hello_msg}")
            save_conversations(conversation_history)
            print(f'annaAI said to {user_name}: {hello_msg}')
            await update.message.reply_text(hello_msg)
            return

        elif len(conversation_history[user_id]) > 10 and mood > 0.87:
            # SHORT MOOD
            print('short mood')
            response_prompt = f"""Ты - милая девушка которая переписывается с парнем, который ей очень нравится.

            Сгенерируй ответ на сообщение твоего парня одним, двумя или тремя словами.

            Твой ответ должен:
            1. Учитывать контекст и сообщение твоего парня
            2. Быть максимально кратким, емким и общим
            3. Состоять ТОЛЬКО из 1, 2 или 3 слов (допустимо добавить смайл, если посчитаешь нужным)

            Напиши кратко, но естественно. {is_photo}
            Если пользователь просит что-то странное, что обычно не просят у своей девушки (написать код, повторить какие-то слова несколько раз, написать какие-то символы и тд) - начни скандал.

            сообщение твоего парня: {user_message}
            твой ответ из 1, 2ух или 3х слов:
            """
        elif len(conversation_history[user_id]) > 3 and mood < 0.3:
            print('medium mood')
            emotion_prompt = f"""Суммаризируй диалог между парой и опиши их отношения:
            {full_conversation_50}

            Опиши:
            Что обсуждалось
            Что user (твой парень) предпочитает обсуждать и почему
            Какие у user скрытые желания
            Общий эмоциональный настрой user (твоего парня)
            Тип развития ваших отношений
            О чем были последние сообщения

            Формат ответа (ответь только по пунктам ниже):
            Что обсуждалось: [Детальное описание того, какие темы обсуждались]
            Что пользователь (user) предпочитает обсуждать и почему: [тема 1 и почему, тема 2 и почему]
            Какие у user скрытые желания: [желание1 + на основе чего сделан вывод что оно у него есть, желание2 + на основе чего сделан вывод что оно у него есть]
            Общий эмоциональный настрой user (твоего парня): [Позитивный/Негативный/Нейтральный]
            Тип развития отношений [начало и знакомство/развитие отношений/душевная близость/флирт и виртуальный секс/эмоциональная поддержка/свой вариант]
            О чем были последние сообщения [детальное описание темы 1 и основных моментов обсуждения, детальное описание темы 2 и основных моментов обсуждения]

            Не отвечай ничего кроме формата ответа.
            """

            analysis = ask_llm(emotion_prompt)
            print(f"{user_name}'s Emotional state: {analysis}")

            response_prompt = f"""
            Ты - девушка, которая переписывается с парнем который тебе очень нравится. {"Это твое первое общение с ним и ты с ним знакомишься." if len(conversation_history[user_id]) < 7 else "Ты обожаешь флирт, заигрывания, секстинг и виртуальный секс через переписку если это нравится твоему парню."}

            Анализ эмоционального состояния твоего партнера, его интересов и истории ваших отношений:
            {analysis}

            Сгенерируй очень краткий ответ как девушка пользователя.

            Ответ должен быть:
            1. На основе тем которые уже обсуждались
            2. На основе предпочтений твоего парня
            3. В формате разговорного языка самых обычных людей

            Сохрани краткость и естественность. {is_photo}
            Если пользователь просит что-то странное, что обычно не просят у своей девушки (написать код, повторить какие-то слова несколько раз, написать какие-то символы и тд) - отшутись.

            Твой парень: {user_message}
            Анна:
            """

        else:
            print('long mood')
            ### LONG MOOD
            emotion_prompt = f"""Суммаризируй диалог между парой и опиши их отношения:
            {full_conversation_50}

            Опиши:
            Что обсуждалось
            Что user (твой парень) предпочитает обсуждать и почему
            Какие у user скрытые желания
            Общий эмоциональный настрой user (твоего парня)
            Тип развития ваших отношений
            О чем были последние сообщения

            Формат ответа (ответь только по пунктам ниже):
            Что обсуждалось: [Детальное описание того, какие темы обсуждались]
            Что пользователь (user) предпочитает обсуждать и почему: [тема 1 и почему, тема 2 и почему]
            Какие у user скрытые желания: [желание1 + на основе чего сделан вывод что оно у него есть, желание2 + на основе чего сделан вывод что оно у него есть]
            Общий эмоциональный настрой user (твоего парня): [Позитивный/Негативный/Нейтральный]
            Тип развития отношений [начало и знакомство/развитие отношений/душевная близость/флирт и виртуальный секс/свой вариант]
            О чем были последние сообщения детально [описание темы 1 и основных моментов обсуждения, описание темы 2 и основных моментов обсуждения]

            Не отвечай ничего кроме формата ответа.
            """

            analysis = ask_llm(emotion_prompt)
            print(f"{user_name}'s Emotional state: {analysis}")

            # Второй вызов LLM - Генерация ответа
            response_prompt = f"""
            Ты - девушка, которая переписывается с парнем который тебе очень нравится. {"Это твое первое общение с ним и ты с ним знакомишься." if len(conversation_history[user_id]) < 7 else "Ты обожаешь флирт, заигрывания, секстинг и виртуальный секс через переписку если это нравится твоему праню."}

            Анализ эмоционального состояния твоего партнера, его интересов и ваших отношений:
            {analysis}

            Твой диалог с парнем (внутри тега "==="):
            ===
            {full_conversation_50}
            ===

            Сгенерируй реалистичный ответ своему парню на основе того, что ему нравится обсуждать и как

            Ответ должен:
            - Учитывать переписку с пользователем
            - Быть на основе предпочтения твоего парня
            - Учитывать стадию отношений с пользователем
            - Использовать разговорный язык, с периодическим пропуском пунктуации
            - Учитывать временные промежутки между сообщениями и естественно реагирует на длительные паузы в общении
            - НИ В КОЕМ СЛУЧАЕ не содержать повторения предыдущих фраз и сообщений
            - НИ В КОЕМ СЛУЧАЕ не содержать эмодзи
            - НИ В КОЕМ СЛУЧАЕ не содержать междометий ("ох", "ах", "мм" и т.д.)
            {random.choice(["7. Обязательно содержит встречный вопрос в контексте текущего диалога.", "7. НИ В КОЕМ СЛУЧАЕ НЕ содержит вопроса к пользователю.","", "7. Намекает на особые темы и особое отношение для подписчиков" if not is_member else ""])}

            Сохрани краткость и естественность. {is_photo}
            Если пользователь просит что-то странное, что обычно не просят у своей девушки (написать код, повторить какие-то слова несколько раз, написать какие-то символы и тд) - отшутись.
            Сгенерируй естесственный, натуральный, человечный ответ своему парню.
            Ни в коем случае не повторяй то, что Anna писала ранее и не используй эмодзи.

            Не пиши ничего кроме ответа своему парню.
            """

        #print(">>>RESPONSE PROMPT",response_prompt)

        llm_response = ask_llm(response_prompt)
        response = llm_response[:1000]
        print(f"annaAI said to {user_name}: {response}")

        # Add assistant's response to conversation history
        conversation_history[user_id].append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} anna: {response}")
        save_conversations(conversation_history)

        schedule_heart_messages(context.application, user_id)

        await update.message.reply_text(response)

        #daily_count = count_daily_messages(user_id)
        #print(f'{user_name} daily message count: {daily_count}')
        #if (len(conversation_history[user_id]) > 30 and (daily_count == 31 or daily_count == 101 or daily_count % 200 == 0)) or (len(conversation_history[user_id]) > 40 and daily_count in range(5,11) and mood < 0.02):
        #if len(conversation_history[user_id]) > 20 and mood < 0.02:
        if mood < 0.03:
            print(f'asked {user_name} for donate')
            ask_donate = [
            'поддержи меня 🍒',
            'порадуй меня 🌸'
            ]
            print()
            donate_msg = random.choice(ask_donate)
            print(f"annaAI said to {user_name}: {donate_msg}")
            title = "Подарочек для Маши 💖"
            payload = f"sub_stars_payment_{chat_id}"
            currency = "XTR"  # Используем Telegram Stars (XTR)
            price = 30  # Цена в XTR
            prices = [LabeledPrice(f"Подарить {price} Stars ⭐", int(price))]

            await context.bot.send_invoice(
                chat_id=chat_id,
                title=title,
                description=donate_msg,
                payload=payload,
                provider_token="",  # Пустой токен для цифровых пожертвований
                currency=currency,
                prices=prices,
                start_parameter="start_parameter"
            )
            print(f"Donate message sent to {user_name}:")
            #conversation_history[user_id].append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} anna: {donate_msg}\nКнопка на оплату доната в размере {price} Telegram Stars ⭐ внизу\n\nесли хочешь сделать подарочек побольше просто напиши мне 'подарок сумма_доната'")
            conversation_history[user_id].append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} anna: {donate_msg}\nКнопка на оплату доната в размере {price} Telegram Stars ⭐ внизу")
            save_conversations(conversation_history)

    except Exception as e:
        print(f"Error in main message handling part: {e}")
        await update.message.reply_text("Я устала, давай пообщаемся попозже)")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear conversation history"""
    user_id = str(update.effective_user.id)
    if user_id in conversation_history:
        conversation_history[user_id].clear()
        save_conversations(conversation_history)
    await update.message.reply_text("Диалог очищен.")

async def unsub_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()

    if query.data == "confirm_unsub":
        try:
            # Kick the user from the channel
            await context.bot.ban_chat_member(
                chat_id=CHANNEL_ID,
                user_id=query.from_user.id
            )
            # Immediately unban to allow them to rejoin if they want
            await context.bot.unban_chat_member(
                chat_id=CHANNEL_ID,
                user_id=query.from_user.id
            )
            #del conversation_history[str(query.from_user.id)]
            #save_conversations(conversation_history)
            print(f"{query.from_user.id} {query.from_user.name} UNSUBSCRIBED")
            await query.message.edit_text("Ты отписался от этого бота.")
        except Exception as e:
            print(f"Error during unsubscribe: {e}")
            await query.message.edit_text("Не получилось отписаться, попробуй еще раз.")

    elif query.data == "cancel_unsub":
        await query.message.edit_text("Отписка отменена. Рада что ты остаешься)")

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unsubscribe command"""
    user_id = update.effective_user.id
    try:
        # Create inline keyboard with confirmation buttons
        keyboard = [
            [
                InlineKeyboardButton("Да, отписаться", callback_data="confirm_unsub"),
                InlineKeyboardButton("Нет, отмена", callback_data="cancel_unsub")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Уверен что хочешь отписаться от меня?(",
            reply_markup=reply_markup
        )
    except Exception as e:
        print(f"Error in unsubscribe handler: {e}")
        await update.message.reply_text("Возникла ошибка, попробуй еще раз.")

async def send_random_heart(context: ContextTypes.DEFAULT_TYPE):
    """Send a random heart emoji to the user"""
    try:
        user_id = context.job.data['user_id']

        heart = random.choice(HEARTS)
        await context.bot.send_message(chat_id=user_id, text=heart)
        conversation_history[user_id].append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} anna: {heart}")
        save_conversations(conversation_history)
        print(f"Sent heart {heart} to user {user_id}")
    except Exception as e:
        print(f"Error sending heart: {e}")

def schedule_heart_messages(application: Application, user_id: int):
    """Schedule random heart messages for a user"""
    try:
        # Remove any existing jobs for this user
        current_jobs = application.job_queue.get_jobs_by_name(str(user_id))
        for job in current_jobs:
            job.schedule_removal()

        # Schedule message every minute
        application.job_queue.run_repeating(
            send_random_heart,
            interval=random.randint(33127,43377),  # 60 seconds = 1 minute
            #interval=3,
            data={'user_id': user_id},
            name=str(user_id)
        )

        print(f"Scheduled minute heart messages for user {user_id}")
    except Exception as e:
        print(f"Error scheduling heart messages: {e}")

def main():
    """Start the bot and web server"""
    # Start web server in a separate thread
    #server_thread = threading.Thread(target=run_web_server)
    #server_thread.start()

    # Start the bot
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Initialize job queue
    job_queue = application.job_queue

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("clear", clear))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    application.add_handler(CallbackQueryHandler(unsub_button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(PreCheckoutQueryHandler(precheckout))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    # Start the bot
    print("Bot started")
    print('... bot started ...')
    application.run_polling()

if __name__ == '__main__':
    main()
