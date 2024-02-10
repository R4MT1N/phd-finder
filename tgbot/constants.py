import os

CHANNEL_CHAT_ID = os.getenv('TG_CHANNEL_ID')
TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')

WATCH_CHANNEL_POSITION_INLINE = 'watch_channel_position'
REMOVE_CHANNEL_POSITION_INLINE = 'remove_channel_position'
MY_ONGOING_POSITIONS_INLINE = 'my_ongoing_positions'
MY_EXPIRED_POSITIONS_INLINE = 'my_expired_positions'
REMOVED_POSITIONS_INLINE = 'removed_positions'

UNDO_WATCH_POSITION_INLINE = 'unwatch_position'
UNDO_REMOVE_POSITION_INLINE = 'restore_position'
UNDO_UNWATCH_POSITION_INLINE = 'undo_unwatch_position'
UNDO_RESTORE_POSITION_INLINE = 'undo_restore_position'
CANCEL_INLINE = 'cancel'

UNWATCH_COMMAND = 'up'
# REMOVE_COMMAND = 'rp'
RESTORE_COMMAND = 'rsp'

MY_ONGOING_POSITIONS_COMMAND = 'ongoing'
MY_EXPIRED_POSITIONS_COMMAND = 'expired'
REMOVED_POSITIONS_COMMAND = 'removed'

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
