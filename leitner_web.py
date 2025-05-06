import streamlit as st
import json
import os
import random
from datetime import datetime, timedelta

# File paths
DATA_FILE = 'leitner_cards.json'
SCHEDULE_FILE = 'custom_schedule.json'
SESSION_FILE = 'leitner_session.json'
MAX_LEVEL = 7

# Load or initialize data
def load_json(file_path, default):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return default

def save_json(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

cards = load_json(DATA_FILE, [])
schedule_data = load_json(SCHEDULE_FILE, {"start_date": str(datetime.now().date()), "schedule": {}})
session_data = load_json(SESSION_FILE, {})

start_date = datetime.strptime(schedule_data["start_date"], "%Y-%m-%d").date()
days_since_start = (datetime.now().date() - start_date).days
today_day = (days_since_start % 64) + 1
todays_levels = schedule_data["schedule"].get(str(today_day), [1])
today_key = str(datetime.now().date())

# Save cards
def save_cards():
    save_json(DATA_FILE, cards)

# Save session
def save_session():
    save_json(SESSION_FILE, session_data)

# Get today's due cards
def get_due_cards():
    reviewed_ids = session_data.get(today_key, {}).get("reviewed_ids", [])
    return [c for i, c in enumerate(cards) if c['level'] in todays_levels and i not in reviewed_ids]

# UI Components
def show_summary():
    st.markdown("### 📊 Level Distribution")
    total = len(cards)
    for i in range(1, MAX_LEVEL + 1):
        count = len([c for c in cards if c['level'] == i])
        st.write(f"Level {i}: {count} cards")
    st.success(f"📅 Today is Day {today_day} — reviewing levels: {', '.join(map(str, todays_levels))}")

def add_card():
    with st.form("add_card_form"):
        front = st.text_input("Question")
        back = st.text_input("Answer")
        tag = st.text_input("Tag (optional)")
        submitted = st.form_submit_button("Add Card")
        if submitted and front and back:
            cards.append({
                'front': front,
                'back': back,
                'level': 1,
                'tag': tag,
                'missed_count': 0,
                'last_reviewed': str(datetime.now().date())
            })
            save_cards()
            st.success("✅ Card added!")

def delete_card(index):
    if 0 <= index < len(cards):
        del cards[index]
        save_cards()
        st.success("🗑️ Card deleted!")

def review_cards(card_list):
    if today_key not in session_data:
        session_data[today_key] = {"reviewed_ids": []}
        save_session()

    remaining_cards = [i for i, c in enumerate(cards) if c in card_list and i not in session_data[today_key]["reviewed_ids"]]
    if not remaining_cards:
        st.success("🎉 You're done for today!")
        return

    index = random.choice(remaining_cards)
    card = cards[index]

    st.markdown(f"### ❓ [Level {card['level']}] {card['front']}")
    if st.button("Show Answer"):
        st.session_state.show_answer = True

    if st.session_state.get("show_answer", False):
        st.markdown(f"**Answer:** {card['back']}")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ Got it"):
                card['level'] = min(card['level'] + 1, MAX_LEVEL)
                card['last_reviewed'] = str(datetime.now().date())
                card['missed_count'] = 0
                session_data[today_key]["reviewed_ids"].append(index)
                save_cards()
                save_session()
                st.session_state.show_answer = False
                st.rerun()
        with col2:
            if st.button("❌ Missed it"):
                card['level'] = 1
                card['last_reviewed'] = str(datetime.now().date())
                card['missed_count'] += 1
                session_data[today_key]["reviewed_ids"].append(index)
                save_cards()
                save_session()
                st.session_state.show_answer = False
                st.rerun()
        with col3:
            if st.button("🗑️ Delete"):
                delete_card(index)
                session_data[today_key]["reviewed_ids"].append(index)
                save_session()
                st.rerun()

def import_cards():
    st.header("📥 Import Cards")
    st.markdown("Format: Question::Answer::Tag::Level")
    input_text = st.text_area("Paste your cards below:")
    if st.button("Import Now"):
        lines = input_text.strip().split('\n')
        imported = 0
        for line in lines:
            parts = line.strip().split("::")
            if len(parts) >= 2:
                front = parts[0]
                back = parts[1]
                tag = parts[2] if len(parts) > 2 else ""
                level = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 1
                cards.append({
                    'front': front,
                    'back': back,
                    'tag': tag,
                    'level': level,
                    'missed_count': 0,
                    'last_reviewed': str(datetime.now().date())
                })
                imported += 1
        save_cards()
        st.success(f"✅ Imported {imported} cards")

def override_levels():
    st.header("🛠 Manage Cards")
    for i, card in enumerate(cards):
        with st.expander(f"{card['front']} → {card['back']} (Level {card['level']})"):
            card['level'] = st.slider("Level", 1, MAX_LEVEL, card['level'], key=f"slider_{i}")
            if st.button("🗑️ Delete", key=f"delete_{i}"):
                delete_card(i)
                st.experimental_rerun()
    save_cards()

# Sidebar menu
page = st.sidebar.radio("📚 Menu", ["Home", "Review Today's Cards", "Add Card", "Import Cards", "Manage Cards"])
st.title("🧠 Leitner Flashcard App")

# Page logic
if page == "Home":
    show_summary()
elif page == "Review Today's Cards":
    review_cards(get_due_cards())
elif page == "Add Card":
    add_card()
elif page == "Import Cards":
    import_cards()
elif page == "Manage Cards":
    override_levels()
