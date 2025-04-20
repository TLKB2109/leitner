import streamlit as st
import json
import os
import random
from datetime import datetime, timedelta

DATA_FILE = 'leitner_cards.json'
BOX_COUNT = 7

# Load data
def load_cards():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

# Save data
def save_cards(cards):
    with open(DATA_FILE, 'w') as f:
        json.dump(cards, f, indent=2)

cards = load_cards()

# Due logic
def is_due(card):
    box_interval = [1, 2, 4, 7, 14, 21, 30]
    days = box_interval[card['box'] - 1]
    last = datetime.strptime(card.get('last_reviewed', str(datetime.now().date())), "%Y-%m-%d")
    return datetime.now().date() >= (last + timedelta(days=days)).date()

def get_due_cards():
    return [c for c in cards if is_due(c)]

def show_summary():
    st.markdown("### 📊 Box Distribution")
    total = len(cards)
    for i in range(1, BOX_COUNT + 1):
        count = len([c for c in cards if c['box'] == i])
        percent = (count / total * 100) if total > 0 else 0
        st.write(f"Box {i}: {count} cards ({percent:.1f}%)")

    due = [c['box'] for c in cards if is_due(c)]
    if due:
        due_boxes = sorted(set(due))
        st.success("🔔 Boxes with due cards today: " + ', '.join(str(b) for b in due_boxes))
    else:
        st.info("✅ No boxes have due cards today.")

# Add new card
def add_card():
    with st.form("add_card_form"):
        front = st.text_input("Question")
        back = st.text_input("Answer")
        tag = st.text_input("Tag (optional)")
        submitted = st.form_submit_button("Add Card")
        if submitted and front and back:
            new_card = {
                'front': front,
                'back': back,
                'box': 1,
                'tag': tag,
                'missed_count': 0,
                'last_reviewed': str(datetime.now().date())
            }
            cards.append(new_card)
            save_cards(cards)
            st.success("✅ Card added!")

# Review interface
def review_cards(card_list):
    if not card_list:
        st.info("No cards to review.")
        return

    card = random.choice(card_list)
    st.markdown(f"### ❓ [Box {card['box']}] {card['front']}")
    if st.button("Show Answer"):
        st.markdown(f"**Answer:** {card['back']}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Got it"):
                if card['box'] < BOX_COUNT:
                    card['box'] += 1
                card['missed_count'] = 0
                card['last_reviewed'] = str(datetime.now().date())
                save_cards(cards)
                st.success(f"Moved to Box {card['box']}")
                st.experimental_rerun()
        with col2:
            if st.button("❌ Missed it"):
                card['box'] = 1
                card['missed_count'] = card.get('missed_count', 0) + 1
                card['last_reviewed'] = str(datetime.now().date())
                save_cards(cards)
                st.error("Moved to Box 1")
                st.experimental_rerun()

# Page selector
page = st.sidebar.selectbox("📚 Menu", [
    "Home", "Review Due Cards", "Review All Cards", "Review by Tag", "Add New Card", "View All Cards"
])

# Routes
st.title("🧠 Leitner Box Study System (Web App)")

if page == "Home":
    st.header("📌 Summary")
    show_summary()

elif page == "Review Due Cards":
    st.header("📆 Review Due Cards")
    review_cards(get_due_cards())

elif page == "Review All Cards":
    st.header("📚 Review All Cards")
    review_cards(cards)

elif page == "Review by Tag":
    st.header("🏷 Review by Tag")
    tags = list(set(c.get("tag", "") for c in cards if c.get("tag")))
    selected_tag = st.selectbox("Choose a tag:", tags)
    filtered = [c for c in cards if c.get("tag") == selected_tag]
    review_cards(filtered)

elif page == "Add New Card":
    st.header("➕ Add a New Card")
    add_card()

elif page == "View All Cards":
    st.header("🗂 All Cards")
    for i, card in enumerate(cards):
        st.markdown(f"- **{card['front']}** → *{card['back']}* (Box {card['box']}, Tag: {card.get('tag', 'none')})")
