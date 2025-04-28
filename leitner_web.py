import streamlit as st
import json
import os
import random
from datetime import datetime

DATA_FILE = 'leitner_cards.json'
SCHEDULE_FILE = 'custom_schedule.json'
SESSION_FILE = 'session_data.json'
MAX_LEVEL = 7

# Load cards
def load_cards():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_cards(cards):
    with open(DATA_FILE, 'w') as f:
        json.dump(cards, f, indent=2)

# Load schedule
def load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, 'r') as f:
            return json.load(f)
    else:
        st.error("⚠️ custom_schedule.json missing!")
        return {"start_date": str(datetime.now().date()), "schedule": {}}

# Load session data
def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_session(session_data):
    with open(SESSION_FILE, 'w') as f:
        json.dump(session_data, f, indent=2)

cards = load_cards()
schedule_data = load_schedule()
session_data = load_session()

start_date = datetime.strptime(schedule_data["start_date"], "%Y-%m-%d").date()
days_since_start = (datetime.now().date() - start_date).days
today_day = (days_since_start % 64) + 1
todays_levels = schedule_data["schedule"].get(str(today_day), [1])

today_key = str(datetime.now().date())
if today_key not in session_data:
    session_data[today_key] = {"completed": []}
    save_session(session_data)

# Helper to get today's cards
def get_today_cards():
    today_due = [c for c in cards if c['level'] in todays_levels]
    completed_fronts = session_data.get(today_key, {}).get("completed", [])
    return [c for c in today_due if c['front'] not in completed_fronts]

def show_summary():
    st.markdown("### 📊 Level Distribution")
    total = len(cards)
    for i in range(1, MAX_LEVEL + 1):
        count = len([c for c in cards if c['level'] == i])
        percent = (count / total * 100) if total > 0 else 0
        st.write(f"Level {i}: {count} cards ({percent:.1f}%)")
    due_today = len(get_today_cards())
    st.success(f"📅 Today is Day {today_day} — reviewing levels: {', '.join(map(str, todays_levels))}")
    st.info(f"🃏 {due_today} cards left to review today!")

def add_card():
    with st.form("add_card_form"):
        front = st.text_input("Question")
        back = st.text_input("Answer")
        tag = st.text_input("Tag (optional)")
        level = st.slider("Starting Level", 1, MAX_LEVEL, 1)
        submitted = st.form_submit_button("Add Card")
        if submitted and front and back:
            cards.append({
                'front': front,
                'back': back,
                'level': level,
                'tag': tag,
                'missed_count': 0,
                'last_reviewed': str(datetime.now().date())
            })
            save_cards(cards)
            st.success("✅ Card added!")

def review_cards(card_list):
    if not card_list:
        st.info("No cards to review.")
        return

    if "current_card" not in st.session_state or st.session_state.current_card not in card_list:
        st.session_state.current_card = random.choice(card_list)
        st.session_state.show_answer = False

    card = st.session_state.current_card

    st.markdown(f"### ❓ [Level {card['level']}] {card['front']}")
    if not st.session_state.get("show_answer", False):
        if st.button("Show Answer"):
            st.session_state.show_answer = True

    if st.session_state.get("show_answer", False):
        st.markdown(f"**Answer:** {card['back']}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Got it"):
                if card['level'] < MAX_LEVEL:
                    card['level'] += 1
                card['missed_count'] = 0
                card['last_reviewed'] = str(datetime.now().date())
                save_cards(cards)
                session_data[today_key]["completed"].append(card['front'])
                save_session(session_data)
                st.success(f"Moved to Level {card['level']}")
                st.rerun()

        with col2:
            if st.button("❌ Missed it"):
                card['level'] = 1
                card['missed_count'] += 1
                card['last_reviewed'] = str(datetime.now().date())
                save_cards(cards)
                session_data[today_key]["completed"].append(card['front'])
                save_session(session_data)
                st.error("Moved to Level 1")
                st.rerun()

def override_levels():
    st.header("🛠 Manually Move Cards Between Levels")
    for i, card in enumerate(cards):
        with st.expander(f"📌 {card['front']} → {card['back']} (Level {card['level']})"):
            new_level = st.slider(f"Set new level for card {i+1}", 1, MAX_LEVEL, card['level'], key=f"override_{i}")
            if st.button("Update", key=f"update_{i}"):
                card['level'] = new_level
                save_cards(cards)
                st.success(f"✅ Updated to Level {new_level}")

page = st.sidebar.selectbox("📚 Menu", [
    "Home", "Review Today's Cards", "Review All Cards", "Add New Card", "Manual Override"
])

st.title("📘 Leitner Box")

if page == "Home":
    st.header("📌 Summary")
    show_summary()

elif page == "Review Today's Cards":
    st.header("📆 Review Today's Cards")
    review_cards(get_today_cards())

elif page == "Review All Cards":
    st.header("📚 Review All Cards")
    review_cards(cards)

elif page == "Add New Card":
    st.header("➕ Add a New Card")
    add_card()

elif page == "Manual Override":
    override_levels()
