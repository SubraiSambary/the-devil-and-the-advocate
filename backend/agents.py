# =============================================================
# agents.py — The three debate agents
# =============================================================

import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from prompts import (
    get_devil_prompt,
    get_advocate_prompt,
    get_judge_prompt,
    get_opening_prompt_devil,
    get_opening_prompt_advocate,
)

load_dotenv()

MODE         = os.getenv("MODE", "local")
OLLAMA_URL   = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MAX_ROUNDS   = int(os.getenv("MAX_DEBATE_ROUNDS", "5"))
MIN_WORDS    = int(os.getenv("MIN_WORDS_PER_TURN", "30"))
MAX_WORDS    = int(os.getenv("MAX_WORDS_PER_TURN", "80"))


class LLMClient:
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
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        try:
            if self.mode == "cloud":
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=full_messages,
                    max_tokens=150,        # reduced for speed
                    temperature=0.9,
                )
                return response.choices[0].message.content.strip()
            else:
                response = await asyncio.to_thread(
                    self.client.chat,
                    model=self.model,
                    messages=full_messages,
                    options={
                        "temperature": 0.9,
                        "num_predict": 150,    # reduced for speed
                        "num_ctx":     2048,   # smaller context = faster
                    },
                )
                return response["message"]["content"].strip()
        except Exception as e:
            print(f"LLM error: {e}")
            return "..."

    async def quick_chat(self, prompt: str) -> str:
        """Single-turn call — no history. Used for opening lines."""
        try:
            if self.mode == "cloud":
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=80,
                    temperature=1.0,
                )
                return response.choices[0].message.content.strip()
            else:
                response = await asyncio.to_thread(
                    self.client.chat,
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    options={
                        "temperature": 1.0,
                        "num_predict": 80,
                        "num_ctx":     512,
                    },
                )
                return response["message"]["content"].strip()
        except Exception as e:
            print(f"LLM error: {e}")
            return "..."


