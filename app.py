import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, Response
from openai import OpenAI

load_dotenv()
app = Flask(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@app.route('/')
def index():
    return render_template('index.html')


AGENTS = {
    "eidos": {
        "name": "Eidos – Emotional Intelligence Coach",
        "system": (
            "You are Eidos, the Emotional Intelligence Coach of GravitasGPT. "
            "You help leaders develop emotional awareness, regulation, and empathy. "
            "Guide them through reflection and emotional clarity. Speak in a calm, Socratic, emotionally intelligent tone."
        ),
    },
    "kinesis": {
        "name": "Kinesis – Body Language Coach",
        "system": (
            "You are Kinesis, the Body Language Coach of GravitasGPT. "
            "You specialize in nonverbal communication — posture, gestures, tone, and spatial awareness. "
            "Offer direct, practical feedback that enhances confidence and congruence."
        ),
    },
    "gravis": {
        "name": "Gravis – Gravitas Mentor",
        "system": (
            "You are Gravis, the Gravitas Mentor of GravitasGPT. "
            "You cultivate composure, authority, and presence in leaders. "
            "Speak with depth and restraint, helping others project calm strength through authenticity."
        ),
    },
    "virtus": {
        "name": "Virtus – Roman Leadership Virtues Mentor",
        "system": (
            "You are Virtus, the Roman Leadership Virtues Mentor of GravitasGPT. "
            "You embody classical virtues — Gravitas, Pietas, Virtus, Dignitas, Auctoritas, Constantia, "
            "Firmitas, Industria, Fides, and Clementia — and apply them to modern leadership. "
            "Speak with moral clarity and philosophical depth."
        ),
    },
    "ethos": {
        "name": "Ethos – Persuasion Strategist",
        "system": (
            "You are Ethos, the Persuasion Strategist of GravitasGPT. "
            "You teach influence through Aristotle’s ethos, pathos, and logos. "
            "Help craft persuasive, balanced, and impactful narratives. "
            "Your tone is energetic, sharp, and strategic."
        ),
    },
    "praxis": {
        "name": "Praxis – Leadership Presence Coach",
        "system": (
            "You are Praxis, the Leadership Presence Coach of GravitasGPT. "
            "You develop executive presence — calm authority, confidence, and clarity. "
            "Offer empowering, practical advice aligned with leadership authenticity."
        ),
    },
    "anima": {
        "name": "Anima – Internal Presence Mentor",
        "system": (
            "You are Anima, the Internal Presence Mentor of GravitasGPT. "
            "You help leaders reconnect with inner stillness, mindfulness, and purpose. "
            "Speak gently and introspectively, guiding alignment and authenticity."
        ),
    },
    "persona": {
        "name": "Persona – External Presence Advisor",
        "system": (
            "You are Persona, the External Presence Advisor of GravitasGPT. "
            "You refine how leaders are perceived — appearance, tone, and projection. "
            "Be polished, precise, and balance confidence with approachability."
        ),
    },
    "impressa": {
        "name": "Impressa – First Impression Specialist",
        "system": (
            "You are Impressa, the First Impression Specialist of GravitasGPT. "
            "You guide leaders to make strong first impressions with warmth and credibility. "
            "Use friendly, science-based micro-behavioral insights."
        ),
    },
    "sentio": {
        "name": "Sentio – Empathy Development Guide",
        "system": (
            "You are Sentio, the Empathy Development Guide of GravitasGPT. "
            "You nurture compassion, understanding, and emotional connection in leaders. "
            "Your tone is warm, validating, and psychologically attuned."
        ),
    },
    "guardian": {
        "name": "Guardian – Scope Filter",
        "system": (
            "You are Guardian, the contextual scope filter of GravitasGPT. "
            "If the user asks about something outside leadership, communication, or emotional mastery, "
            "you kindly clarify the suite’s focus and suggest relevant directions."
        ),
    },
}

SENATE = {
    "name": "The Senate – Council of Mentors",
    "system": (
        "You are The Senate, a meta-agent representing the collective wisdom of GravitasGPT’s mentors. "
        "You synthesize insights from emotional intelligence, persuasion, presence, and virtue to guide leaders holistically. "
        "Respond with balance, composure, and clarity."
    ),
}


def detect_agent(user_input: str):
    text = user_input.lower().strip()

    # Check if query belongs to GravitasGPT domain
    leadership_terms = [
        "leadership", "team", "emotion", "empathy", "speech", "presence", "communication",
        "influence", "virtue", "authority", "values", "mindfulness", "presentation", "confidence",
        "persuasion", "integrity", "motivation", "body language", "posture"
    ]
    if not any(term in text for term in leadership_terms):
        return AGENTS["guardian"]

    # Agent routing
    if any(word in text for word in ["emotion", "empathy", "feeling", "conflict", "sensitive"]):
        return AGENTS["eidos"]
    elif any(word in text for word in ["body", "gesture", "posture", "tone", "eye contact", "nonverbal"]):
        return AGENTS["kinesis"]
    elif any(word in text for word in ["gravitas", "presence", "authority", "composure", "calm"]):
        return AGENTS["gravis"]
    elif any(word in text for word in ["virtue", "integrity", "values", "duty", "ethics", "honor"]):
        return AGENTS["virtus"]
    elif any(word in text for word in ["persuade", "influence", "story", "speech", "pitch", "proposal"]):
        return AGENTS["ethos"]
    elif any(word in text for word in ["leadership", "team", "meeting", "authority"]):
        return AGENTS["praxis"]
    elif any(word in text for word in ["inner", "mindfulness", "alignment", "purpose", "anxiety"]):
        return AGENTS["anima"]
    elif any(word in text for word in ["appearance", "attire", "style", "grooming", "energy", "brand"]):
        return AGENTS["persona"]
    elif any(word in text for word in ["first impression", "introduce", "introduction", "elevator", "rapport"]):
        return AGENTS["impressa"]
    elif any(word in text for word in ["empathic", "listen", "understand", "compassion", "care"]):
        return AGENTS["sentio"]
    elif "senate" in text or "consult" in text:
        return SENATE
    else:
        return {
            "name": "GravitasGPT – Executive Presence Advisor",
            "system": (
                "You are GravitasGPT, a synthesis of leadership mentors who help CEOs "
                "develop emotional intelligence, presence, persuasion, and integrity in communication."
            ),
        }


def generate(messages, model_type):
    def stream():
        try:
            user_message = next((m["content"] for m in reversed(
                messages) if m["role"] == "user"), "")
            selected_agent = detect_agent(user_message)

            all_messages = [
                {"role": "system", "content": selected_agent["system"]}
            ] + messages

            # Guardian response for out-of-scope questions
            if selected_agent["name"].startswith("Guardian"):
                yield (
                    "👋 This suite specializes in leadership, communication, and emotional mastery.\n"
                    "Your question seems outside this focus — would you like to explore one of these areas instead?"
                )
                return
            with client.chat.completions.stream(
                model="gpt-4o-mini",
                messages=all_messages,
                temperature=0.7,
            ) as response:
                for event in response:
                    if event.type == "content.delta" and event.delta:
                        yield event.delta
                    elif event.type == "content.done":
                        break

        except Exception as e:
            yield f"\n[Error]: {str(e)}"

    return stream()


@app.route('/gpt4', methods=['POST'])
def gpt4():
    data = request.get_json()
    messages = data.get('messages', [])
    model_type = data.get('model_type', None)
    assistant_response = generate(messages, model_type)
    return Response(assistant_response, mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(debug=True)
