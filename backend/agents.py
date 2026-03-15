# =============================================================
# agents.py — The three debate agents
# =============================================================
#
# PYTHON LESSON: This file teaches you:
# - How to read environment variables with os.getenv()
# - What a Class is and how __init__ works
# - What async/await means and why we need it
# - How generators work (yield)
# - How lists work (.append, slicing)
# - How try/except handles errors
# =============================================================

import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from prompts import (
    get_devil_prompt,
    get_advocate_prompt,
    get_judge_prompt,
    get_opening_line
)

# load_dotenv() reads your .env file and makes all the
# variables inside available via os.getenv()
# Must be called before any os.getenv() calls
load_dotenv()


# =============================================================
# PYTHON LESSON: os.getenv()
# --------------------------------------------------------------
# os.getenv("KEY", "default") reads a variable from your .env
# file. The second argument is a fallback if the key is missing.
# int() converts a string like "6" into the number 6.
# We do this because .env values are always strings.
# =============================================================

MODE          = os.getenv("MODE", "local")
OLLAMA_URL    = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL  = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")
MAX_ROUNDS    = int(os.getenv("MAX_DEBATE_ROUNDS", "6"))
MIN_WORDS     = int(os.getenv("MIN_WORDS_PER_TURN", "40"))
MAX_WORDS     = int(os.getenv("MAX_WORDS_PER_TURN", "120"))


# =============================================================
# PYTHON LESSON: Classes
# --------------------------------------------------------------
# A class is a blueprint. Think of it like a cookie cutter —
# the class is the shape, each object you create is a cookie.
#
# __init__ is the constructor — it runs automatically when you
# create a new object: client = LLMClient()
#
# self refers to the specific object being used. It's always
# the first parameter of any method but you never pass it
# manually — Python does that automatically.
# =============================================================

class LLMClient:
    """
    Talks to either Ollama (local) or Groq (cloud)
    depending on the MODE setting in your .env file.
    """

    def __init__(self):
        self.mode = MODE

        if self.mode == "cloud":
            from groq import Groq
            self.client = Groq(api_key=GROQ_API_KEY)
            self.model  = "llama-3.1-8b-instant"
        else:
            import ollama
            self.client = ollama
            self.model  = OLLAMA_MODEL


    async def chat(self, system_prompt: str, messages: list) -> str:
        """
        Sends a conversation to the LLM and returns the reply.

        PYTHON LESSON: async/await
        --------------------------------------------------------------
        Normally Python waits for each line to finish before moving
        to the next. Calling an LLM takes 3-10 seconds — during that
        time your server would be completely frozen for everyone else.

        async def marks a function as "asynchronous" — it can be
        paused while waiting and let other code run in the meantime.
        await means "start this, and pause here until it finishes,
        but let other things run while we wait."

        Any function that uses await must itself be async def.
        --------------------------------------------------------------

        Parameters:
            system_prompt — the personality instructions for the agent
            messages      — the conversation history so far

        Returns:
            The agent's reply as a plain string
        """

        # Put system prompt first, then the conversation history
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        # PYTHON LESSON: try/except
        # try:   run this code
        # except SomeError as e:   if that error happens, run this instead
        # This prevents your whole app from crashing on one bad LLM call
        try:
            if self.mode == "cloud":
                # asyncio.to_thread() runs a blocking (non-async) function
                # in a separate thread so it doesn't freeze everything
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=full_messages,
                    max_tokens=300,
                    temperature=0.85,
                )
                return response.choices[0].message.content.strip()
            else:
                response = await asyncio.to_thread(
                    self.client.chat,
                    model=self.model,
                    messages=full_messages,
                    options={"temperature": 0.85, "num_predict": 300},
                )
                return response["message"]["content"].strip()

        except Exception as e:
            print(f"LLM error: {e}")
            return "..."


# =============================================================
# The DebateSession — runs one complete debate
# =============================================================

