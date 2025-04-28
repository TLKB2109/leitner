import streamlit as st
import json
import os
import random
from datetime import datetime, timedelta

DATA_FILE = 'leitner_cards.json'
SESSION_FILE = 'session_data.json'
MAX_LEVEL = 7

# Load cards
def load_cards():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

# Save cards
def save_cards(cards):
    with open(DATA_FILE, 'w') as f:
        json.dump(cards, f, indent=2)

# Load session data
def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, 'r') as f:
            return json.load(f)
    return {}

# Save session data
def save_session(session_data):
    with open(SESSION_FILE, 'w') as f:
        json.dump(session_data, f, indent=2)

cards = load_cards()
session_data = load_session()

# Today's key
start_date = datetime(2025, 4, 20)
days_since_start = (datetime.now().date() - start_date.date()).days
today_key = f"day_{(days_since_start % 64) + 1}"

if today_key not in session_data:
    session_data[today_key] = {"completed": []}

# Get today's due cards
schedule = {
    "day_1": [1], "day_2": [1,2], "day_3": [1], "day_4": [1,2,3],
    "day_5": [1,2], "day_6": [1,2,3,4], "day_7": [1,2,3],
    "day_8": [1,2,3,4,5], "day_9": [1,2,3,4], "day_10": [1,2,3,4,5,6],
    "day_11": [1,2,3,4,5], "day_12": [1,2,3,4,5,6,7], "day_13": [1,2,3,4,5,6],
    "day_14": [1,2,3,4,5,6,7], "day_15": [2,3,4,5,6,7], "day_16": [3,4,5,6,7],
    "day_17": [4,5,6,7], "day_18": [5,6,7], "day_19": [6,7], "day_20": [7],
}
levels_today = schedule.get(today_key, [1])

def get_due_cards():
    return [c for c in cards if c['level'] in levels_today and c['front'] not in session_data[today_key]['completed']]

def show_summary():
    st.markdown("### 📊 Level Distribution")
    total = len(cards)
    for i in range(1, MAX_LEVEL + 1):
        count = len([c for c in cards if c['level'] == i])
        percent = (count / total * 100) if total > 0 else 0
        st.write(f"Level {i}: {count} cards ({percent:.1f}%)")
    st.success(f"Today is {today_key.replace('_', ' ').title()} → Reviewing Levels {levels_today}")
    st.info(f"Cards left to review today: {len(get_due_cards())}")

def add_card():
    with st.form("add_card_form"):
        front = st.text_input("Question")
        back = st.text_input("Answer")
        tag = st.text_input("Tag (optional)")
        level = st.number_input("Start at level:", min_value=1, max_value=MAX_LEVEL, value=1)
        submitted = st.form_submit_button("Add Card")
        if submitted and front and back:
            new_card = {
                'front': front,
                'back': back,
                'level': level,
                'tag': tag,
                'missed_count': 0,
                'last_reviewed': str(datetime.now().date())
            }
            cards.append(new_card)
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
                session_data[today_key]['completed'].append(card['front'])
                save_session(session_data)
                st.success(f"Moved to Level {card['level']}")
                st.rerun()

        with col2:
            if st.button("❌ Missed it"):
                card['level'] = 1
                card['missed_count'] += 1
                card['last_reviewed'] = str(datetime.now().date())
                save_cards(cards)
                session_data[today_key]['completed'].append(card['front'])
                save_session(session_data)
                st.error("Moved to Level 1")
                st.rerun()

def import_cards():
    st.header("📥 Import Multiple Cards")
    st.markdown("Paste cards below using format:")
    st.code("Question::Answer::Tag::Level", language="text")

    input_text = st.text_area("Paste here", height=200)
    if st.button("Import!"):
        lines = input_text.strip().split('\n')
        imported = 0
        for line in lines:
            parts = line.split("::")
            if len(parts) >= 2:
                front = parts[0]
                back = parts[1]
                tag = parts[2] if len(parts) >= 3 else ""
                level = int(parts[3]) if len(parts) >= 4 and parts[3].isdigit() else 1
                cards.append({
                    'front': front,
                    'back': back,
                    'level': level,
                    'tag': tag,
                    'missed_count': 0,
                    'last_reviewed': str(datetime.now().date())
                })
                imported += 1
        save_cards(cards)
        st.success(f"✅ Imported {imported} cards!")

def manual_override():
    st.header("🛠 Move Cards Between Levels")
    for idx, card in enumerate(cards):
        with st.expander(f"{card['front']} → {card['back']} (Level {card['level']})"):
            new_level = st.slider("Level", 1, MAX_LEVEL, card['level'], key=f"override_{idx}")
            if st.button("Update", key=f"update_{idx}"):
                card['level'] = new_level
                save_cards(cards)
                st.success("Updated!")

# Streamlit app structure
page = st.sidebar.selectbox("📚 Menu", [
    "Home", "Review Today's Cards", "Add New Card", "Import Cards", "Manual Override"
])

st.title("🧠 Leitner Box Study System")

if page == "Home":
    show_summary()

elif page == "Review Today's Cards":
    review_cards(get_due_cards())

elif page == "Add New Card":
    add_card()

elif page == "Import Cards":
    import_cards()

elif page == "Manual Override":
    manual_override()
