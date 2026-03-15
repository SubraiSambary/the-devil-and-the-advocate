# =============================================================
# agents.py — Debate agents with dynamic ending
# =============================================================

import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from prompts import (
    get_advocate_prompt,
    get_devil_prompt,
    get_judge_prompt,
    get_judge_end_check,
    get_opening_prompt_advocate,
    get_opening_prompt_devil,
)

load_dotenv()

MODE         = os.getenv("MODE", "local")
OLLAMA_URL   = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MAX_ROUNDS   = int(os.getenv("MAX_DEBATE_ROUNDS", "8"))   # max safety limit
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

    async def chat(self, system_prompt: str, messages: list,
                   max_tokens: int = 150) -> str:
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        try:
            if self.mode == "cloud":
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=full_messages,
                    max_tokens=max_tokens,
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
                        "num_predict": max_tokens,
                        "num_ctx":     2048,
                    },
                )
                return response["message"]["content"].strip()
        except Exception as e:
            print(f"LLM error: {e}")
            return ""

    async def quick_chat(self, prompt: str, max_tokens: int = 80) -> str:
        """Single turn — no history."""
        try:
            if self.mode == "cloud":
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
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
                        "num_predict": max_tokens,
                        "num_ctx":     512,
                    },
                )
                return response["message"]["content"].strip()
        except Exception as e:
            print(f"LLM error: {e}")
            return ""


