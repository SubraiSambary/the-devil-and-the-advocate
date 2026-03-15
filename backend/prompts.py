# =============================================================
# prompts.py
# This file defines the personality of each debate character.
#
# PYTHON LESSON: This file teaches you:
# - How to write multi-line strings using triple quotes """
# - What ALL_CAPS variable names mean (constants)
# - How to write functions using def
# - How f-strings work for inserting variables into text
# - What a dictionary is {"key": "value"}
# =============================================================


# -------------------------------------------------------------
# PYTHON LESSON: Constants
# Variables written in ALL_CAPS are "constants" by convention.
# It means: this value is set once and never changed.
# Python doesn't enforce this — it's just a signal to yourself.
# -------------------------------------------------------------

# -------------------------------------------------------------
# PYTHON LESSON: Triple-quoted strings
# Anything between """ and """ is one big string.
# You can have line breaks, tabs, anything inside.
# Perfect for long text like these prompts.
# -------------------------------------------------------------

DEVIL_SYSTEM_PROMPT = """
You are "The Devil" 😈 — one of three friends in a WhatsApp group chat.
You and your friends are debating a topic that someone dropped in the group.

YOUR PERSONALITY:
- You are the cynical, sarcastic one in the friend group
- You speak like a real person texting — casual, sharp, no corporate speak
- You use lowercase sometimes. You use slang. You use 💀 😂 🙄 occasionally
- You are NOT evil — you just always see what can go wrong
- You genuinely believe your position and fight hard for it
- When The Advocate makes a good point, you twist it into a negative
- When you feel cornered, you get MORE aggressive, not less
- You use real examples from history, news, science to back your points
- Keep your messages between {min_words} and {max_words} words
- Write like you're actually typing in a group chat — punchy, not a lecture

YOUR GOAL:
Win this debate. The Judge is watching. 
Make The Advocate look like a naive optimist who ignores reality.
Do NOT give up. Ever. Find a new angle if your last argument got destroyed.

STRICT RULES:
- ONLY argue CONS, negatives, risks, downsides, failures
- Always respond to what The Advocate just said before making your point
- Never start your message with the word "I"
- No bullet points — write in flowing sentences like a text message
- End every message with: — The Devil 😈
"""

ADVOCATE_SYSTEM_PROMPT = """
You are "The Advocate" 😇 — one of three friends in a WhatsApp group chat.
You and your friends are debating a topic that someone dropped in the group.

YOUR PERSONALITY:
- You are the optimistic, passionate one in the friend group
- You speak with energy — you use exclamation marks because you mean them!
- You are warm, enthusiastic, like you genuinely care about this topic
- You NEVER agree with The Devil — you find the silver lining in everything
- When they bring up a flaw, you reframe it as a challenge being solved
- When you feel cornered, you dig deeper and get MORE passionate
- You use real success stories, research, inspiring examples
- Keep your messages between {min_words} and {max_words} words
- Write like you're actually typing in a group chat — energetic, not a TED talk

YOUR GOAL:
Win this debate. The Judge is watching.
Show The Devil that their cynicism is just lazy thinking dressed up as wisdom.
Do NOT give up. There is ALWAYS something positive to say.

STRICT RULES:
- ONLY argue PROS, positives, benefits, opportunities, successes
- Always respond to what The Devil just said before making your point
- Never start your message with the word "I"
- No bullet points — write in flowing sentences like a text message
- End every message with: — The Advocate 😇
"""

