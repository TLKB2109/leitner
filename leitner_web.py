import streamlit as st
st.cache_data.clear()
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

# Initial load
cards = load_cards()
session_data = load_session()

# Today's key
start_date = datetime(2025, 4, 20)
days_since_start = (datetime.now().date() - start_date.date()).days
today_key = f"day_{(days_since_start % 64) + 1}"

if today_key not in session_data:
    session_data[today_key] = {"completed": []}

# Review schedule
schedule = {
    "day_1": [2,1], "day_2": [3,1], "day_3": [2,1], "day_4": [4,1],
    "day_5": [2,1], "day_6": [3,1], "day_7": [2,1],
    "day_8": [1], "day_9": [2,1], "day_10": [3,1],
    "day_11": [2,1], "day_12": [5,1], "day_13": [4,2,1],
    "day_14": [3,1], "day_15": [2,1], "day_16": [1],
    "day_17": [2,1], "day_18": [3,1], "day_19": [2,1], "day_20": [4,1], 
    "day_21":[2,1],"day_22":[3,1],"day_23":[2,1],"day_24":[6,1],"day_25":[2,1],"day_26":[3,1],"day_27":[2,1],
    "day_28":[5,1],"day_29":[4,2,1],"day_30":[3,1],"day_31":[2,1],"day_32":[1],"day_33":[2,1],
    "day_34":[3,1],"day_35":[2,1],"day_36":[4,1],"day_37":[2,1],"day_38":[3,1],"day_39":[2,1],"day_40":[1],"day_41":[2,1],
    "day_42":[3,1],"day_43":[2,1],"day_44":[5,1],"day_45":[4,2,1],"day_46":[3,1],"day_47":[2,1],"day_48":[1],
    "day_49":[2,1],"day_50":[3,1],"day_51":[2,1],"day_52":[4,1],"day_53":[2,1],"day_54":[3,1],"day_55":[2,1],"day_56":[7,1],"day_57":[2,1],
    "day_58":[3,1],"day_59":[6,2,1],"day_60":[5,1],"day_61":[4,2,1],"day_62":[3,1],"day_63":[2,1],"day_64":[1]
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
    st.success(f"Today is {today_key.replace('_', ' ').title()} — Reviewing Levels {levels_today}")
    st.info(f"Cards left today: {len(get_due_cards())}")

def add_card():
    with st.form("add_card_form"):
        front = st.text_input("Question")
        back = st.text_input("Answer")
        tag = st.text_input("Tag (optional)")
        level = st.number_input("Start at level:", 1, MAX_LEVEL, 1)
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

    if "current_card" not in st.session_state:
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
                # Promote card
                for c in cards:
                    if c['front'] == card['front']:
                        if c['level'] < MAX_LEVEL:
                            c['level'] += 1
                        c['missed_count'] = 0
                        c['last_reviewed'] = str(datetime.now().date())
                save_cards(cards)
                session_data[today_key]['completed'].append(card['front'])
                save_session(session_data)
                st.success("✅ Promoted to next level!")
                st.session_state.pop("current_card")
                st.rerun()

        with col2:
            if st.button("❌ Missed it"):
                # Demote card
                for c in cards:
                    if c['front'] == card['front']:
                        c['level'] = 1
                        c['missed_count'] += 1
                        c['last_reviewed'] = str(datetime.now().date())
                save_cards(cards)
                session_data[today_key]['completed'].append(card['front'])
                save_session(session_data)
                st.error("❌ Reset to Level 1!")
                st.session_state.pop("current_card")
                st.rerun()

def import_cards():
    st.header("📥 Import Cards")
    st.markdown("Format: `Question::Answer::Tag::Level`")
    input_text = st.text_area("Paste here", height=200)

    if st.button("Import!"):
        lines = input_text.strip().split('\n')
        imported = 0
        for line in lines:
            parts = line.split("::")
            if len(parts) >= 2:
                front = parts[0]
                back = parts[1]
                tag = parts[2] if len(parts) > 2 else ""
                level = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 1
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
            new_level = st.slider("New Level", 1, MAX_LEVEL, card['level'], key=f"override_{idx}")
            if st.button("Update", key=f"update_{idx}"):
                card['level'] = new_level
                save_cards(cards)
                st.success(f"Updated {card['front']} to Level {new_level}!")

# Layout
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
