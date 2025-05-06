import streamlit as st
import json
import os
import random
from datetime import datetime

# Constants
DATA_FILE = 'leitner_cards.json'
SCHEDULE_FILE = 'schedule.json'
MAX_LEVEL = 7

# Load functions
def load_cards():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_cards(cards):
    with open(DATA_FILE, 'w') as f:
        json.dump(cards, f, indent=2)

def load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, 'r') as f:
            return json.load(f)
    # Fallback if schedule file is missing
    return {
        "start_date": str(datetime.today().date()),
        "schedule": {str(i): [1] for i in range(1, 65)}
    }

# Initialize
cards = load_cards()
schedule_data = load_schedule()
start_date = datetime.strptime(schedule_data["start_date"], "%Y-%m-%d").date()
days_since_start = (datetime.now().date() - start_date).days
today_day = (days_since_start % 64) + 1
todays_levels = schedule_data["schedule"].get(str(today_day), [1])

# Session state
if 'current_card' not in st.session_state:
    st.session_state.current_card = None
if 'show_answer' not in st.session_state:
    st.session_state.show_answer = False
if 'reviewed_ids' not in st.session_state:
    st.session_state.reviewed_ids = []

# Helper functions
def get_due_cards():
    return [c for c in cards if c['level'] in todays_levels and c['id'] not in st.session_state.reviewed_ids]

def pick_next_card():
    due = get_due_cards()
    return random.choice(due) if due else None

def show_summary():
    st.markdown("### 📊 Level Summary")
    total = len(cards)
    for lvl in range(1, MAX_LEVEL + 1):
        count = len([c for c in cards if c['level'] == lvl])
        st.write(f"Level {lvl}: {count} cards")
    st.info(f"📆 Today is Day {today_day} — reviewing levels: {', '.join(map(str, todays_levels))}")

def review_today():
    if not get_due_cards():
        st.success("✅ All cards done for today!")
        return

    if not st.session_state.current_card:
        st.session_state.current_card = pick_next_card()

    card = st.session_state.current_card
    if not card:
        st.success("✅ All cards done for today!")
        return

    st.markdown(f"### ❓ [Level {card['level']}] {card['front']}")
    if st.button("Show Answer"):
        st.session_state.show_answer = True

    if st.session_state.show_answer:
        st.markdown(f"**Answer:** {card['back']}")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("✅ Correct"):
                card['level'] = min(card['level'] + 1, MAX_LEVEL)
                card['last_reviewed'] = str(datetime.today().date())
                st.session_state.reviewed_ids.append(card['id'])
                save_cards(cards)
                st.session_state.show_answer = False
                st.session_state.current_card = None
                st.rerun()

        with col2:
            if st.button("❌ Incorrect"):
                card['level'] = 1
                card['last_reviewed'] = str(datetime.today().date())
                st.session_state.reviewed_ids.append(card['id'])
                save_cards(cards)
                st.session_state.show_answer = False
                st.session_state.current_card = None
                st.rerun()

        with col3:
            if st.button("🗑️ Delete"):
                cards.remove(card)
                save_cards(cards)
                st.session_state.reviewed_ids.append(card['id'])
                st.session_state.show_answer = False
                st.session_state.current_card = None
                st.rerun()

def add_card():
    with st.form("Add Card"):
        front = st.text_input("Front")
        back = st.text_input("Back")
        tag = st.text_input("Tag (optional)")
        level = st.slider("Level", 1, MAX_LEVEL, 1)
        if st.form_submit_button("Add"):
            card = {
                "id": str(random.randint(100000, 999999)),
                "front": front,
                "back": back,
                "tag": tag,
                "level": level,
                "last_reviewed": ""
            }
            cards.append(card)
            save_cards(cards)
            st.success("Card added!")

def import_cards():
    st.markdown("### 📥 Import Cards (format: front::back::tag::level)")
    text = st.text_area("Paste your cards here")
    if st.button("Import"):
        count = 0
        for line in text.strip().split("\n"):
            parts = line.strip().split("::")
            if len(parts) >= 2:
                front = parts[0]
                back = parts[1]
                tag = parts[2] if len(parts) > 2 else ""
                level = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 1
                cards.append({
                    "id": str(random.randint(100000, 999999)),
                    "front": front,
                    "back": back,
                    "tag": tag,
                    "level": level,
                    "last_reviewed": ""
                })
                count += 1
        save_cards(cards)
        st.success(f"Imported {count} card(s)")

def manual_override():
    st.markdown("### 🛠️ Manual Override")
    for i, card in enumerate(cards):
        with st.expander(f"{card['front']} → {card['back']} [Level {card['level']}]"):
            new_level = st.slider("Set new level", 1, MAX_LEVEL, card['level'], key=f"lvl_{i}")
            if st.button("Update", key=f"btn_{i}"):
                card['level'] = new_level
                save_cards(cards)
                st.success("Updated!")
            if st.button("Delete", key=f"del_{i}"):
                cards.pop(i)
                save_cards(cards)
                st.rerun()

# Sidebar navigation
st.sidebar.title("📚 Menu")
page = st.sidebar.radio("", [
    "Summary", "Review Today's Cards", "Add Card", "Import Cards", "Manual Override"
])

st.title("🧠 Leitner Box (Custom SRS)")

if page == "Summary":
    show_summary()
elif page == "Review Today's Cards":
    review_today()
elif page == "Add Card":
    add_card()
elif page == "Import Cards":
    import_cards()
elif page == "Manual Override":
    manual_override()
