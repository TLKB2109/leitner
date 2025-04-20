import json
import os
import random

DATA_FILE = 'leitner_cards.json'
BOX_COUNT = 7

# Load or initialize flashcards
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as f:
        cards = json.load(f)
else:
    cards = []

# Add new card
def add_card():
    front = input("Question: ")
    back = input("Answer: ")
    cards.append({'front': front, 'back': back, 'box': 1})

# Save cards to file
def save_cards():
    with open(DATA_FILE, 'w') as f:
        json.dump(cards, f, indent=2)

# Review cards from a chosen box
def review_box(box_number):
    box_cards = [card for card in cards if card['box'] == box_number]
    if not box_cards:
        print(f"No cards in Box {box_number}")
        return

    random.shuffle(box_cards)
    for card in box_cards:
        print("\nQuestion:", card['front'])
        input("Press Enter to show answer...")
        print("Answer:", card['back'])
        response = input("Did you get it right? (y/n): ").strip().lower()

        if response == 'y' and card['box'] < BOX_COUNT:
            card['box'] += 1
            print(f"✅ Moved to Box {card['box']}")
        elif response == 'n':
            card['box'] = 1
            print("❌ Moved to Box 1")

# Main loop
while True:
    print("\n=== Leitner Box ===")
    print("1. Add new card")
    print("2. Review Box 1")
    print("3. Review Box 2")
    print("4. Review Box 3")
    print("5. Review Box 4")
    print("6. Review Box 5")
    print("7. Review Box 6")
    print("8. Review Box 7")
    print("9. Exit")

    choice = input("Choose an option: ").strip()

    if choice == '1':
        add_card()
        save_cards()
    elif choice in ['2', '3', '4', '5', '6','7','8']:
        review_box(int(choice) - 1)
        save_cards()
    elif choice == '9':
        save_cards()
        print("Goodbye!")
        break
    else:
        print("Invalid choice.")
