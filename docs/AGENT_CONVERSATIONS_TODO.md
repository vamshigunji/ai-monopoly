# 💬 Agent Conversations - Implementation Notes

## Current Status: ❌ Not Implemented

The UI has **Private Thoughts** and **Public Conversations** panels, but they currently show **"No thoughts yet..."** and **"No conversation yet..."** because the backend agents don't emit these events.

---

## Why They're Empty

### The Frontend is Ready ✅
- `ThoughtPanel.tsx` listens for `AGENT_THOUGHT` events
- `ConversationPanel.tsx` listens for `AGENT_SPOKE` events
- `gameStore.ts` has handlers for both event types

### The Backend Doesn't Emit Them ❌
- Agents never call `emit(EventType.AGENT_SPOKE, ...)`
- Agents never call `emit(EventType.AGENT_THOUGHT, ...)`
- The event types exist in `types.py` but are never used

---

## How to Implement

### Option 1: Extract from AI Response (Easiest)

Modify the AI prompt to return thoughts and speech:

**Updated Prompt:**
```
Respond with JSON:
{
  "decision": "buy" or "pass",
  "private_thought": "Your internal reasoning (not visible to others)",
  "public_statement": "What you say out loud to other players (optional)"
}
```

**Updated Agent Code:**
```python
# backend/src/monopoly/agents/openai_agent.py

async def make_decision(self, game_view, decision_context):
    prompt = await self._build_base_prompt(game_view, decision_context)
    response = await self.client.chat.completions.create(...)
    content = response.choices[0].message.content
    decision = self._parse_response(content)

    # Extract and emit thoughts
    if "private_thought" in decision:
        self._emit_thought(decision["private_thought"])

    # Extract and emit public speech
    if "public_statement" in decision and decision["public_statement"]:
        self._emit_speech(decision["public_statement"])

    return decision

def _emit_thought(self, thought: str):
    """Emit private thought event"""
    self._event_bus.emit(EventType.AGENT_THOUGHT, {
        "player_id": self.player_id,
        "thought": thought
    })

def _emit_speech(self, message: str):
    """Emit public speech event"""
    self._event_bus.emit(EventType.AGENT_SPOKE, {
        "player_id": self.player_id,
        "message": message
    })
```

### Option 2: Separate LLM Call (More Realistic)

Make a separate API call to generate personality-driven commentary:

```python
async def _generate_commentary(self, action_taken: str) -> dict:
    """Generate thoughts and speech based on action"""
    prompt = f"""
    You are {self.personality.name}.
    You just {action_taken}.

    Generate:
    1. A private thought (your internal strategic reasoning)
    2. A public statement (what you say to intimidate/negotiate with others)

    Return JSON:
    {{
      "private_thought": "...",
      "public_statement": "..."
    }}
    """

    response = await self.client.chat.completions.create(
        model=self.personality.model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,  # More creative for personality
    )

    return json.loads(response.choices[0].message.content)
```

### Option 3: Template-Based (Fastest, No Extra API Calls)

Use personality templates for common actions:

```python
SPEECH_TEMPLATES = {
    "The Shark": {
        "property_purchased": [
            "Another property in my empire. You're all going down.",
            "That's mine now. Want to trade? It'll cost you.",
            "Building my monopoly, one property at a time."
        ],
        "rent_paid": [
            "Fine, take your money. I'll get it back when you land on MY properties.",
            "Enjoy it while it lasts. I'm coming for you.",
        ]
    },
    "The Professor": {
        "property_purchased": [
            "According to my calculations, this property has a 67% ROI.",
            "Statistically optimal purchase. The expected value is positive.",
        ],
        "rent_paid": [
            "A mere $24. That's 2.8% of my liquid assets. Acceptable.",
            "The probability of this hurting my strategy is minimal.",
        ]
    },
    # ... etc for Hustler and Turtle
}

def _emit_templated_speech(self, action: str):
    templates = SPEECH_TEMPLATES.get(self.personality.name, {}).get(action, [])
    if templates:
        import random
        message = random.choice(templates)
        self._emit_speech(message)
```

---

## Recommended Approach

**For MVP: Option 1 (Extract from AI Response)**
- ✅ Simple to implement
- ✅ Authentic to each agent's personality
- ✅ No extra API calls
- ⚠️ Slightly longer responses

