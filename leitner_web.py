import streamlit as st
import json
import os
import random
from datetime import datetime

DATA_FILE = 'leitner_cards.json'
SCHEDULE_FILE = 'custom_schedule.json'
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

# Load schedule
def load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, 'r') as f:
            return json.load(f)
    else:
        st.error("⚠️ custom_schedule.json is missing!")
        return {"start_date": str(datetime.now().date()), "schedule": {}}

cards = load_cards()
schedule_data = load_schedule()
start_date = datetime.strptime(schedule_data["start_date"], "%Y-%m-%d").date()
days_since_start = (datetime.now().date() - start_date).days
today_day = (days_since_start % 64) + 1
todays_levels = schedule_data["schedule"].get(str(today_day), [1])

if "reviewed_ids" not in st.session_state:
    st.session_state.reviewed_ids = set()

# Helper functions
def get_due_cards():
    due_cards = [c for c in cards if c['level'] in todays_levels]
    return [c for c in due_cards if id(c) not in st.session_state.reviewed_ids]

def show_summary():
    st.markdown("### 📊 Level Distribution")
    total = len(cards)
    for i in range(1, MAX_LEVEL + 1):
        count = len([c for c in cards if c['level'] == i])
        percent = (count / total * 100) if total > 0 else 0
        st.write(f"Level {i}: {count} cards ({percent:.1f}%)")
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
            save_cards(cards)
            st.success("✅ Card added!")

def review_cards(card_list):
    if not card_list:
        st.success("🎉 All done for today!")
        return

    if "current_card_index" not in st.session_state or st.session_state.current_card_index >= len(card_list):
        st.session_state.current_card_index = 0
        random.shuffle(card_list)

    card = card_list[st.session_state.current_card_index]

    st.markdown(f"### ❓ [Level {card['level']}] {card['front']}")
    if st.button("Show Answer"):
        st.session_state.show_answer = True

    if st.session_state.get("show_answer", False):
        st.markdown(f"**Answer:** {card['back']}")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Got it"):
                # Level up
                card['level'] = min(card['level'] + 1, MAX_LEVEL)
                card['last_reviewed'] = str(datetime.now().date())
                card['missed_count'] = 0
                save_cards(cards)

                st.session_state.reviewed_ids.add(id(card))
                st.session_state.current_card_index += 1
                st.session_state.show_answer = False
                st.rerun()

        with col2:
            if st.button("❌ Missed it"):
                # Reset to Level 1
                card['level'] = 1
                card['missed_count'] = card.get('missed_count', 0) + 1
                card['last_reviewed'] = str(datetime.now().date())
                save_cards(cards)

                st.session_state.reviewed_ids.add(id(card))
                st.session_state.current_card_index += 1
                st.session_state.show_answer = False
                st.rerun()

def import_cards():
    st.header("📥 Import Multiple Cards")
    st.code("Question::Answer::Tag::Level (tag and level optional)", language="text")

    input_text = st.text_area("Paste your cards here:", height=200)
    if st.button("Import Cards"):
        lines = input_text.strip().split('\n')
        imported = 0
        for line in lines:
            parts = line.split("::")
            if len(parts) >= 2:
                front = parts[0].strip()
                back = parts[1].strip()
                tag = parts[2].strip() if len(parts) >= 3 else ""
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
        st.success(f"✅ Imported {imported} card(s)!")

def override_levels():
    st.header("🛠 Manually Move Cards Between Levels")
    for idx, card in enumerate(cards):
        with st.expander(f"{card['front']} → {card['back']} (Level {card['level']})"):
            new_level = st.slider(f"Level:", 1, MAX_LEVEL, card['level'], key=f"override_{idx}")
            if st.button("Update", key=f"update_{idx}"):
                card['level'] = new_level
                save_cards(cards)
                st.success("✅ Level updated!")

def view_all_cards():
    st.header("🗂 View All Cards")
    for card in cards:
        st.write(f"**{card['front']}** → *{card['back']}* (Level {card['level']}, Tag: {card.get('tag', 'none')})")

# Page routing
page = st.sidebar.selectbox("📚 Menu", [
    "Home", "Review Today's Cards", "Review All Cards", "Review by Tag", "Add New Card", "Import Cards", "Manual Override", "View All Cards"
])

st.title("🧠 Leitner Box Study System")

if page == "Home":
    show_summary()
elif page == "Review Today's Cards":
    review_cards(get_due_cards())
elif page == "Review All Cards":
    review_cards(cards)
elif page == "Review by Tag":
    tags = list(set(c.get("tag", "") for c in cards if c.get("tag")))
    if tags:
        selected_tag = st.selectbox("Choose a tag:", tags)
        filtered = [c for c in cards if c.get("tag") == selected_tag]
        review_cards(filtered)
    else:
        st.warning("⚠️ No tags yet.")
elif page == "Add New Card":
    add_card()
elif page == "Import Cards":
    import_cards()
elif page == "Manual Override":
    override_levels()
elif page == "View All Cards":
    view_all_cards()
