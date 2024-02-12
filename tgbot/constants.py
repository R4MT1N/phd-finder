import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent.joinpath('.env'), override=True)

CHANNEL_CHAT_ID = os.getenv('TG_CHANNEL_ID')
TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')

COMMAND_SEP = '+'

# Inline Commands
WATCH_CHANNEL_POSITION_INLINE = 'watch_channel_position'
REMOVE_CHANNEL_POSITION_INLINE = 'remove_channel_position'
UNIVERSITY_POSITIONS_INLINE = 'university_positions'
UNIVERSITIES_INLINE = 'universities'
MY_ONGOING_POSITIONS_INLINE = 'my_ongoing_positions'
MY_EXPIRED_POSITIONS_INLINE = 'my_expired_positions'
REMOVED_POSITIONS_INLINE = 'removed_positions'
UNDO_WATCH_POSITION_INLINE = 'unwatch_position'
UNDO_REMOVE_POSITION_INLINE = 'restore_position'
UNDO_UNWATCH_POSITION_INLINE = 'undo_unwatch_position'
UNDO_RESTORE_POSITION_INLINE = 'undo_restore_position'
UPCOMING_WEEK_DEADLINES_INLINE = 'week_deadlines'
UPCOMING_DAY_DEADLINES_INLINE = 'day_deadlines'
CANCEL_INLINE = 'cancel'

# Button Label
UNDO_BTN = "⬅️ Undo"
NVM_BTN = "I'm OK"  # NVM = Never mind
REFRESH_BTN = '🔄 Refresh'
NEXT_BTN = '➡️ Next'
PREVIOUS_BTN = '⬅️ Previous'
WATCH_BTN = "🔔 Watch"
REMOVE_BTN = "❌ Remove"

# Info & Error Texts
ONLY_REGISTERED_USER_ALLOWED = 'First, you have to be a registered user'
ONLY_ADMINS_ALLOWED = 'Only admins can do that'
POSITION_ID_INVALID = 'The position id "{}" is invalid'
UNIVERSITY_ID_INVALID = 'The university id "{}" is invalid'
POSITION_UNWATCHED = 'Position "{}" is removed from watchlist'
POSITION_WATCHED = 'Position is added to watchlist'
POSITION_TITLE_WATCHED = 'Position "{}" is added to watchlist'
POSITION_ALREADY_IN_LIST = 'Position is already in watchlist'
POSITION_REMOVED = 'Position is removed'
POSITION_ALREADY_REMOVED = 'Position is already removed'
POSITION_RESTORED = 'Position "{}" is restored'
NOTHING_CHANGED = 'Nothing has changed'
EMPTY_UPCOMING_WEEK_DEADLINES = 'No deadline in the upcoming week'
EMPTY_UPCOMING_DAY_DEADLINES = 'No deadline in the upcoming day'

# Titles
UPCOMING_WEEK_DEADLINES_TITLE = 'Upcoming Week Deadlines'
UPCOMING_DAY_DEADLINES_TITLE = 'Upcoming Day Deadlines'
ONGOING_POSITIONS_TITLE = 'Watchlist'
EXPIRED_POSITIONS_TITLE = 'Expired Positions'
REMOVED_POSITIONS_TITLE = 'Removed Positions'

# Bot Commands
# REMOVE_COMMAND = 'rp'
WATCH_COMMAND = 'wp'
UNWATCH_COMMAND = 'uwp'
RESTORE_COMMAND = 'rsp'
UNIVERSITY_POSITIONS_COMMAND = 'unip'
ONGOING_POSITIONS_COMMAND = 'Watchlist'
EXPIRED_POSITIONS_COMMAND = 'Expired Positions'
REMOVED_POSITIONS_COMMAND = 'Removed Positions'
UNIVERSITIES_COMMAND = 'Universities'

start_funny_sentences = [
    "Alright, it's time to add some positions to your list, please!",
    "Enough procrastinating! Add some positions to your list now, please!",
    "That's the limit! Please go and add some positions to your list.",
    "We've reached the point where you need to add some positions to your list, now.",
    "No more delays! It's time to add some positions to your list, please.",
    "We've had sufficient time; now, please add some positions to your list.",
    "Enough dilly-dallying! Go add some positions to your list, please!",
    "We're at the end of the line. Add some positions to your list, please!",
    "That's it! Time to add some positions to your list without further delay.",
    "We've come to a stopping point. Please add some positions to your list now."
]
