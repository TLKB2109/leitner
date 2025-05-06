import streamlit as st
import json
import os
import random
from datetime import datetime

# ---------- CONFIGURATION ----------
DATA_FILE = 'leitner_cards.json'
MAX_LEVEL = 7

# Here is your corrected 64-day custom schedule
game_schedule = {
    1: [2, 1], 2: [3, 1], 3: [2, 1], 4: [4, 1], 5: [2, 1], 6: [3, 1], 7: [2, 1], 8: [1],
    9: [2, 1], 10: [3, 1], 11: [2, 1], 12: [5, 1], 13: [4, 2, 1], 14: [3, 1], 15: [2, 1], 16: [1],
    17: [2, 1], 18: [3, 1], 19: [2, 1], 20: [4, 1], 21: [2, 1], 22: [3, 1], 23: [2, 1], 24: [6, 1],
    25: [2, 1], 26: [3, 1], 27: [2, 1], 28: [5, 1], 29: [4, 2, 1], 30: [3, 1], 31: [2, 1], 32: [1],
    33: [2, 1], 34: [3, 1], 35: [2, 1], 36: [4, 1], 37: [2, 1], 38: [3, 1], 39: [2, 1], 40: [1],
    41: [2, 1], 42: [3, 1], 43: [2, 1], 44: [5, 1], 45: [4, 2, 1], 46: [3, 1], 47: [2, 1], 48: [1],
    49: [2, 1], 50: [3, 1], 51: [2, 1], 52: [4, 1], 53: [2, 1], 54: [3, 1], 55: [2, 1], 56: [7, 1],
    57: [2, 1], 58: [3, 1], 59: [6, 2, 1], 60: [5, 1], 61: [4, 2, 1], 62: [3, 1], 63: [2, 1], 64: [1]
}

# ---------- LOAD/SAVE FUNCTIONS ----------
def load_cards():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_cards(cards):
    with open(DATA_FILE, 'w') as f:
        json.dump(cards, f, indent=2)

cards = load_cards()

# ---------- TODAY'S LEVELS ----------
start_date = datetime(2024, 1, 1).date()
days_since_start = (datetime.now().date() - start_date).days
today_day = (days_since_start % 64) + 1
todays_levels = game_schedule.get(today_day, [1])

# ---------- HELPER FUNCTIONS ----------
def get_due_cards():
    return [c for c in cards if c['level'] in todays_levels and not c.get('reviewed_today', False)]

def reset_today_flags():
    for card in cards:
        card['reviewed_today'] = False
    save_cards(cards)

def show_summary():
    st.markdown("### 📊 Level Summary")
    total = len(cards)
    due_today = len(get_due_cards())
    for i in range(1, MAX_LEVEL + 1):
        count = len([c for c in cards if c['level'] == i])
        percent = (count / total * 100) if total > 0 else 0
        st.write(f"Level {i}: {count} cards ({percent:.1f}%)")
    st.success(f"📅 Today is Day {today_day}: reviewing levels {todays_levels}")
    st.info(f"🃏 {due_today} cards left to review today!")

# ---------- MAIN FUNCTIONS ----------
def add_card():
    with st.form("add_card_form"):
        front = st.text_input("Front (Question)")
        back = st.text_input("Back (Answer)")
        tag = st.text_input("Tag (optional)")
        submitted = st.form_submit_button("Add Card")
        if submitted and front and back:
            new_card = {
                'front': front,
                'back': back,
                'level': 1,
                'tag': tag,
                'reviewed_today': False
            }
            cards.append(new_card)
            save_cards(cards)
            st.success("✅ Card added!")

def review_cards(card_list):
    if not card_list:
        st.info("No cards to review!")
        return

    if "current_card" not in st.session_state or st.session_state.current_card not in card_list:
        st.session_state.current_card = random.choice(card_list)

    card = st.session_state.current_card

    st.markdown(f"### ❓ [Level {card['level']}] {card['front']}")
    if st.button("Show Answer"):
        st.session_state.show_answer = True

    if st.session_state.get("show_answer", False):
        st.markdown(f"**Answer:** {card['back']}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Got it"):
                if card['level'] < MAX_LEVEL:
                    card['level'] += 1
                card['reviewed_today'] = True
                save_cards(cards)
                st.session_state.current_card = None
                st.session_state.show_answer = False
                st.experimental_rerun()

        with col2:
            if st.button("❌ Missed it"):
                card['level'] = 1
                card['reviewed_today'] = True
                save_cards(cards)
                st.session_state.current_card = None
                st.session_state.show_answer = False
                st.experimental_rerun()

def import_cards():
    st.header("📥 Import Multiple Cards")
    st.markdown("Paste cards here (format: Front::Back::Tag)")
    input_text = st.text_area("Paste here:", height=200)
    if st.button("Import Cards"):
        lines = input_text.strip().split('\n')
        for line in lines:
            parts = line.split("::")
            if len(parts) >= 2:
                front = parts[0]
                back = parts[1]
                tag = parts[2] if len(parts) >= 3 else ""
                cards.append({
                    'front': front,
                    'back': back,
                    'level': 1,
                    'tag': tag,
                    'reviewed_today': False
                })
        save_cards(cards)
        st.success("✅ Cards imported!")

def manual_override():
    st.header("🛠 Manual Override")
    for idx, card in enumerate(cards):
        with st.expander(f"{card['front']} (Level {card['level']})"):
            new_level = st.slider("Level", 1, MAX_LEVEL, card['level'], key=f"level_{idx}")
            if new_level != card['level']:
                card['level'] = new_level
                save_cards(cards)
                st.success("Updated!")

# ---------- MAIN PAGE ----------
st.set_page_config(page_title="Leitner Box", layout="wide")
st.title("🧠 Leitner Box Study System")

page = st.sidebar.selectbox("Menu", ["Home", "Review Today's Cards", "Add New Card", "Import Cards", "Manual Override"])

if page == "Home":
    show_summary()

elif page == "Review Today's Cards":
    if st.button("🔄 Reset Reviewed Flags (start new day)"):
        reset_today_flags()
    review_cards(get_due_cards())

elif page == "Add New Card":
    add_card()

elif page == "Import Cards":
    import_cards()

elif page == "Manual Override":
    manual_override()