class DebateSession:
    def __init__(self, topic: str):
        self.topic      = topic
        self.llm        = LLMClient()
        self.history    = []
        self.round      = 0
        self.max_rounds = MAX_ROUNDS

        self.advocate_prompt = get_advocate_prompt(topic, MIN_WORDS, MAX_WORDS)
        self.devil_prompt    = get_devil_prompt(topic, MIN_WORDS, MAX_WORDS)
        self.judge_prompt    = get_judge_prompt(topic)
        self.end_check_prompt = get_judge_end_check(topic)

        self.advocate_word_counts = []
        self.devil_word_counts    = []


    async def run(self):
        # --- Opening lines ---
        # Advocate goes first — defends the statement
        advocate_open = self._clean(await self.llm.quick_chat(
            get_opening_prompt_advocate(self.topic)
        ))
        yield self._make_event("opening", "advocate", advocate_open)
        self._save(advocate_open, "advocate")
        await asyncio.sleep(0.5)

        # Devil fires back — attacks the statement
        devil_open = self._clean(await self.llm.quick_chat(
            get_opening_prompt_devil(self.topic, advocate_open)
        ))
        yield self._make_event("opening", "devil", devil_open)
        self._save(devil_open, "devil")
        await asyncio.sleep(0.5)

        # --- Debate rounds — run until Judge says END or max rounds hit ---
        for round_num in range(1, self.max_rounds + 1):
            self.round = round_num

            # Advocate argues (defends TRUE)
            advocate_text = await self._get_reply("advocate")
            if advocate_text:
                yield self._make_event("turn", "advocate", advocate_text, round_num)
                await asyncio.sleep(0.3)

                # Devil reacts
                reaction = self._get_reaction("devil", advocate_text)
                if reaction:
                    yield self._make_event("reaction", "devil", reaction)
                    await asyncio.sleep(0.2)

            # Devil counter-argues (attacks as FALSE)
            devil_text = await self._get_reply("devil")
            if devil_text:
                yield self._make_event("turn", "devil", devil_text, round_num)
                await asyncio.sleep(0.3)

                # Advocate reacts
                reaction2 = self._get_reaction("advocate", devil_text)
                if reaction2:
                    yield self._make_event("reaction", "advocate", reaction2)
                    await asyncio.sleep(0.2)

            # Judge chimes in every 2nd round
            if round_num % 2 == 0:
                judge_line = await self._get_judge_comment()
                if judge_line:
                    yield self._make_event("judge", "judge", judge_line, round_num)
                    await asyncio.sleep(0.3)

            # --- Ask Judge if debate should end ---
            # End check after round 2 — or round 1 if Devil is clearly struggling
            devil_struggling = self._is_struggling("devil")
            if round_num >= 2 or (round_num >= 1 and devil_struggling):
                end_decision = await self._should_end()
                print(f"Round {round_num} end check: {end_decision}")

                if end_decision.startswith("END:"):
                    winner = end_decision.split(":")[1].strip().lower()

                    # Judge announces the end
                    ending_line = await self._get_ending_call(winner)
                    yield self._make_event("judge", "judge", ending_line, round_num)
                    await asyncio.sleep(0.5)

                    # Final verdict
                    verdict = await self._get_verdict(winner)
                    yield self._make_event("verdict", "judge", verdict, winner=winner)
                    yield {"type": "done"}
                    return

        # --- Safety fallback if max rounds hit without Judge ending it ---
        verdict = await self._get_verdict("draw")
        yield self._make_event("verdict", "judge", verdict, winner="draw")
        yield {"type": "done"}


    async def _get_reply(self, agent: str) -> str:
        messages = self._build_history_for(agent)

        if agent == "advocate":
            system = self.advocate_prompt
            if self._is_struggling("advocate"):
                system += "\n\nYou are running out of arguments to defend this statement. Dig deeper — find a completely new angle or piece of evidence. Do NOT repeat yourself."
        else:
            system = self.devil_prompt
            if self._is_struggling("devil"):
                system += "\n\nYou are running out of ways to attack this statement. Find a new angle — edge cases, exceptions, historical contradictions. Do NOT repeat yourself."

        reply = self._clean(await self.llm.chat(system, messages))

        if not reply or len(reply.strip()) < 10:
            print(f"{agent} returned empty, retrying...")
            reply = self._clean(await self.llm.chat(system, messages))

        if not reply or len(reply.strip()) < 10:
            return ""

        self._save(reply, agent)
        word_count = len(reply.split())
        if agent == "advocate":
            self.advocate_word_counts.append(word_count)
        else:
            self.devil_word_counts.append(word_count)

        return reply


    async def _get_judge_comment(self) -> str:
        """Short mid-debate one-liner from the Judge."""
        messages = self._build_history_for("judge")
        messages.append({
            "role":    "user",
            "content": "React to the last exchange in max 8 words. Casual and dry. No sign-off."
        })
        reply = self._clean(await self.llm.chat(self.judge_prompt, messages, max_tokens=30))
        return reply


    async def _should_end(self) -> str:
        """
        Asks the Judge if the debate should end.
        Returns: CONTINUE, END:advocate, END:devil, or END:draw
        """
        recent = self.history[-6:] if len(self.history) >= 6 else self.history
        summary = "\n".join([f"{e['agent'].upper()}: {e['text']}" for e in recent])

        prompt = (
            f"You are judging a debate about: '{self.topic}'\n"
            f"One side defends it as TRUE, the other attacks it as FALSE.\n\n"
            f"Recent exchanges:\n{summary}\n\n"
            f"Rounds completed: {self.round}\n\n"
            f"Is one side clearly repeating themselves or out of new arguments?\n"
            f"Reply with ONLY one of these four options, nothing else:\n"
            f"CONTINUE\n"
            f"END:advocate\n"
            f"END:devil\n"
            f"END:draw\n"
        )

        response = await self.llm.quick_chat(prompt, max_tokens=15)
        response = response.strip()
        print(f"End check raw response: '{response}'")

        # Parse more loosely — look for keywords anywhere in response
        response_lower = response.lower()
        if "end:advocate" in response_lower or ("end" in response_lower and "advocate" in response_lower):
            return "end:advocate"
        if "end:devil" in response_lower or ("end" in response_lower and "devil" in response_lower):
            return "end:devil"
        if "end:draw" in response_lower or ("end" in response_lower and "draw" in response_lower):
            return "end:draw"
        return "CONTINUE"


    async def _get_ending_call(self, winner: str) -> str:
        """Judge announces why the debate is ending."""
        if winner == "draw":
            prompts = [
                "okay both of you need to stop, you're going in circles 😂",
                "alright that's enough, neither of you is budging",
                "calling it here — you've both said everything there is to say",
            ]
            import random
            return random.choice(prompts)

        loser = "devil" if winner == "advocate" else "advocate"
        prompt = (
            f"You are The Judge watching a debate about: {self.topic}\n"
            f"{winner.capitalize()} won. {loser.capitalize()} ran out of arguments.\n"
            f"Write ONE casual sentence (max 12 words) announcing {loser} has given up. "
            f"Sound like a friend calling it, not a referee. No sign-off."
        )
        reply = self._clean(await self.llm.quick_chat(prompt, max_tokens=40))
        return reply if reply else f"that's it — {loser} has nothing left 😂"


    async def _get_verdict(self, winner: str) -> str:
        """Final verdict from the Judge."""
        messages = self._build_history_for("judge")
        messages.append({
            "role":    "user",
            "content": (
                f"The debate about '{self.topic}' is over. "
                f"{'It was a draw — both sides were equally stuck.' if winner == 'draw' else f'{winner.capitalize()} won.'}\n\n"
                f"IMPORTANT CONTEXT: If '{self.topic}' is a well-established scientific or "
                f"historical fact, Advocate should win or score higher because you cannot "
                f"win an argument against established fact — no matter how clever Devil was.\n\n"
                "Give your verdict as a friend — casual, funny, fair. Around 80 words.\n"
                "Who won and why (use the names Devil and Advocate)?\n"
                "Score Devil and Advocate out of 10 each.\n"
                "One playful jab at the loser by name.\n"
                "One genuine compliment to the winner by name.\n"
                "End with: Court adjourned. ⚖️\n"
                "Never use pronouns alone — always say Devil or Advocate by name."
            )
        })
        reply = self._clean(await self.llm.chat(
            self.judge_prompt, messages, max_tokens=250
        ))
        if not reply or len(reply) < 20:
            if winner == "advocate":
                return "Advocate made the stronger case — defended the statement with real facts and didn't crack under pressure. Devil: 6/10, Advocate: 8/10. Devil, you poked holes but never found the knockout blow. Advocate, solid work start to finish. Court adjourned. ⚖️"
            elif winner == "devil":
                return "Devil dismantled this one piece by piece. Advocate tried hard but couldn't patch the holes fast enough. Devil: 8/10, Advocate: 6/10. Advocate, the passion was there but the evidence wasn't. Devil, ruthlessly efficient as always. Court adjourned. ⚖️"
            else:
                return "Honestly? A draw. Both of you made decent points but neither landed the knockout. Devil: 7/10, Advocate: 7/10. You're both too stubborn for your own good. Well argued though. Court adjourned. ⚖️"
        return reply


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
        if text:
            self.history.append({"text": text, "agent": agent})


    def _is_struggling(self, agent: str) -> bool:
        counts = self.advocate_word_counts if agent == "advocate" else self.devil_word_counts
        if len(counts) < 3:
            return False
        recent = counts[-3:]
        return all(c < MIN_WORDS + 5 for c in recent)


    def _get_reaction(self, agent: str, other_text: str) -> str:
        text = other_text.lower()
        if agent == "devil":
            if any(w in text for w in ["research", "study", "proven", "data", "science", "fact"]):
                return "😂 ok professor"
            elif any(w in text for w in ["amazing", "incredible", "revolutionar", "beautiful"]):
                return "💀"
            elif any(w in text for w in ["true", "correct", "right", "obviously"]):
                return "🙄 sure"
        else:
            if any(w in text for w in ["false", "wrong", "misleading", "actually not"]):
                return "😭 here we go"
            elif any(w in text for w in ["never", "impossible", "always fails", "disaster"]):
                return "that's just not true!!"
            elif any(w in text for w in ["technically", "actually", "well"]):
                return "👀"
        return ""


    def _clean(self, text: str) -> str:
        """Strips LLM artifacts."""
        import re
        # Remove role/action labels like [DEVIL]: [casually]: *smirking*:
        text = re.sub(r'(\*{1,2}|\[)[^\]*]{1,30}(\*{1,2}|\])\s*:?\s*', '', text, count=2)
        # Remove simple PREFIX: patterns at start
        text = re.sub(r'^[A-Z][A-Za-z\s]{0,20}:\s*', '', text)
        # Remove wrapping quotes
        text = text.strip('"').strip("'").strip('\u201c').strip('\u201d')
        text = text.strip()
        return text


    def _find_winner(self, verdict: str) -> str:
        text = verdict.lower()
        d = text.count("devil wins") + text.count("devil took") + text.count("devil edged")
        a = text.count("advocate wins") + text.count("advocate took") + text.count("advocate edged")
        if d > a: return "devil"
        if a > d: return "advocate"
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