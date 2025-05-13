import streamlit as st
import json
import os
import uuid
import random
from datetime import datetime

# File paths
DATA_FILE = 'leitner_cards.json'
SCHEDULE_FILE = 'custom_schedule.json'
REVIEWED_FILE = 'reviewed_ids.json'
MAX_LEVEL = 7

# Load/save cards
def load_cards():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            cards = json.load(f)
            for card in cards:
                if 'id' not in card:
                    card['id'] = str(uuid.uuid4())
            return cards
    return []

def save_cards(cards):
    with open(DATA_FILE, 'w') as f:
        json.dump(cards, f, indent=2)

# Load/save reviewed IDs
def load_reviewed_ids():
    if os.path.exists(REVIEWED_FILE):
        with open(REVIEWED_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_reviewed_ids(reviewed_dict):
    with open(REVIEWED_FILE, 'w') as f:
        json.dump(reviewed_dict, f)

# Load schedule
def load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, 'r') as f:
            return json.load(f)
    else:
        return {"start_date": str(datetime.now().date()), "schedule": {}}

# Get today's day number and active levels
def get_today_day_and_levels(schedule_data):
    start_date = datetime.strptime(schedule_data["start_date"], "%Y-%m-%d").date()
    days_since_start = (datetime.now().date() - start_date).days
    today_day = (days_since_start % 64) + 1
    levels = schedule_data["schedule"].get(str(today_day), [1])
    return today_day, levels

# Return list of due cards for today
def get_due_cards(cards, todays_levels, reviewed_ids):
    return [c for c in cards if c['level'] in todays_levels and c['id'] not in reviewed_ids]

# Show card distribution
def show_summary(cards, today_day, todays_levels):
    st.subheader("📊 Level Distribution")
    total = len(cards)
    for i in range(1, MAX_LEVEL + 1):
        count = len([c for c in cards if c['level'] == i])
        percent = (count / total * 100) if total else 0
        st.write(f"Level {i}: {count} cards ({percent:.1f}%)")
    st.success(f"📅 Today is Day {today_day} — reviewing levels: {', '.join(map(str, todays_levels))}")

# Review logic
def review_cards(cards, todays_levels, today_key):
    if "reviewed_ids" not in st.session_state:
        st.session_state.reviewed_ids = load_reviewed_ids().get(today_key, [])
    if "card_queue" not in st.session_state:
        st.session_state.card_queue = get_due_cards(cards, todays_levels, st.session_state.reviewed_ids)
        random.shuffle(st.session_state.card_queue)

    due_cards = st.session_state.card_queue
    st.info(f"Cards left today: **{len(due_cards)}**")

    if not due_cards:
        st.success("🎉 You're done for today!")
        return

    card = due_cards[0]
    st.markdown(f"### ❓ {card['front']} (Level {card['level']})")

    if st.button("Show Answer"):
        st.session_state.show_answer = True

    if st.session_state.get("show_answer", False):
        st.markdown(f"**Answer:** {card['back']}")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("✅ Correct"):
                card['level'] = min(card['level'] + 1, MAX_LEVEL)
                card['last_reviewed'] = str(datetime.now().date())
                st.session_state.reviewed_ids.append(card['id'])
                save_cards(cards)
                st.session_state.card_queue.pop(0)
                st.session_state.show_answer = False
                save_reviewed_ids({today_key: st.session_state.reviewed_ids})
                st.rerun()

        with col2:
            if st.button("❌ Incorrect"):
                card['level'] = 1
                card['last_reviewed'] = str(datetime.now().date())
                st.session_state.reviewed_ids.append(card['id'])
                save_cards(cards)
                st.session_state.card_queue.pop(0)
                st.session_state.show_answer = False
                save_reviewed_ids({today_key: st.session_state.reviewed_ids})
                st.rerun()

        with col3:
            if st.button("🗑 Delete"):
                cards.remove(card)
                st.session_state.reviewed_ids.append(card['id'])
                save_cards(cards)
                st.session_state.card_queue.pop(0)
                st.session_state.show_answer = False
                save_reviewed_ids({today_key: st.session_state.reviewed_ids})
                st.success("Card deleted.")
                st.rerun()

        with col4:
            if st.button("⏭ Skip"):
                st.session_state.card_queue.append(st.session_state.card_queue.pop(0))
                st.session_state.show_answer = False
                st.rerun()

# Add card
def add_card(cards):
    st.subheader("➕ Add Card")
    front = st.text_input("Question")
    back = st.text_input("Answer")
    tag = st.text_input("Tag (optional)")
    if st.button("Add"):
        if front and back:
            cards.append({
                'id': str(uuid.uuid4()),
                'front': front,
                'back': back,
                'level': 1,
                'tag': tag,
                'last_reviewed': ""
            })
            save_cards(cards)
            st.success("Card added!")

# Import
def import_cards(cards):
    st.subheader("📥 Import Cards")
    st.markdown("Format: `Question::Answer::Tag::Level`")
    text = st.text_area("Paste multiple cards")
    if st.button("Import"):
        count = 0
        for line in text.strip().split("\n"):
            parts = line.split("::")
            if len(parts) >= 2:
                front = parts[0].strip()
                back = parts[1].strip()
                tag = parts[2].strip() if len(parts) > 2 else ""
                level = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 1
                cards.append({
                    'id': str(uuid.uuid4()),
                    'front': front,
                    'back': back,
                    'tag': tag,
                    'level': level,
                    'last_reviewed': ""
                })
                count += 1
        save_cards(cards)
        st.success(f"Imported {count} card(s).")

# Manual edit
def manual_override(cards):
    st.subheader("🛠 Manual Override")
    for card in cards:
        with st.expander(f"{card['front']} → {card['back']} (Level {card['level']})"):
            card['front'] = st.text_input("Edit question", value=card['front'], key=card['id'] + "_front")
            card['back'] = st.text_input("Edit answer", value=card['back'], key=card['id'] + "_back")
            card['tag'] = st.text_input("Edit tag", value=card.get('tag', ""), key=card['id'] + "_tag")
            card['level'] = st.slider("Level", 1, MAX_LEVEL, card['level'], key=card['id'] + "_level")
            if st.button("Save Changes", key=card['id'] + "_save"):
                save_cards(cards)
                st.success("Card updated")

# App Setup
st.set_page_config("Leitner Box", layout="wide")
st.title("🧠 Leitner Flashcards")

cards = load_cards()
schedule = load_schedule()
today_day, todays_levels = get_today_day_and_levels(schedule)
today_key = str(datetime.now().date())

page = st.sidebar.radio("📋 Menu", [
    "Home",
    "Review Today's Cards",
    "Review All Cards",
    "Review by Tag",
    "Add New Card",
    "Import Cards",
    "Manual Override"
])

if page == "Home":
    show_summary(cards, today_day, todays_levels)

elif page == "Review Today's Cards":
    review_cards(cards, todays_levels, today_key)

elif page == "Review All Cards":
    review_cards(cards, list(range(1, MAX_LEVEL + 1)), today_key)

elif page == "Review by Tag":
    tags = list(set(c.get("tag", "") for c in cards if c.get("tag")))
    if tags:
        tag = st.selectbox("Choose a tag", tags)
        review_cards([c for c in cards if c.get("tag") == tag], list(range(1, MAX_LEVEL + 1)), today_key)
    else:
        st.info("No tags available.")

elif page == "Add New Card":
    add_card(cards)

elif page == "Import Cards":
    import_cards(cards)

elif page == "Manual Override":
    manual_override(cards)
