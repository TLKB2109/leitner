import streamlit as st
import json
import os
import uuid
from datetime import datetime

DATA_FILE = 'leitner_cards.json'
SCHEDULE_FILE = 'custom_schedule.json'
MAX_LEVEL = 7

# Load and save
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
    return {"start_date": str(datetime.now().date()), "schedule": {}}

cards = load_cards()
schedule_data = load_schedule()

# Setup today
start_date = datetime.strptime(schedule_data["start_date"], "%Y-%m-%d").date()
days_since_start = (datetime.now().date() - start_date).days
today_day = (days_since_start % 64) + 1
todays_levels = schedule_data["schedule"].get(str(today_day), [1])

# Assign IDs to old cards
for card in cards:
    if 'id' not in card:
        card['id'] = str(uuid.uuid4())
save_cards(cards)

# Get due cards
def get_due_cards():
    reviewed = st.session_state.get("reviewed_ids", [])
    return [c for c in cards if c['level'] in todays_levels and c['id'] not in reviewed]

# Show summary
def show_summary():
    st.subheader("📊 Level Distribution")
    total = len(cards)
    for i in range(1, MAX_LEVEL + 1):
        count = len([c for c in cards if c['level'] == i])
        st.write(f"Level {i}: {count} cards ({count/total*100:.1f}%)" if total else f"Level {i}: 0 cards")
    st.info(f"📅 Today is Day {today_day}, reviewing levels: {', '.join(map(str, todays_levels))}")

# Review logic
def review_today():
    if "reviewed_ids" not in st.session_state:
        st.session_state.reviewed_ids = []

    due = get_due_cards()
    if not due:
        st.success("✅ All cards done for today!")
        return

    card = due[0]
    st.markdown(f"### ❓ {card['front']}")
    user_input = st.text_input("Your Answer")

    if st.button("Submit"):
        if user_input.strip().lower() == card['back'].strip().lower():
            st.success(f"✅ Correct! ({card['back']})")
            card['level'] = min(card['level'] + 1, MAX_LEVEL)
        else:
            st.error(f"❌ Incorrect. Correct answer: {card['back']}")
            card['level'] = 1

        st.session_state.reviewed_ids.append(card['id'])
        save_cards(cards)
        st.rerun()

    if st.button("🗑 Delete This Card"):
        cards.remove(card)
        save_cards(cards)
        st.session_state.reviewed_ids.append(card['id'])  # prevent rerun error
        st.rerun()

# Add card
def add_card():
    front = st.text_input("Question")
    back = st.text_input("Answer")
    tag = st.text_input("Tag (optional)")

    if st.button("Add Card") and front and back:
        new_card = {
            "id": str(uuid.uuid4()),
            "front": front,
            "back": back,
            "tag": tag,
            "level": 1,
            "missed_count": 0,
            "last_reviewed": str(datetime.now().date())
        }
        cards.append(new_card)
        save_cards(cards)
        st.success("✅ Card added!")

# Manual override
def override_levels():
    st.subheader("🛠 Manual Override / Delete")
    for card in cards:
        with st.expander(f"{card['front']} → {card['back']} (Level {card['level']})"):
            col1, col2 = st.columns(2)
            with col1:
                new_level = st.slider("Set Level", 1, MAX_LEVEL, card['level'], key=card['id'])
                if st.button("Update", key=f"update_{card['id']}"):
                    card['level'] = new_level
                    save_cards(cards)
                    st.success("Updated!")
            with col2:
                if st.button("Delete", key=f"del_{card['id']}"):
                    cards.remove(card)
                    save_cards(cards)
                    st.success("Deleted!")
                    st.rerun()

# Import
def import_cards():
    st.subheader("📥 Bulk Import")
    st.text("Format: Question::Answer::Tag::Level (optional tag/level)")
    raw = st.text_area("Paste cards:")
    if st.button("Import"):
        count = 0
        for line in raw.strip().split("\n"):
            parts = line.strip().split("::")
            if len(parts) >= 2:
                cards.append({
                    "id": str(uuid.uuid4()),
                    "front": parts[0],
                    "back": parts[1],
                    "tag": parts[2] if len(parts) >= 3 else "",
                    "level": int(parts[3]) if len(parts) == 4 else 1,
                    "missed_count": 0,
                    "last_reviewed": str(datetime.now().date())
                })
                count += 1
        save_cards(cards)
        st.success(f"✅ Imported {count} card(s)")

# Sidebar menu
page = st.sidebar.radio("📚 Menu", [
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
    override_levels()
