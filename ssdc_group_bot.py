#!/usr/bin/env python
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <https://www.gnu.org/licenses/>.

"""
SSDC group bot
Functions:
/start - Checks if the bot is up and running
/help - Get this help Text
/ann - Announce slot(s) to a channel
/chn - Get the list of joinable channels for slots
/source - Downloads the source code

Usage:
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import html, json, logging, os, pytz,\
       telegram as tg,\
       telegram.constants as tgc,\
       telegram.ext as tge

BIKE_GROUP_ID = -1001593988521
CAR_GROUP_ID = -1001190711156
BIKE_CHANNELS = {
    "2B P1" : -1001604026024,
    "2B P2" : -1001512038565,
    "2B P3" : -1001842179238,
    "2B P4" : -1001552345568,
    "2B P5" : -1001718416402,
    "2B P6" : -1001627609929,
    "2B P7" : -1001844283126,
    "2B P8" : -1001868104827,
    "2B RC" : -1001868702249,
    "2B RR" : -1001939909308,
    "2A P1" : -1001943914824,
    "2A P2" : -1001912331384,
    "2A P3" : -1001967167420,
    "2A RC" : -1001718018850,
    "2 P1" : -1001964773035,
    "2 P2" : -1001850933520,
    "2 P3" : -1001917546955,
    "2 RC" : -1001939432931
}
CAR_CHANNELS = {
    "TP-PDI": -1002168273942,
    "TP-SCH-3": -1002191654192,
    "TP-SCH-3A": -1002205374514,
    "3" : -1001823773006,
    "3A" : -1001634604197
}
# for /chn command output
# way too slow to get chn chat object then invite link
CHANNEL_LINKS = {
    -1001604026024 : "https://t.me/+fB4w9-K8zEJlOTJl",
    -1001512038565 : "https://t.me/+AIva_-Iv5zphYTI1",
    -1001842179238 : "https://t.me/+gGOn5mHm5kY5NTJl",
    -1001552345568 : "https://t.me/+h51k-CVRzjljNTA9",
    -1001718416402 : "https://t.me/+vtLRKWPyVgUzNWY1",
    -1001627609929 : "https://t.me/+rhNIJffk6qs5ZWRl",
    -1001844283126 : "https://t.me/+aucJV4RwdHk4NTQ1",
    -1001868104827 : "https://t.me/+vMho4VozKq4xNTFl",
    -1001868702249 : "https://t.me/+Y9FTux_MDEYxYjk1",
    -1001939909308 : "https://t.me/+ebLnzAo85fU2NDdl",
    -1001943914824 : "https://t.me/+gkzbLfcNrLA5MGU1",
    -1001912331384 : "https://t.me/+NF0AVoex4yozMjM1",
    -1001967167420 : "https://t.me/+20GoW_qUWho0N2M1",
    -1001718018850 : "https://t.me/+0fREBjkxID40ODdl",
    -1001964773035 : "https://t.me/+Spo5RmLjKJo0MjFl",
    -1001850933520 : "https://t.me/+UW9g5OY4WC43M2Nl",
    -1001917546955 : "https://t.me/+zQ1BrJsDFMxlMWI1",
    -1001939432931 : "https://t.me/+u19jMP010cYxMzU9",
    -1001823773006 : "https://t.me/+KkKUd_q4f3pmMjc1",
    -1001634604197 : "https://t.me/+3hbQj79djhU2ZWI9",
    -1002168273942 : "https://t.me/+07OaxB9HcAFlNjll",
    -1002191654192 : "https://t.me/+0hRhqJxaMhdkZGVl",
    -1002205374514 : "https://t.me/+wXCj54mx3HgxYmE1"
}

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
# higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(
    update: tg.Update,
    context: tge.ContextTypes.DEFAULT_TYPE
    ) -> None:
    """Send a message when the command /start is issued."""
    reply = " ".join((
        f"Hi {update.effective_user.mention_html()} I am indeed awake,",
        "you can proceed to /ann your slot now,",
        "or see what else I can /help with."
        ))
    await update.effective_message.reply_html(reply)

async def help(
    update: tg.Update,
    context: tge.ContextTypes.DEFAULT_TYPE
    ) -> None:
    """Send a message when the command /help is issued."""
    reply = "\n".join((" ".join((
        "I understand the following commands,",
        f"{update.effective_user.mention_html()}:")),
        "<code>/start</code> - Get a greeting",
        "<code>/help</code> - Get this help text",
        "<code>/ann</code> - Announce slot to a channel (*)",
        "<code>/chn</code> - Get the list of channels (*)",
        "(*) Only available to @ssdcmotorbikegroup and @ssdcclass345"
        ))
    await update.effective_message.reply_html(reply)
    return

def get_bike_combi(request_words) -> str:
    """Check if a request contains valid bike combi and returns combi."""
    lessons = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "RC", "RR"]
    classes = ["2B", "2A", "2"]
    # 2b is interpreted as binary number hence cannot use in variable name.
    twob_only_lessons = ["P4", "P5", "P6", "P7", "P8", "RR"]
    combi = ""
    for l in lessons:
        if l in [x.upper() for x in request_words]:
            if l in twob_only_lessons:
                combi = f"2B {l}"
                break
            else:
                for c in classes:
                    if c in [x.upper() for x in request_words]:
                        combi = f"{c} {l}"
                        break
            break
    return combi

def make_announcement_request(update, context):
    """Extract sender and message, return sender, request_text or None if invalid."""
    sender = update.effective_user
    request_text = " ".join(context.args)
    # if reply to another user's message
    if update.effective_message.reply_to_message:
        sender = update.effective_message.reply_to_message.from_user
    if len(request_text) < 9:
        return None, None
    return sender, request_text

async def ann_bike(
    update: tg.Update,
    context: tge.ContextTypes.DEFAULT_TYPE
    ) -> None:
    """Send the message to a channel when /ann is issued - BIKE GROUP."""
    combi = get_bike_combi(context.args)
    if not combi:
        await update.effective_message.reply_html(
            "\n".join((
                " ".join((
                    "You did not specify class and lesson,",
                    f"{update.effective_user.mention_html()}."
                    )),
                "Classes: 2B, 2A, or 2",
                "Lessons: P1-P8, RC, or RR",
                "Example: <code>/ann 2A P3 trysell tomorrow 3pm</code>",
                "If you need slots, join the correct channel instead.",
                "Press /chn to see the list of channels."
                ))
            )
        return
    sender, request_text = make_announcement_request(update, context)
    if not request_text:
        await update.effective_message.reply_html(
            "\n".join((
                " ".join((
                    "Your message should have at least 9 characters,",
                    f"{update.effective_user.mention_html()}."
                    )),
                "If you need slots, join the correct channel instead.",
                "Press /chn to see the list of channels."
                ))
            )
        return
    broadcast = "\n".join((
        html.escape(request_text),
        f"Sent by: {sender.mention_html()}"
        ))
    await context.bot.send_message(chat_id=BIKE_CHANNELS[combi], text=broadcast)
    if sender == update.effective_user:
        reply = f"I've sent your message, {sender.mention_html()}."
    else:
        reply = f"I've sent the message from {sender.mention_html()}."
    await update.effective_message.reply_html(reply)
    return

async def ann_car(
    update: tg.Update,
    context: tge.ContextTypes.DEFAULT_TYPE
    ) -> None:
    """Send the message to a channel when /ann is issued - CAR GROUP."""
    for c in CAR_CHANNELS:
        if c in [x.upper() for x in context.args]:
            sender, request_text = make_announcement_request(update, context)
            if not request_text:
                await update.effective_message.reply_html(
                    "\n".join((
                        " ".join((
                            "Your message should have at least 9 characters,",
                            f"{update.effective_user.mention_html()}."
                            )),
                        "If you need slots, join the correct channel instead.",
                        "Press /chn to see the list of channels."
                        ))
                    )
                return
            broadcast = "\n".join((
                html.escape(request_text),
                f"Sent by: {sender.mention_html()}"
                ))
            await context.bot.send_message(
                chat_id=CAR_CHANNELS[c],
                text=broadcast
                )
            if sender == update.effective_user:
                reply = f"I've sent your message, {sender.mention_html()}."
            else:
                reply = f"I've sent the message from {sender.mention_html()}."
            await update.effective_message.reply_html(reply)
            break
    # else executed if for loop iterated through without any break hit,
    # i.e. no valid class was found.
    else:
        await update.effective_message.reply_html(
            "\n".join((
                " ".join((
                    "You didn't specify the class: 3A (auto) or 3 (manual),",
                    f"{update.effective_user.mention_html()}."
                    )),
                "Example: <code>/ann 3A trysell tomorrow 3pm</code>",
                "If you need slots, join the correct channel instead.",
                "Press /chn to see the list of channels."
                ))
            )
        return

async def ann_dms(
    update: tg.Update,
    context: tge.ContextTypes.DEFAULT_TYPE
    ) -> None:
    """Send the message to a channel when /ann is issued - DMs."""
    combi = get_bike_combi(context.args)
    await update.effective_message.reply_html(combi)
    return

async def chn_bike(
    update: tg.Update,
    context: tge.ContextTypes.DEFAULT_TYPE
    ) -> None:
    """List the channels when /chn is issued - BIKE GROUP."""
    reply = " ".join((
        "These are the channels for motorcycle,",
        f"{update.effective_user.mention_html()}:\n"
        ))
    for c in BIKE_CHANNELS:
        reply += " ".join((
            f"* class and lesson: <b>{c}</b>,",
            f"link: {CHANNEL_LINKS[BIKE_CHANNELS[c]]}\n"
            ))
    reply += "\n"
    reply += "To get notified of slots, join the above channels.\n"
    reply += "To announce slots, use /ann"
    await update.effective_message.reply_html(reply)
    return

async def chn_bike_single(
    update: tg.Update,
    context: tge.ContextTypes.DEFAULT_TYPE
    ) -> None:
    """Get a single channel for a valid class + lesson argument. - BIKE GROUP"""
    combi = get_bike_combi(context.args)
    if not combi:
        await update.effective_message.reply_html(
            "\n".join((
                " ".join((
                    "You did not specify class and lesson,",
                    f"{update.effective_user.mention_html()}."
                    )),
                "Classes: 2B, 2A, or 2",
                "Lessons: P1-P8, RC, or RR",
                "Press /chn to see the list of channels.",
                "To announce slots, use /ann"
                ))
            )
        return
    reply = " ".join((
        f"This is the channel link for {combi},",
        f"{update.effective_user.mention_html()}:\n",
        f"{CHANNEL_LINKS[BIKE_CHANNELS[combi]]}"
        ))
    reply += "\n"
    reply += "To get notified of slots, join the above channel.\n"
    reply += "To announce slots, use /ann"
    await update.effective_message.reply_html(reply)
    return

async def chn_car(
    update: tg.Update,
    context: tge.ContextTypes.DEFAULT_TYPE
    ) -> None:
    """List the channels when /chn is issued - CAR GROUP."""
    reply = " ".join((
        "These are the channels for car,",
        f"{update.effective_user.mention_html()}:\n"
        ))
    for c in CAR_CHANNELS:
        reply += " ".join((
            f"* class: <b>{c}</b>,",
            f"link: {CHANNEL_LINKS[CAR_CHANNELS[c]]}\n"
            ))
    reply += "\n"
    reply += "To get notified of slots, join the above channels.\n"
    reply += "To announce slots, use /ann"
    await update.effective_message.reply_html(reply)
    return

async def chn_car_single(
    update: tg.Update,
    context: tge.ContextTypes.DEFAULT_TYPE
    ) -> None:
    """List the channel for a single argument. - CAR GROUP"""
    for c in CAR_CHANNELS:
        if c in [x.upper() for x in context.args]:
            reply = " ".join((
                f"This is the channel for {c},",
                f"{update.effective_user.mention_html()}:\n",
                f"{CHANNEL_LINKS[CAR_CHANNELS[c]]}"
                ))
            reply += "\n"
            reply += "To get notified of slots, join the above channel.\n"
            reply += "To announce slots, use /ann"
            await update.effective_message.reply_html(reply)
            return
    else:
        await update.effective_message.reply_html(
            "\n".join((
                " ".join((
                    "You didn't specify the class: 3A (auto) or 3 (manual),",
                    f"{update.effective_user.mention_html()}."
                    )),
                "Press /chn to see the list of channels.",
                "To announce slots, use /ann"
                ))
            )
        return
async def chn_dms(
    update: tg.Update,
    context: tge.ContextTypes.DEFAULT_TYPE
    ) -> None:
    """List the channels when /chn is issued - DMs."""
    reply = " ".join((
        
        "These are the channels for car,\n",
        ))
    for c in CAR_CHANNELS:
        reply += " ".join((
            f"* class: <b>{c}</b>,",
            f"link: {CHANNEL_LINKS[CAR_CHANNELS[c]]}\n"
            ))
    reply+="These are the channels for motorcycle,\n"    
    for c in BIKE_CHANNELS:
        reply += " ".join((
            f"* class and lesson: <b>{c}</b>,",
            f"link: {CHANNEL_LINKS[BIKE_CHANNELS[c]]}\n"
            ))
    reply += "\n"
    reply += "To get notified of slots, join the above channels.\n"
    reply += "To announce slots, use /ann"
    await update.effective_message.reply_html(reply)
    return

async def source(
    update: tg.Update,
    context: tge.ContextTypes.DEFAULT_TYPE
    ) -> None:
    await update.effective_message.reply_document(
        document=open(__file__),
        caption=" ".join((
            "This is my source code,",
            f"{update.effective_user.mention_html()}."
            ))
        )
    return

def create_photo_caption(update):
    """Return new caption with user mention or None if no caption."""
    if not update.effective_message.caption:
        return None
    return "\n".join((
        update.effective_message.caption,
        f"Sent by {update.effective_user.mention_html()}"
        ))

async def send_single_photo(chat_id, caption, update, context):
    reply_text = " ".join((
        "I've sent your photo,",
        f"{update.effective_user.mention_html()}."
        ))
    if update.effective_message.media_group_id:
        reply_text += "\nNOTE: I will only send this photo from the set you sent."
    await context.bot.send_photo(
        chat_id=chat_id,
        photo=update.effective_message.photo[0],
        caption=caption
        )
    await update.effective_message.reply_html(reply_text)

async def img_bike(
    update: tg.Update,
    context: tge.ContextTypes.DEFAULT_TYPE
    ) -> None:
    """Send the photo to the specified channel. - BIKE GROUP"""
    request_words = update.effective_message.caption.split()
    combi = get_bike_combi(request_words)
    if not combi:
        # do not print error as this function executes on every photo with
        # caption sent in bike group!
        return
    new_caption = create_photo_caption(update)
    if not new_caption or not combi:
        return
    await send_single_photo(BIKE_CHANNELS[combi], new_caption, update, context)

async def img_car(
    update: tg.Update,
    context: tge.ContextTypes.DEFAULT_TYPE
    ) -> None:
    """Send the photo to the specified channel. - CAR GROUP"""
    request_words = update.effective_message.caption.split()
    new_caption = create_photo_caption(update)
    if not new_caption:
        return
    for c in CAR_CHANNELS:
        if c in [x.upper() for x in request_words]:
            await send_single_photo(CAR_CHANNELS[c], new_caption, update, context)
            return
    else:
        # do not print error as this function is executed on every photo with
        # caption sent in car group!
        return

async def ann_help_bike(
    update: tg.Update,
    context: tge.ContextTypes.DEFAULT_TYPE
    ) -> None:
    """Give the usage for /ann without arguments. - BIKE GROUP"""
    reply = "\n".join((" ".join((
        "Please use the following format for <code>/ann</code>, ",
        f"{update.effective_user.mention_html()}:")),
        "<code>/ann &lt;class&gt; &lt;lesson&gt; &lt;remarks&gt;</code>",
        "Example: <code>/ann 2b p3 trysell tomorrow 11pm</code>",
        "Valid values for class + lesson:",
        ", ".join(list(BIKE_CHANNELS)),
        "To get notified about slots, press /chn to see the list of channels."
        ))
    await update.effective_message.reply_html(reply)
    return

async def ann_help_car(
    update: tg.Update,
    context: tge.ContextTypes.DEFAULT_TYPE
    ) -> None:
    """Give the usage for /ann without arguments. - CAR GROUP"""
    reply = "\n".join((" ".join((
        "Please use the following format for <code>/ann</code>, ",
        f"{update.effective_user.mention_html()}:")),
        "<code>/ann &lt;class&gt; &lt;remarks&gt;</code>",
        "Example: <code>/ann 3 trysell tomorrow 11pm</code>",
        "Valid values for class:",
        ", ".join(list(CAR_CHANNELS)),
        "To get notified about slots, press /chn to see the list of channels."
        ))
    await update.effective_message.reply_html(reply)
    return

async def error_handler(
    update: object,
    context: tge.ContextTypes.DEFAULT_TYPE
    ) -> None:
    """Fallback error handler for all errors in the bot."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    context.application.stop_running()
    return

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    # set bot default to HTML message output and Singapore timezone.
    with open("bot_keys.json") as fp:
        application = tge.Application.builder().token(
            json.load(fp)["api"]
            ).defaults(
                tge.Defaults(
                    parse_mode=tgc.ParseMode.HTML,
                    tzinfo=pytz.timezone("Asia/Singapore")
                    )
                ).build()

    # on different commands - answer in Telegram
    application.add_handler(tge.CommandHandler(
        "start", start
        ))
    application.add_handler(tge.CommandHandler(
        "help", help
        ))
    application.add_handler(tge.CommandHandler(
        "ann", ann_bike,
        filters=tge.filters.Chat(BIKE_GROUP_ID),
        has_args=True
        ))
    application.add_handler(tge.CommandHandler(
        "ann", ann_help_bike,
        filters=tge.filters.Chat(BIKE_GROUP_ID),
        has_args=False
        ))
    application.add_handler(tge.CommandHandler(
        "ann", ann_car,
        filters=tge.filters.Chat(CAR_GROUP_ID),
        has_args=True
        ))
    application.add_handler(tge.CommandHandler(
        "ann", ann_help_car,
        filters=tge.filters.Chat(CAR_GROUP_ID),
        has_args=False
        ))
    application.add_handler(tge.CommandHandler(
        "ann", ann_dms,
        filters=tge.filters.ChatType.PRIVATE,
        has_args=True
        ))
    application.add_handler(tge.CommandHandler(
        "ann", ann_dms_help,
        filters=tge.filters.ChatType.PRIVATE,
        has_args=False
        ))
    application.add_handler(tge.CommandHandler(
        "chn", chn_bike,
        filters=tge.filters.Chat(BIKE_GROUP_ID),
        has_args=False
        ))
    application.add_handler(tge.CommandHandler(
        "chn", chn_car,
        filters=tge.filters.Chat(CAR_GROUP_ID),
        has_args=False
        ))
    application.add_handler(tge.CommandHandler(
        "chn", chn_bike_single,
        filters=tge.filters.Chat(BIKE_GROUP_ID),
        has_args=True
        ))
    application.add_handler(tge.CommandHandler(
        "chn", chn_car_single,
        filters=tge.filters.Chat(CAR_GROUP_ID),
        has_args=True
        ))
    application.add_handler(tge.CommandHandler(
        "chn", chn_dms,
        filters=tge.filters.ChatType.PRIVATE,
        has_args=False
        ))
    application.add_handler(tge.CommandHandler("source", source))
    application.add_handler(tge.MessageHandler(
        (
            tge.filters.Chat(BIKE_GROUP_ID) &
            tge.filters.CaptionRegex("^/[aA][nN][nN]") &
            tge.filters.PHOTO
            ),img_bike
        )
    )
    application.add_handler(tge.MessageHandler(
        (
            tge.filters.Chat(CAR_GROUP_ID) &
            tge.filters.CaptionRegex("^/[aA][nN][nN]") &
            tge.filters.PHOTO
            ),
        img_car
        )
    )
    application.add_error_handler(error_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(
        allowed_updates=tg.Update.ALL_TYPES,
        drop_pending_updates=True
        )
    return

if __name__ == "__main__":
    main()
