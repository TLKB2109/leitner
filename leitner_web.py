import streamlit as st
import json
import os
import uuid
import random
from datetime import datetime

# File paths
DATA_FILE = 'leitner_cards.json'
SCHEDULE_FILE = 'custom_schedule.json'
MAX_LEVEL = 7

# Load cards
def load_cards():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            cards = json.load(f)
            for card in cards:
                if 'id' not in card:
                    card['id'] = str(uuid.uuid4())
            return cards
    return []

# Save cards
def save_cards(cards):
    with open(DATA_FILE, 'w') as f:
        json.dump(cards, f, indent=2)

# Load schedule
def load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, 'r') as f:
            return json.load(f)
    else:
        st.error("Schedule file missing!")
        return {"start_date": str(datetime.now().date()), "schedule": {}}

# Calculate today's level list
def get_today_day_and_levels(schedule_data):
    start_date = datetime.strptime(schedule_data["start_date"], "%Y-%m-%d").date()
    days_since_start = (datetime.now().date() - start_date).days
    today_day = (days_since_start % 64) + 1
    levels = schedule_data["schedule"].get(str(today_day), [1])
    return today_day, levels

# Get today's cards
def get_due_cards(cards, todays_levels, reviewed_ids):
    return [c for c in cards if c['level'] in todays_levels and c['id'] not in reviewed_ids]

# Show summary
def show_summary(cards, today_day, todays_levels):
    st.subheader("📊 Level Distribution")
    total = len(cards)
    for i in range(1, MAX_LEVEL + 1):
        count = len([c for c in cards if c['level'] == i])
        percent = (count / total * 100) if total else 0
        st.write(f"Level {i}: {count} cards ({percent:.1f}%)")
    st.success(f"📅 Today is Day {today_day} — reviewing levels: {', '.join(map(str, todays_levels))}")

# Review cards
def review_cards(cards, todays_levels):
    if "reviewed_ids" not in st.session_state:
        st.session_state.reviewed_ids = []

    due_cards = get_due_cards(cards, todays_levels, st.session_state.reviewed_ids)
    if not due_cards:
        st.success("🎉 You're done for today!")
        return

    card = due_cards[0]
    st.session_state.current_card = card
    st.markdown(f"### ❓ {card['front']}  (Level {card['level']})")

    if st.button("Show Answer"):
        st.session_state.show_answer = True

    if st.session_state.get("show_answer", False):
        st.markdown(f"**Answer:** {card['back']}")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ Correct"):
                card['level'] = min(card['level'] + 1, MAX_LEVEL)
                card['last_reviewed'] = str(datetime.now().date())
                st.session_state.reviewed_ids.append(card['id'])
                save_cards(cards)
                st.session_state.show_answer = False
                st.rerun()

        with col2:
            if st.button("❌ Incorrect"):
                card['level'] = 1
                card['last_reviewed'] = str(datetime.now().date())
                st.session_state.reviewed_ids.append(card['id'])
                save_cards(cards)
                st.session_state.show_answer = False
                st.rerun()

        with col3:
            if st.button("🗑 Delete"):
                cards.remove(card)
                st.session_state.reviewed_ids.append(card['id'])
                save_cards(cards)
                st.success("Card deleted.")
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

# Import cards
def import_cards(cards):
    st.subheader("📥 Import Cards")
    st.markdown("Paste in format: `Question::Answer::Tag::Level`")
    text = st.text_area("Bulk import")
    if st.button("Import"):
        lines = text.strip().split("\n")
        count = 0
        for line in lines:
            parts = line.strip().split("::")
            if len(parts) >= 2:
                front = parts[0]
                back = parts[1]
                tag = parts[2] if len(parts) > 2 else ""
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
        st.success(f"Imported {count} cards.")

# Override levels
def manual_override(cards):
    st.subheader("🛠 Manual Override")
    for card in cards:
        with st.expander(f"{card['front']} → {card['back']} (Level {card['level']})"):
            col1, col2 = st.columns([3, 1])
            with col1:
                new_level = st.slider("Level", 1, MAX_LEVEL, card['level'], key=card['id'])
            with col2:
                if st.button("Update", key=card['id'] + "_update"):
                    card['level'] = new_level
                    save_cards(cards)
                    st.success("Updated")

# App logic
cards = load_cards()
schedule = load_schedule()
today_day, todays_levels = get_today_day_and_levels(schedule)

st.set_page_config(page_title="Leitner App", layout="wide")
st.title("🧠 Leitner Box Study App")

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
    review_cards(cards, todays_levels)

elif page == "Review All Cards":
    review_cards(cards, list(range(1, MAX_LEVEL + 1)))

elif page == "Review by Tag":
    tags = list(set(c['tag'] for c in cards if c.get("tag")))
    tag = st.selectbox("Choose a tag", tags)
    filtered = [c for c in cards if c.get("tag") == tag]
    review_cards(filtered, list(range(1, MAX_LEVEL + 1)))

elif page == "Add New Card":
    add_card(cards)

elif page == "Import Cards":
    import_cards(cards)

elif page == "Manual Override":
    manual_override(cards)