class DebateSession:
    def __init__(self, topic: str):
        self.topic      = topic
        self.llm        = LLMClient()
        self.history    = []
        self.round      = 0
        self.max_rounds = MAX_ROUNDS

        self.devil_prompt    = get_devil_prompt(topic, MIN_WORDS, MAX_WORDS)
        self.advocate_prompt = get_advocate_prompt(topic, MIN_WORDS, MAX_WORDS)
        self.judge_prompt    = get_judge_prompt(topic)

        self.devil_word_counts    = []
        self.advocate_word_counts = []


    async def run(self):
        # --- Dynamic opening lines ---
        devil_open = await self.llm.quick_chat(
            get_opening_prompt_devil(self.topic)
        )
        yield self._make_event("opening", "devil", devil_open)
        self._save(devil_open, "devil")
        await asyncio.sleep(0.5)

        advocate_open = await self.llm.quick_chat(
            get_opening_prompt_advocate(self.topic, devil_open)
        )
        yield self._make_event("opening", "advocate", advocate_open)
        self._save(advocate_open, "advocate")
        await asyncio.sleep(0.5)

        # --- Debate rounds ---
        for round_num in range(1, self.max_rounds + 1):
            self.round = round_num

            first, second = ("devil", "advocate") if round_num % 2 != 0 else ("advocate", "devil")

            # First speaker
            first_text = await self._get_reply(first)
            yield self._make_event("turn", first, first_text, round_num)
            await asyncio.sleep(0.3)

            # Quick emoji reaction
            reaction = self._get_reaction(second, first_text)
            if reaction:
                yield self._make_event("reaction", second, reaction)
                await asyncio.sleep(0.2)

            # Second speaker
            second_text = await self._get_reply(second)
            yield self._make_event("turn", second, second_text, round_num)
            await asyncio.sleep(0.3)

            reaction2 = self._get_reaction(first, second_text)
            if reaction2:
                yield self._make_event("reaction", first, reaction2)
                await asyncio.sleep(0.2)

            # Judge every 2nd round
            if round_num % 2 == 0:
                judge_line = await self._get_judge_comment()
                yield self._make_event("judge", "judge", judge_line, round_num)
                await asyncio.sleep(0.3)

        # --- Final verdict ---
        verdict = await self._get_verdict()
        winner  = self._find_winner(verdict)
        yield self._make_event("verdict", "judge", verdict, winner=winner)
        yield {"type": "done"}


    async def _get_reply(self, agent: str) -> str:
        messages = self._build_history_for(agent)

        if agent == "devil":
            system = self.devil_prompt
            if self._is_struggling("devil"):
                system += "\n\nYou are losing ground. Get more aggressive. Find a brand new angle NOW."
        else:
            system = self.advocate_prompt
            if self._is_struggling("advocate"):
                system += "\n\nYou are losing ground. Dig deeper! Make your strongest point yet."

        reply = await self.llm.chat(system, messages)
        self._save(reply, agent)

        word_count = len(reply.split())
        if agent == "devil":
            self.devil_word_counts.append(word_count)
        else:
            self.advocate_word_counts.append(word_count)

        return reply


    async def _get_judge_comment(self) -> str:
        messages = self._build_history_for("judge")
        messages.append({
            "role":    "user",
            "content": "React in max 6 words. Be dry and observational. No sign-off."
        })
        return await self.llm.chat(self.judge_prompt, messages)


    async def _get_verdict(self) -> str:
        messages = self._build_history_for("judge")
        messages.append({
            "role":    "user",
            "content": (
                "Debate is over. Give your final verdict in 80-100 words. "
                "Who won? Score both sides out of 10 on arguments, evidence, comebacks. "
                "Roast the loser. Praise the winner. "
                "End with: Court adjourned. ⚖️  No name sign-off."
            )
        })
        return await self.llm.chat(self.judge_prompt, messages)


    def _build_history_for(self, agent: str) -> list:
        messages = []
        for entry in self.history:
            role = "assistant" if entry["agent"] == agent else "user"
            messages.append({
                "role":    role,
                "content": f"[{entry['agent'].upper()}]: {entry['text']}"
            })
        return messages


    def _save(self, text: str, agent: str):
        self.history.append({"text": text, "agent": agent})


    def _is_struggling(self, agent: str) -> bool:
        counts = self.devil_word_counts if agent == "devil" else self.advocate_word_counts
        if len(counts) < 3:
            return False
        recent = counts[-3:]
        return all(c < MIN_WORDS + 5 for c in recent)


    def _get_reaction(self, agent: str, other_text: str) -> str:
        text = other_text.lower()
        if agent == "devil":
            if any(w in text for w in ["research", "study", "proven", "data", "science"]):
                return "😂 ok professor"
            elif any(w in text for w in ["amazing", "incredible", "revolutionar", "wonderful"]):
                return "💀"
            elif any(w in text for w in ["society", "people", "world", "everyone"]):
                return "🙄"
        else:
            if any(w in text for w in ["disaster", "terrible", "failed", "worst", "broken"]):
                return "😭 here we go"
            elif any(w in text for w in ["never works", "impossible", "always fails"]):
                return "that's just not true!!"
            elif any(w in text for w in ["actually", "technically", "statistic"]):
                return "👀"
        return ""


    def _find_winner(self, verdict: str) -> str:
        text = verdict.lower()
        d = text.count("devil wins") + text.count("winner: devil") + text.count("devil takes")
        a = text.count("advocate wins") + text.count("winner: advocate") + text.count("advocate takes")
        if d > a:   return "devil"
        if a > d:   return "advocate"
        return "draw"


    def _make_event(self, type: str, agent: str, text: str,
                    round_num: int = 0, winner: str = "") -> dict:
        event = {
            "type":      type,
            "agent":     agent,
            "text":      text,
            "timestamp": datetime.now().strftime("%I:%M %p"),
        }
        if round_num: event["round"] = round_num
        if winner:    event["winner"] = winner
        return event