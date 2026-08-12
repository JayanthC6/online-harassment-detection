import sys
import os

# Add the current directory to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
import json

texts = [
    {"text": "I will kill you and your family, I know where you live", "actor_id": "angry_user_99"}, # Threat (Critical)
    {"text": "You are a stupid idiot and nobody likes you", "actor_id": "troll_master"}, # Toxicity
    {"text": "I am going to release those photos of you if you don't pay me $1000", "actor_id": "anon_hacker"}, # Extortion (Critical)
    {"text": "Your account has been suspended. Please click here to verify your identity.", "actor_id": "support_scam"}, # Phishing
    {"text": "Invest in this new crypto coin, guaranteed 100x return in 2 days", "actor_id": "crypto_bro"}, # Scam
    {"text": "Send bobs and vagene", "actor_id": "creep_123"}, # Sexual Harassment
    {"text": "Kill yourself now", "actor_id": "hater_x"}, # Self Harm / Threat
    {"text": "I'm going to track your IP and swat your house", "actor_id": "angry_gamer"}, # Threat (Critical)
    {"text": "You're a disgusting pig", "actor_id": "troll_master"}, # Toxicity
    {"text": "I hate people of your kind, you should all be deported", "actor_id": "racist_dude"}, # Hate Speech
    {"text": "Hello how are you doing today?", "actor_id": "friendly_bot"}, # None
    {"text": "Please send me your social security number to claim your prize.", "actor_id": "scammer_1"}, # Scam/Phishing
    {"text": "Give me your lunch money or else I will beat you up", "actor_id": "bully_kid"}, # Extortion
    {"text": "I have hacked your webcam and have a video of you. Send 0.1 BTC to this address.", "actor_id": "anon_hacker"}, # Blackmail (Critical)
    {"text": "Go back to your country you freak", "actor_id": "racist_dude"} # Hate Speech
]

if __name__ == "__main__":
    print("Seeding database with 15 sample incidents...")
    with app.app_context():
        client = app.test_client()
        for item in texts:
            response = client.post('/predict', json=item)
            if response.status_code == 200:
                data = response.get_json()
                label = data.get('primary_label', 'Unknown')
                score = data.get('risk_score', 0)
                print(f"Seeded: {item['text'][:30]:<30} -> {label} (Risk: {score})")
            else:
                print(f"Failed to seed: {item['text'][:30]} - {response.status_code}")
    print("Seeding complete.")
