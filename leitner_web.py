import streamlit as st
import json
import os
from datetime import datetime

DATA_FILE = "cards.json"
SCHEDULE_FILE = "schedule.json"

# ========== Default Schedule ==========
DEFAULT_SCHEDULE = {
    "start_date": str(datetime.today().date()),
    "schedule": {str(i): [1] for i in range(1, 65)}
}
for i in range(1, 65):
    if i % 2 == 0:
        DEFAULT_SCHEDULE["schedule"][str(i)].append(2)
    if i % 4 == 0:
        DEFAULT_SCHEDULE["schedule"][str(i)].append(3)

# ========== Load / Save ==========
def load_cards():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cards(cards):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)

def load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_SCHEDULE

def get_today_day(start_date_str):
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    return ((datetime.today().date() - start_date).days % 64) + 1

# ========== Streamlit App ==========
st.set_page_config(page_title="Leitner Box Flashcards", layout="wide")

if "cards" not in st.session_state:
    st.session_state.cards = load_cards()
if "current_card" not in st.session_state:
    st.session_state.current_card = None
if "show_answer" not in st.session_state:
    st.session_state.show_answer = False
if "history" not in st.session_state:
    st.session_state.history = []

# Load schedule
schedule = load_schedule()
today_day = get_today_day(schedule["start_date"])
today_levels = schedule["schedule"].get(str(today_day), [1])

# Sidebar
st.sidebar.title("📥 Import / Save")
input_data = st.sidebar.text_area("Paste cards here (Question::Answer::Tag::Level):", height=200)
if st.sidebar.button("Import Cards"):
    new_cards = {}
    for line in input_data.strip().split("\n"):
        parts = line.split("::")
        if len(parts) >= 2:
            q, a = parts[0].strip(), parts[1].strip()
            tag = parts[2].strip() if len(parts) >= 3 else ""
            level = int(parts[3].strip()) if len(parts) == 4 and parts[3].strip().isdigit() else 1
            new_cards[q] = {"answer": a, "level": level, "tag": tag}
    st.session_state.cards.update(new_cards)
    save_cards(st.session_state.cards)
    st.success(f"✅ Imported {len(new_cards)} cards.")

if st.sidebar.button("💾 Save Progress"):
    save_cards(st.session_state.cards)
    st.success("Progress saved!")

# Main Title
st.title("📘 Leitner Box Flashcards")
st.subheader(f"Today's Levels: {today_levels} (Day {today_day})")

# Get today's cards
today_cards = {
    q: d for q, d in st.session_state.cards.items()
    if d["level"] in today_levels
}

# Handle reviewing
if not today_cards:
    st.success("🎉 You finished all cards for today!")
else:
    if not st.session_state.current_card:
        st.session_state.current_card = list(today_cards.items())[0]
        st.session_state.show_answer = False

    q, d = st.session_state.current_card
    st.markdown(f"**Question:** {q}")

    if st.session_state.show_answer:
        st.markdown(f"**Answer:** {d['answer']}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Got it"):
                st.session_state.cards[q]["level"] += 1
                st.session_state.history.append((q, "Correct", d["level"]))
                st.session_state.current_card = None
                st.experimental_rerun()
        with col2:
            if st.button("❌ Missed it"):
                st.session_state.cards[q]["level"] = 1
                st.session_state.history.append((q, "Wrong", d["level"]))
                st.session_state.current_card = None
                st.experimental_rerun()
    else:
        if st.button("Show Answer"):
            st.session_state.show_answer = True

# History
if st.session_state.history:
    st.markdown("---")
    st.subheader("📜 Review History")
    for q, result, prev_level in reversed(st.session_state.history[-10:]):
        st.write(f"**{result}**: {q} (was Level {prev_level})")
