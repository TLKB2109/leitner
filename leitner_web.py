import streamlit as st
import json
import os
import random
from datetime import datetime

# --- File paths ---
DATA_FILE = 'leitner_cards.json'
SCHEDULE_FILE = 'custom_schedule.json'
SESSION_FILE = 'leitner_session.json'
MAX_LEVEL = 7

# --- Load/save functions ---
def load_json(file, default):
    if os.path.exists(file):
        with open(file, 'r') as f:
            return json.load(f)
    return default

def save_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=2)

cards = load_json(DATA_FILE, [])
schedule_data = load_json(SCHEDULE_FILE, {"start_date": str(datetime.now().date()), "schedule": {}})
session_data = load_json(SESSION_FILE, {})

start_date = datetime.strptime(schedule_data["start_date"], "%Y-%m-%d").date()
today = datetime.now().date()
today_key = str(today)
days_since_start = (today - start_date).days
today_day = (days_since_start % 64) + 1
todays_levels = schedule_data["schedule"].get(str(today_day), [1])

# --- Get cards for today ---
def get_due_cards():
    return [c for c in cards if c['level'] in todays_levels]

# --- Save all ---
def save_all():
    save_json(DATA_FILE, cards)
    save_json(SESSION_FILE, session_data)

# --- Sidebar ---
page = st.sidebar.radio("📚 Menu", [
    "Home", "Review Today's Cards", "Review All Cards", "Review by Tag",
    "Add New Card", "Import Cards", "Manual Override"
])

st.title("🧠 Leitner Box Study App")

# --- Summary ---
def show_summary():
    st.markdown(f"### 📅 Today is Day {today_day}")
    st.markdown(f"🔁 Reviewing levels: **{', '.join(map(str, todays_levels))}**")
    level_counts = {i: 0 for i in range(1, MAX_LEVEL+1)}
    for c in cards:
        level_counts[c['level']] += 1
    st.markdown("### 📊 Cards per Level")
    for i in range(1, MAX_LEVEL+1):
        st.write(f"Level {i}: {level_counts[i]} cards")
    st.markdown(f"🧮 Total cards: {len(cards)}")

# --- Add Card ---
def add_card():
    with st.form("add_form"):
        q = st.text_input("Question")
        a = st.text_input("Answer")
        tag = st.text_input("Tag (optional)")
        submitted = st.form_submit_button("Add")
        if submitted and q and a:
            cards.append({
                'front': q, 'back': a, 'level': 1, 'tag': tag,
                'missed_count': 0, 'last_reviewed': str(today)
            })
            save_all()
            st.success("✅ Card added!")

# --- Review Cards ---
def review_cards(card_list, label="Today's"):
    if today_key not in session_data:
        session_data[today_key] = {"cards_today": [], "current_index": 0}

    session = session_data[today_key]
    if not session["cards_today"]:
        session["cards_today"] = [c for c in card_list]
        random.shuffle(session["cards_today"])
        session["current_index"] = 0
        save_all()

    if session["current_index"] >= len(session["cards_today"]):
        st.success("🎉 All cards reviewed for today!")
        return

    st.info(f"Cards left today: **{len(session['cards_today']) - session['current_index']}**")
    st.progress(session["current_index"] / len(session["cards_today"]))

    card = session["cards_today"][session["current_index"]]
    st.markdown(f"### ❓ Level {card['level']}: {card['front']}")

    if st.button("Show Answer"):
        st.session_state.show = True

    if st.session_state.get("show", False):
        st.markdown(f"**Answer:** {card['back']}")
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button("✅ Got it"):
                card['level'] = min(card['level'] + 1, MAX_LEVEL)
                card['last_reviewed'] = str(today)
                card['missed_count'] = 0
                st.success(f"✅ Correct! Promoted to Level {card['level']}")
                session["current_index"] += 1
                st.session_state.show = False
                save_all()
                st.rerun()

        with col2:
            if st.button("❌ Missed it"):
                card['level'] = 1
                card['missed_count'] += 1
                card['last_reviewed'] = str(today)
                st.error(f"❌ Incorrect. Reset to Level 1.\n\nCorrect answer: {card['back']}")
                session["current_index"] += 1
                st.session_state.show = False
                save_all()
                st.rerun()

        with col3:
            if st.button("🗑 Delete"):
                cards.remove(card)
                session["cards_today"].pop(session["current_index"])
                st.warning("🗑 Card deleted.")
                save_all()
                st.rerun()

# --- Import Cards ---
def import_cards():
    st.markdown("### 📥 Import Cards")
    st.code("Question::Answer::Tag::Level")
    raw = st.text_area("Paste cards here (one per line):", height=200)
    if st.button("Import"):
        count = 0
        for line in raw.strip().split('\n'):
            parts = line.split("::")
            if len(parts) >= 2:
                front = parts[0]
                back = parts[1]
                tag = parts[2] if len(parts) >= 3 else ""
                level = int(parts[3]) if len(parts) >= 4 and parts[3].isdigit() else 1
                cards.append({
                    'front': front, 'back': back, 'tag': tag,
                    'level': level, 'missed_count': 0,
                    'last_reviewed': str(today)
                })
                count += 1
        save_all()
        st.success(f"✅ Imported {count} cards.")

# --- Manual Override ---
def override_levels():
    st.markdown("### 🛠 Manage Cards")
    for i, card in enumerate(cards):
        with st.expander(f"[Level {card['level']}] {card['front']}", expanded=False):
            st.markdown(f"**Answer:** {card['back']} — Tag: `{card.get('tag', '')}`")
            new_level = st.slider("Level", 1, MAX_LEVEL, card['level'], key=f"lvl_{i}")
            if st.button("Update", key=f"update_{i}"):
                card['level'] = new_level
                save_all()
                st.success("✅ Level updated.")
            if st.button("Delete", key=f"delete_{i}"):
                cards.pop(i)
                save_all()
                st.warning("🗑 Card deleted.")
                st.rerun()

# --- Tag Review ---
def review_by_tag():
    tags = sorted(list(set(c.get('tag', '') for c in cards if c.get('tag'))))
    tag = st.selectbox("Choose a tag:", tags)
    filtered = [c for c in cards if c.get('tag') == tag]
    review_cards(filtered, label=f"Tag: {tag}")

# --- Page Routing ---
if page == "Home":
    show_summary()
elif page == "Review Today's Cards":
    review_cards(get_due_cards())
elif page == "Review All Cards":
    review_cards(cards)
elif page == "Review by Tag":
    review_by_tag()
elif page == "Add New Card":
    add_card()
elif page == "Import Cards":
    import_cards()
elif page == "Manual Override":
    override_levels()
