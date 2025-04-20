import streamlit as st
import json
import os
import random
from datetime import datetime, timedelta

st.set_page_config(page_title="Leitner Box", layout="wide", initial_sidebar_state="expanded")

DATA_FILE = 'leitner_cards.json'
SCHEDULE_FILE = 'custom_schedule.json'
MAX_LEVEL = 7

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
        st.info("No cards to review.")
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
                for real_card in cards:
                    if real_card['front'] == card['front']:
                        if real_card['level'] < MAX_LEVEL:
                            real_card['level'] += 1
                        real_card['missed_count'] = 0
                        real_card['last_reviewed'] = str(datetime.now().date())
                        break
                save_cards(cards)
                st.session_state.show_answer = False

                remaining = [c for c in card_list if c['front'] != card['front']]
                if remaining:
                    st.session_state.current_card = random.choice(remaining)
                else:
                    del st.session_state.current_card

                st.success("✅ Moved to next level")
                st.rerun()

        with col2:
            if st.button("❌ Missed it"):
                for real_card in cards:
                    if real_card['front'] == card['front']:
                        real_card['level'] = 1
                        real_card['missed_count'] = real_card.get('missed_count', 0) + 1
                        real_card['last_reviewed'] = str(datetime.now().date())
                        break
                save_cards(cards)
                st.session_state.show_answer = False

                remaining = [c for c in card_list if c['front'] != card['front']]
                if remaining:
                    st.session_state.current_card = random.choice(remaining)
                else:
                    del st.session_state.current_card

                st.error("❌ Reset to Level 1")
                st.rerun()

def import_cards():
    st.header("📥 Import Multiple Cards")
    st.markdown("Paste cards below using this format (one per line):")
    st.code("Question::Answer::Tag (tag is optional)", language="text")

    input_text = st.text_area("Paste your cards here:", height=200)
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

                existing = next((c for c in cards if c['front'] == front), None)
                if existing:
                    existing['back'] = back
                    existing['tag'] = tag
                    updated += 1
                else:
                    cards.append({
                        'front': front,
                        'back': back,
                        'level': 1,
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

def view_all_cards():
    st.header("🗂 All Cards")
    for i, card in enumerate(cards):
        with st.expander(f"🔹 {card['front']} (Level {card['level']})"):
            new_front = st.text_input(f"Front {i}", value=card['front'], key=f"front_{i}")
            new_back = st.text_input(f"Back {i}", value=card['back'], key=f"back_{i}")
            new_tag = st.text_input(f"Tag {i}", value=card.get('tag', ''), key=f"tag_{i}")
            col1, col2 = st.columns(2)

            with col1:
                if st.button("💾 Save Changes", key=f"save_{i}"):
                    card['front'] = new_front
                    card['back'] = new_back
                    card['tag'] = new_tag
                    save_cards(cards)
                    st.success("✅ Card updated.")

            with col2:
                if st.button("🗑️ Delete", key=f"delete_{i}"):
                    cards.pop(i)
                    save_cards(cards)
                    st.warning("❌ Card deleted.")
                    st.rerun()

# Sidebar menu
page = st.sidebar.selectbox("📚 Menu", [
    "Home", "Review Today's Cards", "Review All Cards", "Review by Tag",
    "Add New Card", "Import Cards", "View All Cards", "Manual Override"
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
    add_card()

elif page == "Import Cards":
    import_cards()

elif page == "View All Cards":
    view_all_cards()

elif page == "Manual Override":
    override_levels()