class DebateSession:
    """
    Manages one complete debate between The Devil and The Advocate,
    with The Judge watching and ultimately deciding the winner.

    How to use it:
        session = DebateSession(topic="Is AI good for humanity?")
        async for event in session.run():
            print(event)
    """

    def __init__(self, topic: str):
        # PYTHON LESSON: Instance variables
        # self.xxx stores a value ON this specific object.
        # Every method in this class can access it via self.xxx
        self.topic      = topic
        self.llm        = LLMClient()
        self.history    = []        # list — stores every message so far
        self.round      = 0
        self.max_rounds = MAX_ROUNDS

        # Build the prompts once and reuse them
        self.devil_prompt    = get_devil_prompt(topic, MIN_WORDS, MAX_WORDS)
        self.advocate_prompt = get_advocate_prompt(topic, MIN_WORDS, MAX_WORDS)
        self.judge_prompt    = get_judge_prompt(topic)

        # Track word counts to detect when an agent is struggling
        self.devil_word_counts    = []
        self.advocate_word_counts = []


    async def run(self):
        """
        Runs the full debate from start to finish.

        PYTHON LESSON: yield (generators)
        --------------------------------------------------------------
        A normal function returns ONE value and exits.
        A generator function uses `yield` to produce many values
        one at a time — the caller gets each value as it's produced,
        without waiting for the whole function to finish.

        This is perfect for our debate because we want the browser
        to receive each message the moment it's ready, not wait for
        the entire debate to finish.

        async for event in session.run():   ← reads each yielded value
        --------------------------------------------------------------
        """

        # --- Opening lines ---
        devil_open    = get_opening_line("devil", self.topic)
        advocate_open = get_opening_line("advocate", self.topic)

        # yield sends this value to whoever is listening
        yield self._make_event("opening", "devil", devil_open)
        self._save(devil_open, "devil")
        await asyncio.sleep(1.5)

        yield self._make_event("opening", "advocate", advocate_open)
        self._save(advocate_open, "advocate")
        await asyncio.sleep(1.5)

        # --- Debate rounds ---
        # PYTHON LESSON: range(1, 7) produces: 1, 2, 3, 4, 5, 6
        # The variable round_num takes each value in the loop
        for round_num in range(1, self.max_rounds + 1):
            self.round = round_num

            # Devil goes first on odd rounds (1,3,5)
            # Advocate goes first on even rounds (2,4,6)
            # % is modulo — gives the remainder after division
            # 1 % 2 = 1 (odd),  2 % 2 = 0 (even)
            if round_num % 2 != 0:
                first, second = "devil", "advocate"
            else:
                first, second = "advocate", "devil"

            # First speaker argues
            first_text = await self._get_reply(first)
            yield self._make_event("turn", first, first_text, round_num)
            await asyncio.sleep(0.8)

            # Other agent reacts with a quick emoji
            reaction = self._get_reaction(second, first_text)
            if reaction:
                yield self._make_event("reaction", second, reaction)
                await asyncio.sleep(0.5)

            # Second speaker counter-argues
            second_text = await self._get_reply(second)
            yield self._make_event("turn", second, second_text, round_num)
            await asyncio.sleep(0.8)

            # First agent reacts back
            reaction2 = self._get_reaction(first, second_text)
            if reaction2:
                yield self._make_event("reaction", first, reaction2)
                await asyncio.sleep(0.5)

            # Judge chimes in every 2nd round
            if round_num % 2 == 0:
                judge_line = await self._get_judge_comment()
                yield self._make_event("judge", "judge", judge_line, round_num)
                await asyncio.sleep(1.0)

        # --- Final verdict ---
        verdict = await self._get_verdict()
        winner  = self._find_winner(verdict)
        yield self._make_event("verdict", "judge", verdict, winner=winner)
        yield {"type": "done"}


    async def _get_reply(self, agent: str) -> str:
        """Gets one reply from Devil or Advocate."""

        # Build conversation history from this agent's point of view
        messages = self._build_history_for(agent)

        if agent == "devil":
            system = self.devil_prompt
            if self._is_struggling("devil"):
                system += "\n\nYou are running out of arguments. Get more aggressive. Find a completely new angle. Do NOT repeat yourself."
        else:
            system = self.advocate_prompt
            if self._is_struggling("advocate"):
                system += "\n\nYou are running out of arguments. Dig deeper! Find your strongest point yet. Do NOT give up or repeat yourself."

        reply = await self.llm.chat(system, messages)
        self._save(reply, agent)

        # Track word count for this agent
        word_count = len(reply.split())
        if agent == "devil":
            self.devil_word_counts.append(word_count)
        else:
            self.advocate_word_counts.append(word_count)

        return reply


    async def _get_judge_comment(self) -> str:
        """Gets a short one-liner from the Judge."""
        messages = self._build_history_for("judge")
        messages.append({
            "role": "user",
            "content": "React to the debate so far with ONE very short message. Max 12 words. Be dry and observational."
        })
        return await self.llm.chat(self.judge_prompt, messages)


    async def _get_verdict(self) -> str:
        """Gets the Judge's final verdict."""
        messages = self._build_history_for("judge")
        messages.append({
            "role": "user",
            "content": (
                "The debate is over. Give your final verdict. "
                "Who won and why? Score both sides out of 10. "
                "Roast the loser, praise the winner. "
                "End with: Court adjourned. — The Judge ⚖️"
            )
        })
        return await self.llm.chat(self.judge_prompt, messages)


    def _build_history_for(self, agent: str) -> list:
        """
        Builds the message history formatted for the LLM.

        PYTHON LESSON: List comprehensions
        --------------------------------------------------------------
        Instead of writing a loop to build a list:
            result = []
            for entry in self.history:
                result.append(something)

        Python lets you write it in one line:
            result = [something for entry in self.history]

        Much more concise. We use a regular for loop here because
        the logic inside is complex enough to warrant clarity.
        --------------------------------------------------------------
        """
        messages = []
        for entry in self.history:
            # From this agent's perspective:
            # their own past messages = "assistant"
            # everyone else's messages = "user"
            if entry["agent"] == agent:
                role = "assistant"
            else:
                role = "user"

            messages.append({
                "role": role,
                "content": f"[{entry['agent'].upper()}]: {entry['text']}"
            })
        return messages


    def _save(self, text: str, agent: str):
        """Saves a message to the shared debate history."""
        # PYTHON LESSON: .append() adds an item to the end of a list
        self.history.append({"text": text, "agent": agent})


    def _is_struggling(self, agent: str) -> bool:
        """
        Returns True if an agent's recent messages are getting shorter
        — a sign they're running out of good arguments.

        PYTHON LESSON: List slicing with negative indices
        counts[-3:] means "give me the last 3 items in the list"
        Negative indices count from the END of the list:
            counts[-1]  = last item
            counts[-2]  = second to last
            counts[-3:] = last 3 items as a new list
        """
        counts = self.devil_word_counts if agent == "devil" else self.advocate_word_counts

        # Not enough data yet to judge
        if len(counts) < 3:
            return False

        recent = counts[-3:]   # last 3 word counts

        # all() returns True only if every item in the list is True
        # Here: True only if ALL recent messages were short
        return all(c < MIN_WORDS + 10 for c in recent)


    def _get_reaction(self, agent: str, other_text: str) -> str:
        """Returns a quick emoji reaction. No LLM call — keeps it fast."""

        # .lower() converts string to lowercase for easier matching
        text = other_text.lower()

        if agent == "devil":
            if any(w in text for w in ["research", "study", "proven", "data", "science"]):
                return "😂 ok professor"
            elif any(w in text for w in ["amazing", "incredible", "revolutionar"]):
                return "💀"
            elif any(w in text for w in ["people", "society", "world"]):
                return "🙄"
        else:
            if any(w in text for w in ["disaster", "terrible", "failed", "worst"]):
                return "😭 here we go again"
            elif any(w in text for w in ["never", "impossible", "always fails"]):
                return "that's just not true!!"
            elif any(w in text for w in ["actually", "technically", "well"]):
                return "👀"

        return ""


    def _find_winner(self, verdict: str) -> str:
        """Figures out who won from the verdict text."""

        # .lower() so we catch "Devil wins" and "devil wins" equally
        text = verdict.lower()

        devil_score    = text.count("devil wins") + text.count("winner: devil") + text.count("devil takes")
        advocate_score = text.count("advocate wins") + text.count("winner: advocate") + text.count("advocate takes")

        if devil_score > advocate_score:
            return "devil"
        elif advocate_score > devil_score:
            return "advocate"
        else:
            return "draw"


    def _make_event(self, type: str, agent: str, text: str,
                    round_num: int = 0, winner: str = "") -> dict:
        """
        Builds a consistently shaped event dictionary.

        PYTHON LESSON: Default parameter values
        def fn(x, y=0) — y is optional, defaults to 0 if not passed.
        You only need to pass round_num and winner when you have them.
        """
        event = {
            "type":      type,
            "agent":     agent,
            "text":      text,
            "timestamp": datetime.now().strftime("%I:%M %p"),
        }
        if round_num:
            event["round"] = round_num
        if winner:
            event["winner"] = winner
        return event