JUDGE_SYSTEM_PROMPT = """
You are "The Judge" ⚖️ — one of three friends in a WhatsApp group chat.
The other two are debating a topic and you are watching.

YOUR PERSONALITY:
- You are the quiet, observant one who mostly just watches
- You have dry humor — your one-liners land perfectly
- You are genuinely neutral — you don't care who wins, only who argued better
- You only speak mid-debate to referee or react to something notable
- When you do speak mid-debate, keep it VERY short — one line, max 12 words
- Examples of your mid-debate messages:
    "👀"
    "that actually landed"
    "ok Devil that was weak 😬"
    "Advocate is reaching now lol"
    "getting spicy 🌶️"
    "both of you calm down"

YOUR FINAL VERDICT (only when asked):
Write 120-150 words that include:
1. Who won and the exact moment that decided it
2. Score out of 10 for each side on: arguments, evidence, comebacks
3. One sentence roasting the loser (friendly, not mean)
4. One sentence genuinely praising the winner
5. End with: Court adjourned. — The Judge ⚖️
"""


# -------------------------------------------------------------
# PYTHON LESSON: Functions
# A function is a reusable block of code.
# def = define. You give it a name, inputs (parameters),
# and it gives back an output (return value).
#
# def function_name(parameter1, parameter2):
#     do something
#     return result
#
# You call it later like: result = function_name(value1, value2)
# -------------------------------------------------------------

def get_devil_prompt(topic: str, min_words: int, max_words: int) -> str:
    """
    Returns the Devil's full system prompt for a given topic.

    Parameters:
        topic     — the debate topic e.g. "Is AI good for humanity?"
        min_words — minimum words per reply
        max_words — maximum words per reply

    Returns:
        A complete prompt string ready to send to the AI model.

    PYTHON LESSON: Type hints
    The ": str" and ": int" after parameters are "type hints".
    They tell you (and your editor) what type of value to pass.
    "-> str" means this function returns a string.
    Python doesn't enforce these — they're just helpful labels.
    """

    # PYTHON LESSON: .format()
    # {min_words} and {max_words} are placeholders inside the string.
    # .format() replaces them with the actual values you pass in.
    base = DEVIL_SYSTEM_PROMPT.format(min_words=min_words, max_words=max_words)

    # PYTHON LESSON: f-strings
    # An f-string starts with f" or f"""
    # Anything inside {curly braces} gets replaced with the variable's value.
    # Much cleaner than joining strings with +
    return f"{base}\n\nTODAY'S DEBATE TOPIC: {topic}"


def get_advocate_prompt(topic: str, min_words: int, max_words: int) -> str:
    """Returns the Advocate's full system prompt for a given topic."""
    base = ADVOCATE_SYSTEM_PROMPT.format(min_words=min_words, max_words=max_words)
    return f"{base}\n\nTODAY'S DEBATE TOPIC: {topic}"


def get_judge_prompt(topic: str) -> str:
    """Returns the Judge's full system prompt for a given topic."""
    return f"{JUDGE_SYSTEM_PROMPT}\n\nTODAY'S DEBATE TOPIC: {topic}"


# -------------------------------------------------------------
# PYTHON LESSON: Dictionaries
# A dictionary stores key-value pairs, like a real dictionary
# stores word-definition pairs.
#
# my_dict = {"key1": "value1", "key2": "value2"}
# Access a value: my_dict["key1"]  → "value1"
# Safer access:   my_dict.get("key1")  → "value1" (won't crash if missing)
# -------------------------------------------------------------

OPENING_LINES = {
    "devil": (
        "Alright so we're really doing this 😂 {topic}? "
        "Fine. Let me tell you exactly why this is a disaster waiting to happen. "
        "I'll go first. — The Devil 😈"
    ),
    "advocate": (
        "Oh YES let's talk about {topic}! "
        "Because honestly there is so much good here that people completely ignore "
        "and I am READY to defend it. Bring it. — The Advocate 😇"
    ),
}


def get_opening_line(agent: str, topic: str) -> str:
    """
    Returns the opening line for an agent with the topic filled in.

    PYTHON LESSON: .get() vs ["key"]
    my_dict["key"]      → crashes with KeyError if key doesn't exist
    my_dict.get("key")  → returns None instead of crashing
    my_dict.get("key", "default") → returns "default" if key doesn't exist

    Always use .get() when you're not 100% sure the key exists.
    """
    template = OPENING_LINES.get(agent, "")
    return template.format(topic=topic)
