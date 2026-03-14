# Agentic Girlfriend

This is my old project from 2024.

A Telegram bot that simulates an AI agent girlfriend, generates responses with an LLM, keeps conversation history, and monetizes interaction through subscriptions, paid media, and donations.

The bot is built on the python-telegram-bot framework and uses an external LLM via APIs such as Together AI or OpenAI.

Main functionality of the bot is the FSM-based LLM prompting - allowing the bot to look actually real and have its own emotional states with a bit of a random mood swings.

## Main functionality

**1. Conversational AI**

The bot acts as a girlfriend-style chat partner.
User messages are sent to an LLM with a predefined system prompt describing the personality and communication style.

Responses are generated based on:

* recent conversation history
* relationship context between the user and the bot
* randomly selected interaction “moods” (short, medium, or full responses)

Conversation history is stored in `conversation_histories.json`.

---

**2. Free message limit and paywall**

Users can send a limited number of free messages.

After the limit is reached, the bot shows a paywall encouraging the user to subscribe via a Telegram channel. If the user is not a subscriber, responses are restricted until subscription.

---

**3. Channel membership check**

Before allowing full interaction, the bot verifies whether the user is subscribed to a specific Telegram channel.

Non-subscribed users receive:

* a subscription message
* a link to join the channel

Subscribers get full access to the conversation features.

---

**4. Paid media (photos and videos)**

Subscribers can request photos or videos.

The bot sends media using Telegram’s paid media feature:

* photos have a price in Telegram Stars
* videos have a higher price
* media is randomly selected from local files

---

**5. Donations**

Occasionally the bot asks the user for a small donation using Telegram Stars payments.
The donation request appears randomly during conversations.

---

**6. Scheduled “heart” messages**

The bot periodically sends spontaneous messages such as:

* “думаю о тебе”
* “я соскучилась”
* “напиши как будет время”

These are scheduled per user using the Telegram job queue and simulate the bot initiating contact.

---

**7. Conversation persistence**

All messages are saved with timestamps so the bot can:

* remember previous discussions
* analyze the relationship context
* generate more personalized replies

---

**8. Commands**

The bot supports several commands:

`/start`
Starts the interaction and performs membership verification.

`/unsubscribe`
Allows users to unsubscribe from the associated channel.

`/clear`
Clears the conversation history.

---

## How it works (simplified flow)

1. User sends a message to the bot.
2. The bot checks channel subscription status.
3. The message is added to conversation history.
4. The bot may trigger special features:

   * photo/video requests
   * paywall
   * donation request
5. The conversation context is sent to the LLM.
6. The LLM generates a reply.
7. The reply is stored and sent back to the user.

---

## Storage

The bot stores data locally:

* `conversation_histories.json` — chat histories
* `users_started.txt` — users who started the bot
* `users_chatting.txt` — users who actively chat
* `users_paywall.txt` — users who reached the paywall

---

## Running the bot

1. Insert your Telegram bot token.
2. Set API keys for the LLM provider.
3. Configure channel IDs and links.
4. Run the script:

```
python bot.py
```

The bot will start polling Telegram and begin responding to messages.
