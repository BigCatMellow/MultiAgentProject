Here's a draft replacement paragraph for the specified markdown:

"HCOM messages contain an `intent` recorded in HCOM's database; however, MAP events and session replays do not store intent information. Agents should utilize `request`, `inform`, and `ack` messages, while measurement code must handle missing intents explicitly."

**Reasoning:** This revision removes the assertion that *every* hcom message carries an intent, aligning with TASK-202's findings regarding unset intents. It retains all critical guidance around agent messaging and measurement handling.