**For Production: Option 2 (Separate LLM Call)**
- ✅ More detailed and realistic
- ✅ Better role-playing
- ⚠️ Costs more (extra API calls)
- ⚠️ Slower (adds latency)

**For Low-Cost Testing: Option 3 (Templates)**
- ✅ Zero API cost
- ✅ Instant responses
- ⚠️ Repetitive after many games
- ⚠️ Less authentic

---

## Example Output

### Private Thought (Only visible when you select that agent)
```
💭 The Shark (T15):
"Tennessee is part of Orange - one of the best monopolies.
With $670 left, I can still survive a few bad rolls. Hustler
owns St. James, so I'll need to trade. But I have the cash
advantage now. Time to pressure them into a deal."
```

### Public Conversation (Visible to all)
```
🦈 The Shark (T15):
"Tennessee Avenue is MINE. Hustler, we need to talk about
St. James. I'm willing to trade... or I can just outbid you
on every auction from here on out. Your choice."
```

---

## Implementation Checklist

To add agent conversations:

- [ ] Choose implementation approach (Option 1, 2, or 3)
- [ ] Update AI prompt to request thoughts/speech
- [ ] Add `_emit_thought()` method to base agent class
- [ ] Add `_emit_speech()` method to base agent class
- [ ] Call emit methods after each decision
- [ ] Test events appear in WebSocket stream
- [ ] Verify frontend panels populate
- [ ] Adjust personality prompts for better role-playing
- [ ] Add rate limiting if using Option 2 (avoid API spam)

---

## Cost Impact

**Option 1 (Extract from response):**
- Cost: Same as current (just longer output tokens)
- ~10-20 extra tokens per decision
- Negligible cost increase

**Option 2 (Separate calls):**
- Cost: **2x current** (doubles API calls)
- Each turn: 2 calls instead of 1
- Significant cost increase (not recommended for testing)

**Option 3 (Templates):**
- Cost: **$0** (no API calls)
- Best for cost-conscious development

---

## Example Implementation (Option 1)

**File: `backend/src/monopoly/agents/openai_agent.py`**

```python
async def make_decision(self, game_view: GameView, decision_context: str):
    """Make a decision with thoughts and speech"""

    # Build prompt requesting thoughts and speech
    prompt = await self._build_base_prompt(game_view, decision_context)
    prompt += """

    In your response, include:
    {
      "decision": "your_action",
      "private_thought": "Your internal strategic reasoning (1-2 sentences)",
      "public_statement": "What you say out loud (optional, only if relevant)"
    }
    """

    # Get AI response
    response = await self.client.chat.completions.create(
        model=self.personality.model,
        messages=[{"role": "user", "content": prompt}],
        temperature=self.personality.temperature,
        max_tokens=300,
    )

    content = response.choices[0].message.content
    decision = self._parse_response(content)

    # Emit thought event
    if "private_thought" in decision:
        self._event_bus.emit(EventType.AGENT_THOUGHT, {
            "player_id": self.player_id,
            "thought": decision["private_thought"]
        })

    # Emit speech event (only if agent chose to speak)
    if decision.get("public_statement"):
        self._event_bus.emit(EventType.AGENT_SPOKE, {
            "player_id": self.player_id,
            "message": decision["public_statement"]
        })

    return decision
```

**Estimated time to implement: 30 minutes**

---

## Testing After Implementation

1. Start a new game
2. Watch the **Private Thoughts** panel - should populate with agent reasoning
3. Watch the **Public Conversations** panel - should show agent trash talk
4. Select different agents from dropdown - each should have unique thoughts
5. Events should be in character (Shark = aggressive, Professor = analytical, etc.)

---

## Future Enhancements

- **Negotiations:** Show trade proposals as conversations
- **Reactions:** Agents react to other players' moves
- **Game milestones:** Special messages when monopolies form, bankruptcies occur, etc.
- **Trash talk:** More colorful language during auctions and trades
- **Strategic hints:** Professor occasionally explains probability to the user

---

## Summary

**Current State:** Frontend ready ✅, Backend not emitting events ❌

**To Fix:** Add 10-15 lines of code to emit `AGENT_THOUGHT` and `AGENT_SPOKE` events after each AI decision.

**Recommended:** Start with **Option 1** (extract from AI response) for fastest implementation with minimal cost impact.
