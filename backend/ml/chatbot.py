import os
from groq import Groq

def generate_chat_response(history: list) -> str:
    """
    Generates a chatbot response using the Groq API.
    Only answers questions related to cyber crimes, digital safety, incident file details, and cyber news.
    
    Args:
        history (list): A list of message dictionaries: [{"role": "user"|"assistant", "content": "..."}]
        
    Returns:
        str: The chatbot's markdown-formatted response.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "System error: GROQ_API_KEY is not configured on the server. The cyber assistant is unavailable."

    client = Groq(api_key=api_key)

    system_prompt = {
        "role": "system",
        "content": (
            "You are ShieldAI's cyber security assistant. You must ONLY provide information "
            "related to cyber crimes, digital safety, incident file details, and cyber news. "
            "If the user asks about anything else (e.g., cooking recipes, general programming, sports, etc.), "
            "politely decline and remind them that you are a specialized cyber security assistant. "
            "Keep your responses concise, informative, and formatted in Markdown."
        )
    }

    # Format history for Groq (ensure only 'role' and 'content' are present, and roles are valid)
    formatted_messages = [system_prompt]
    for msg in history:
        role = msg.get("role")
        if role not in ["user", "assistant"]:
            continue
        formatted_messages.append({
            "role": role,
            "content": msg.get("content", "")
        })

    try:
        chat_completion = client.chat.completions.create(
            messages=formatted_messages,
            model="llama-3.1-8b-instant",
            temperature=0.3,
            max_tokens=500,
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Chatbot Error: {e}")
        return "I'm sorry, I'm having trouble connecting to my neural network right now. Please try again later."
