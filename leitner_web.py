import streamlit as st
import json
import os
import random
from datetime import datetime, timedelta

st.set_page_config(page_title="Leitner Box", layout="wide", initial_sidebar_state="expanded")

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

def get_due_cards():
    return [c for c in cards if c['level'] in todays_levels]

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
            new_card = {
                'front': front,
                'back': back,
                'level': 1,
                'tag': tag,
                'missed_count': 0,
                'last_reviewed': str(datetime.now().date())
            }
            cards.append(new_card)
            save_cards(cards)
            st.success("✅ Card added!")

# --- Track what cards reviewed today ---
if "reviewed_today" not in st.session_state:
    st.session_state.reviewed_today = []

def review_cards(card_list):
    available_cards = [c for c in card_list if c['front'] not in st.session_state.reviewed_today]

    st.markdown(f"📚 Cards left today: **{len(available_cards)}**")

    if not available_cards:
        st.success("✅ All due cards reviewed for today!")
        return

    if "current_card" not in st.session_state or st.session_state.current_card not in available_cards:
        st.session_state.current_card = random.choice(available_cards)

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
                card['missed_count'] = 0
                card['last_reviewed'] = str(datetime.now().date())
                save_cards(cards)
                st.session_state.reviewed_today.append(card['front'])
                st.session_state.show_answer = False
                st.success(f"✅ Moved to Level {card['level']}")
                st.experimental_rerun()

        with col2:
            if st.button("❌ Missed it"):
                card['level'] = 1
                card['missed_count'] = card.get('missed_count', 0) + 1
                card['last_reviewed'] = str(datetime.now().date())
                save_cards(cards)
                st.session_state.reviewed_today.append(card['front'])
                st.session_state.show_answer = False
                st.error("❌ Reset to Level 1")
                st.experimental_rerun()

# --- ✨ NEW: Import cards with Level info! ---
def import_cards():
    st.header("📥 Import Multiple Cards (Now Supports Level!)")
    st.markdown("Paste cards below using this format (one per line):")
    st.code("Question::Answer::Tag::Level", language="text")
    st.markdown("*(If you leave off Tag and Level, it defaults to empty and Level 1.)*")

    input_text = st.text_area("Paste your cards here:", height=300)
    if st.button("Import Cards"):
        lines = input_text.strip().split('\n')
        imported = 0
        updated = 0

        for line in lines:
            parts = line.strip().split("::")
            if len(parts) >= 2:
                front = parts[0].strip()
                back = parts[1].strip()
                tag = parts[2].strip() if len(parts) >= 3 else ""
                level = int(parts[3]) if len(parts) >= 4 and parts[3].isdigit() else 1

                # Check if card already exists
                existing = next((c for c in cards if c['front'] == front), None)
                if existing:
                    existing['back'] = back
                    existing['tag'] = tag
                    existing['level'] = level
                    updated += 1
                else:
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
        st.success(f"✅ Imported {imported} new card(s), updated {updated} existing.")

def override_levels():
    st.header("🛠 Manually Move Cards Between Levels")
    for i, card in enumerate(cards):
        with st.expander(f"📌 {card['front']} → {card['back']} (Level {card['level']})"):
            new_level = st.slider(f"Set new level for card {i+1}", 1, MAX_LEVEL, card['level'], key=f"override_{i}")
            if st.button("Update", key=f"update_{i}"):
                card['level'] = new_level
                save_cards(cards)
                st.success(f"✅ Updated to Level {new_level}")

# Page routing
page = st.sidebar.selectbox("📚 Menu", [
    "Home", "Review Today's Cards", "Review All Cards", "Review by Tag",
    "Add New Card", "Import Cards", "Manual Override"
])

st.title("📘 Leitner Box")

if page == "Home":
    st.header("📌 Summary")
    show_summary()

elif page == "Review Today's Cards":
    st.header("📆 Review Today's Cards")
    review_cards(get_due_cards())

elif page == "Review All Cards":
    st.header("📚 Review All Cards")
    review_cards(cards)

elif page == "Review by Tag":
    st.header("🏷 Review by Tag")
    tags = list(set(c.get("tag", "") for c in cards if c.get("tag")))
    if tags:
        selected_tag = st.selectbox("Choose a tag:", tags)
        filtered = [c for c in cards if c.get("tag") == selected_tag]
        review_cards(filtered)
    else:
        st.warning("No tags available yet.")

elif page == "Add New Card":
    st.header("➕ Add a New Card")
    add_card()

elif page == "Import Cards":
    import_cards()

elif page == "Manual Override":
    override_levels()
