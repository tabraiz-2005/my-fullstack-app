import os
from flask import Flask, render_template, request, Response
from openai import OpenAI
from dotenv import load_dotenv

# Load .env file for local development
load_dotenv()

# Get the API key from the environment
API_KEY = os.environ.get("OPENAI_API_KEY")

# If the key is not found, stop the app and print a clear error
if not API_KEY:
    raise ValueError("OPENAI_API_KEY is not set. Please check your .env file or Render environment variables.")

app = Flask(__name__)

# Initialize the client with the key
client = OpenAI(api_key=API_KEY)

# This route serves your main HTML file
@app.route('/')
def index():
    return render_template('index.html')

# This is the /static/styles.css and /static/main.js
# Flask handles this automatically from the 'static' folder.

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

    # --- UPDATED KEYWORDS ---
    # Check if query belongs to GravitasGPT domain
    leadership_terms = [
        "leader", "leadership", "team", "emotion", "empathy", "speech", "presence", 
        "communicate", "communication", "influence", "virtue", "authority", "values", 
        "mindfulness", "presentation", "confidence", "persuasion", "integrity", 
        "motivation", "body language", "posture", "feeling", "anxiety", "stress"
    ]
    # Use 'any' to see if any term is a substring of the user's input
    if not any(term in text for term in leadership_terms):
        print(f"DEBUG: Query '{text}' is OFF-TOPIC. Routing to Guardian.") # DEBUG LOG
        return AGENTS["guardian"]

    # --- UPDATED KEYWORDS ---
    # Agent routing (This is just a default router, you can make this smarter)
    if any(word in text for word in ["emotion", "empathy", "feeling", "conflict", "sensitive", "stress"]):
        return AGENTS["eidos"]
    elif any(word in text for word in ["body", "gesture", "posture", "tone", "eye contact", "nonverbal"]):
        return AGENTS["kinesis"]
    elif any(word in text for word in ["gravitas", "presence", "authority", "composure", "calm"]):
        return AGENTS["gravis"]
    elif any(word in text for word in ["virtue", "integrity", "values", "duty", "ethics", "honor"]):
        return AGENTS["virtus"]
    elif any(word in text for word in ["persuade", "influence", "story", "speech", "pitch", "proposal"]):
        return AGENTS["ethos"]
    elif any(word in text for word in ["leader", "leadership", "team", "meeting", "authority"]):
        return AGENTS["praxis"]
    elif any(word in text for word in ["inner", "mindfulness", "alignment", "purpose", "anxiety"]):
        return AGENTS["anima"]
    elif any(word in text for word in ["appearance", "attire", "style", "grooming", "energy", "brand"]):
        return AGENTS["persona"]
    elif any(word in text for word in ["first impression", "introduce", "introduction", "elevator", "rapport", "impress"]):
        return AGENTS["impressa"]
    elif any(word in text for word in ["empathic", "listen", "understand", "compassion", "care"]):
        return AGENTS["sentio"]
    elif "senate" in text or "consult" in text:
        return SENATE
    else:
        # Default to the Senate if on-topic but not specific
        print(f"DEBUG: Query '{text}' is ON-TOPIC but not specific. Routing to Senate.") # DEBUG LOG
        return SENATE
    # ---END OF FIX---


def generate(messages, model_type):
    def stream():
        try:
            user_message = next((m["content"] for m in reversed(
                messages) if m["role"] == "user"), "")
            
            # --- ADDED DEBUG LOGGING ---
            print(f"\nDEBUG: Received user message: '{user_message}'")
            selected_agent = detect_agent(user_message)
            print(f"DEBUG: Routed to agent: {selected_agent['name']}")
            # --- END DEBUG LOGGING ---

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
                    # FIX: Get the content from the delta
                    if event.type == "content.delta" and event.delta and event.delta.content:
                        yield event.delta.content 
                    elif event.type == "content.done":
                        break

        except Exception as e:
            # This print will show up in your Render Logs
            print(f"Error streaming response: {e}") 
            yield f"\n[Error: Could not get response from AI. Check server logs.]"

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

