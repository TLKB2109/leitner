import streamlit as st
import json
import os
from datetime import datetime, timedelta

DATA_FILE = 'leitner_cards.json'
SESSION_FILE = 'leitner_session.json'
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

# Load session
def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, 'r') as f:
            return json.load(f)
    return {}

# Save session
def save_session(session_data):
    with open(SESSION_FILE, 'w') as f:
        json.dump(session_data, f, indent=2)

# Load schedule
def load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, 'r') as f:
            return json.load(f)
    else:
        st.error("⚠️ custom_schedule.json is missing!")
        return {"start_date": str(datetime.now().date()), "schedule": {}}

cards = load_cards()
session_data = load_session()
schedule_data = load_schedule()

# Set today's day
start_date = datetime.strptime(schedule_data["start_date"], "%Y-%m-%d").date()
days_since_start = (datetime.now().date() - start_date).days
today_day = (days_since_start % 64) + 1
todays_levels = schedule_data["schedule"].get(str(today_day), [1])

today_key = str(datetime.now().date())
if today_key not in session_data:
    session_data[today_key] = {"completed": [], "current_card_index": 0}
    save_session(session_data)

# Filter today's due cards (and make sure you don't re-ask completed ones)
def get_today_cards():
    today_due = [c for c in cards if c['level'] in todays_levels]
    completed_fronts = session_data[today_key]["completed"]
    return [c for c in today_due if c['front'] not in completed_fronts]

# Review screen
def review_cards(card_list):
    if not card_list:
        st.success("✅ No more cards to review today!")
        return

    st.info(f"Cards left today: {len(card_list)}")

    # Randomize the deck each time
    if "current_card" not in st.session_state:
        st.session_state.current_card = card_list[0]
        st.session_state.show_answer = False

    card = st.session_state.current_card

    st.markdown(f"### ❓ [Level {card['level']}] {card['front']}")

    if st.button("Show Answer"):
        st.session_state.show_answer = True

    if st.session_state.get("show_answer", False):
        st.markdown(f"**Answer:** {card['back']}")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Got it"):
                # Promote the card
                for c in cards:
                    if c['front'] == card['front'] and c['back'] == card['back']:
                        c['level'] = min(c['level'] + 1, MAX_LEVEL)
                        c['missed_count'] = 0
                        c['last_reviewed'] = str(datetime.now().date())
                save_cards(cards)

                # Mark as completed for today
                session_data[today_key]["completed"].append(card['front'])
                save_session(session_data)

                # Move to next card
                st.session_state.current_card = None
                st.session_state.show_answer = False
                st.rerun()

        with col2:
            if st.button("❌ Missed it"):
                # Demote the card
                for c in cards:
                    if c['front'] == card['front'] and c['back'] == card['back']:
                        c['level'] = 1
                        c['missed_count'] = c.get('missed_count', 0) + 1
                        c['last_reviewed'] = str(datetime.now().date())
                save_cards(cards)

                # Mark as completed for today
                session_data[today_key]["completed"].append(card['front'])
                save_session(session_data)

                # Move to next card
                st.session_state.current_card = None
                st.session_state.show_answer = False
                st.rerun()

# Add new card
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

# Manual override screen
def override_levels():
    st.header("🛠 Manually Move Cards Between Levels")
    for i, card in enumerate(cards):
        with st.expander(f"📌 {card['front']} → {card['back']} (Level {card['level']})"):
            new_level = st.slider(f"Set new level for {card['front']}", 1, MAX_LEVEL, card['level'], key=f"override_{i}")
            if st.button("Update", key=f"update_{i}"):
                card['level'] = new_level
                save_cards(cards)
                st.success(f"✅ Updated to Level {new_level}")

# Show summary
def show_summary():
    st.header("📊 Leitner Box Summary")
    total = len(cards)
    if total == 0:
        st.info("No cards yet!")
        return

    level_counts = [0] * MAX_LEVEL
    for c in cards:
        if 1 <= c['level'] <= MAX_LEVEL:
            level_counts[c['level'] - 1] += 1

    for i, count in enumerate(level_counts):
        st.write(f"Level {i+1}: {count} cards ({(count/total)*100:.1f}%)")

    st.success(f"📅 Today is Day {today_day} — Reviewing Levels: {', '.join(map(str, todays_levels))}")

# Import cards
def import_cards():
    st.header("📥 Import Multiple Cards")
    st.markdown("Paste cards below using this format (one per line):")
    st.code("Question::Answer::Tag::Level (Level optional)", language="text")

    input_text = st.text_area("Paste your cards here:", height=200)
    if st.button("Import Cards"):
        lines = input_text.strip().split('\n')
        imported = 0
        for line in lines:
            parts = line.strip().split("::")
            if len(parts) >= 2:
                front = parts[0]
                back = parts[1]
                tag = parts[2] if len(parts) >= 3 else ""
                level = int(parts[3]) if len(parts) >= 4 else 1
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

# Routes
page = st.sidebar.radio("📚 Menu", [
    "Home", "Review Today's Cards", "Review All Cards", "Add New Card", "Import Cards", "Manual Override"
])

st.title("🧠 Leitner Box Study System")

if page == "Home":
    show_summary()

elif page == "Review Today's Cards":
    review_cards(get_today_cards())

elif page == "Review All Cards":
    review_cards(cards)

elif page == "Add New Card":
    add_card()

elif page == "Import Cards":
    import_cards()

elif page == "Manual Override":
    override_levels()
