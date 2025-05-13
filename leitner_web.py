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

# Load and Save
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

def load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, 'r') as f:
            return json.load(f)
    return {"start_date": str(datetime.now().date()), "schedule": {}}

def load_reviewed_ids():
    if os.path.exists(REVIEWED_FILE):
        with open(REVIEWED_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_reviewed_ids(data):
    with open(REVIEWED_FILE, 'w') as f:
        json.dump(data, f)

# Daily state
def get_today_day_and_levels(schedule_data):
    start_date = datetime.strptime(schedule_data["start_date"], "%Y-%m-%d").date()
    days_since = (datetime.now().date() - start_date).days
    today_day = (days_since % 64) + 1
    return today_day, schedule_data["schedule"].get(str(today_day), [1])

def get_due_cards(cards, levels, reviewed_ids):
    return [c for c in cards if c['level'] in levels and c['id'] not in reviewed_ids]

# UI
def show_summary(cards, today_day, todays_levels):
    st.subheader("📊 Level Distribution")
    total = len(cards)
    for i in range(1, MAX_LEVEL + 1):
        count = len([c for c in cards if c['level'] == i])
        percent = (count / total * 100) if total else 0
        st.write(f"Level {i}: {count} cards ({percent:.1f}%)")
    st.success(f"📅 Today is Day {today_day} — reviewing levels: {', '.join(map(str, todays_levels))}")

# Review logic
def review_cards(cards, levels, today_key):
    reviewed_ids = st.session_state.get("reviewed_ids", {}).get(today_key, [])
    due_cards = get_due_cards(cards, levels, reviewed_ids)

    st.info(f"Cards left: {len(due_cards)}")

    if not due_cards:
        st.success("🎉 Done reviewing!")
        return

    # Shuffle new set
    if "queue" not in st.session_state or not st.session_state.queue:
        st.session_state.queue = due_cards.copy()
        random.shuffle(st.session_state.queue)

    card = st.session_state.queue[0]
    st.markdown(f"### ❓ {card['front']} (Level {card['level']})")

    if st.button("Show Answer"):
        st.session_state.show_answer = True

    if st.session_state.get("show_answer", False):
        st.markdown(f"**Answer:** {card['back']}")

        col1, col2, col3, col4 = st.columns(4)

        def update_and_advance(correct):
            if correct:
                card['level'] = min(card['level'] + 1, MAX_LEVEL)
            else:
                card['level'] = 1
            card['last_reviewed'] = str(datetime.now().date())
            reviewed_ids.append(card['id'])
            save_cards(cards)
            reviewed_dict = st.session_state.get("reviewed_ids", {})
            reviewed_dict[today_key] = reviewed_ids
            save_reviewed_ids(reviewed_dict)
            st.session_state.show_answer = False
            st.session_state.queue.pop(0)
            st.rerun()

        with col1:
            if st.button("✅ Correct"):
                update_and_advance(True)
        with col2:
            if st.button("❌ Incorrect"):
                update_and_advance(False)
        with col3:
            if st.button("🗑 Delete"):
                cards.remove(card)
                st.session_state.queue.pop(0)
                save_cards(cards)
                st.rerun()
        with col4:
            if st.button("⏭ Skip"):
                st.session_state.queue.append(st.session_state.queue.pop(0))
                st.session_state.show_answer = False
                st.rerun()

# Reset
def reset_today(today_key):
    reviewed = load_reviewed_ids()
    if today_key in reviewed:
        del reviewed[today_key]
        save_reviewed_ids(reviewed)
        st.session_state.pop("queue", None)
        st.success("🔄 Today's progress reset.")
        st.rerun()

# Add
def add_card(cards):
    st.subheader("➕ Add Card")
    q = st.text_input("Question")
    a = st.text_input("Answer")
    tag = st.text_input("Tag (optional)")
    if st.button("Add") and q and a:
        cards.append({'id': str(uuid.uuid4()), 'front': q, 'back': a, 'level': 1, 'tag': tag, 'last_reviewed': ""})
        save_cards(cards)
        st.success("Card added!")

# Import
def import_cards(cards):
    st.subheader("📥 Import Cards")
    text = st.text_area("Paste `Question::Answer::Tag::Level`")
    if st.button("Import"):
        count = 0
        for line in text.strip().split("\n"):
            parts = line.strip().split("::")
            if len(parts) >= 2:
                cards.append({
                    'id': str(uuid.uuid4()),
                    'front': parts[0],
                    'back': parts[1],
                    'tag': parts[2] if len(parts) > 2 else "",
                    'level': int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 1,
                    'last_reviewed': ""
                })
                count += 1
        save_cards(cards)
        st.success(f"✅ Imported {count} cards!")

# Override
def manual_override(cards):
    st.subheader("🛠 Manual Override")
    for card in cards:
        with st.expander(f"{card['front']} → {card['back']} (Level {card['level']})"):
            front = st.text_input("Edit Front", card['front'], key=f"front_{card['id']}")
            back = st.text_input("Edit Back", card['back'], key=f"back_{card['id']}")
            tag = st.text_input("Edit Tag", card.get('tag', ''), key=f"tag_{card['id']}")
            level = st.slider("Level", 1, MAX_LEVEL, card['level'], key=f"level_{card['id']}")
            if st.button("Save", key=f"save_{card['id']}"):
                card['front'], card['back'], card['tag'], card['level'] = front, back, tag, level
                save_cards(cards)
                st.success("Saved")

# Review by level
def review_by_level(cards):
    level = st.selectbox("Select Level", list(range(1, MAX_LEVEL+1)))
    selected = [c for c in cards if c['level'] == level]
    if selected:
        review_cards(selected, [level], today_key="manual")
    else:
        st.info("No cards in this level.")

# Load state
cards = load_cards()
schedule = load_schedule()
today_day, todays_levels = get_today_day_and_levels(schedule)
today_key = str(datetime.now().date())

if "reviewed_ids" not in st.session_state:
    st.session_state.reviewed_ids = load_reviewed_ids()

st.set_page_config("Leitner App", layout="wide")
st.title("🧠 Leitner Study App")

# Menu
page = st.sidebar.radio("📚 Menu", [
    "Home", "Review Today's Cards", "Review All Cards", "Review by Level",
    "Review by Tag", "Add New Card", "Import Cards", "Manual Override"
])

# Routing
if page == "Home":
    show_summary(cards, today_day, todays_levels)
    if st.button("🔁 Reset Today"):
        reset_today(today_key)

elif page == "Review Today's Cards":
    review_cards(cards, todays_levels, today_key)

elif page == "Review All Cards":
    review_cards(cards, list(range(1, MAX_LEVEL+1)), today_key="all")

elif page == "Review by Level":
    review_by_level(cards)

elif page == "Review by Tag":
    tags = list(set(c['tag'] for c in cards if c.get("tag")))
    if tags:
        tag = st.selectbox("Choose Tag", tags)
        selected = [c for c in cards if c.get("tag") == tag]
        review_cards(selected, list(range(1, MAX_LEVEL+1)), today_key="tag_" + tag)
    else:
        st.info("No tags yet.")

elif page == "Add New Card":
    add_card(cards)

elif page == "Import Cards":
    import_cards(cards)

elif page == "Manual Override":
    manual_override(cards)
