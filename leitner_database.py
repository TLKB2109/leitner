import json
import os

DATA_FILE = 'leitner_cards.json'
LEVELS = 7

# Load or initialize card database
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as f:
        cards = json.load(f)
else:
    cards = []

def save_cards():
    with open(DATA_FILE, 'w') as f:
        json.dump(cards, f, indent=2)

def add_card(front, back):
    card = {
        "front": front,
        "back": back,
        "level": 1
    }
    cards.append(card)
    save_cards()
    print(f"✅ Added to Level 1: {front} → {back}")

def view_by_level():
    print("\n📚 Cards by Level:")
    for level in range(1, LEVELS + 1):
        level_cards = [c for c in cards if c['level'] == level]
        print(f"\nLevel {level} ({len(level_cards)} cards):")
        for c in level_cards:
            print(f" - {c['front']} → {c['back']}")

if __name__ == '__main__':
    print("🧠 Leitner Card Database")
    print("1. Add a new card")
    print("2. View cards by level")
    choice = input("Choose an option: ").strip()

    if choice == '1':
        front = input("Front (question): ")
        back = input("Back (answer): ")
        add_card(front, back)
    elif choice == '2':
        view_by_level()
    else:
        print("❌ Invalid choice.")
