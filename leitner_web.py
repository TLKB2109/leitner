import streamlit as st
import json
import os
import datetime
import random

DATA_FILE = "cards.json"
SCHEDULE_FILE = "schedule.json"

DEFAULT_SCHEDULE = {
    "start_date": "2025-04-19",
    "schedule": {str(i): [1] for i in range(1, 65)}
}

def load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_SCHEDULE

def load_cards():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cards(cards):
    with open(DATA_FILE, "w") as f:
        json.dump(cards, f, indent=2)

def get_today_levels(schedule):
    start_date = datetime.datetime.strptime(schedule["start_date"], "%Y-%m-%d").date()
    today = datetime.date.today()
    day_number = (today - start_date).days % 64 + 1
    return schedule["schedule"].get(str(day_number), [1]), day_number

# Initialize state
st.set_page_config("Leitner Box", layout="wide")
if "cards" not in st.session_state:
    st.session_state.cards = load_cards()
if "current_card" not in st.session_state:
    st.session_state.current_card = None
if "answer_revealed" not in st.session_state:
    st.session_state.answer_revealed = False
if "schedule" not in st.session_state:
    st.session_state.schedule = load_schedule()
if "today_levels" not in st.session_state:
    st.session_state.today_levels, st.session_state.day = get_today_levels(st.session_state.schedule)

st.title("📚 Leitner Box Flashcards")
st.caption(f"Today's Levels: {st.session_state.today_levels} (Day {st.session_state.day})")

# Sidebar menu
with st.sidebar:
    st.header("📥 Import / Save")
    import_text = st.text_area("Paste cards here (Question::Answer::Tag::Level)", height=200)
    if st.button("Import Cards"):
        lines = import_text.strip().split("\n")
        for line in lines:
            try:
                q, a, tag, level = [x.strip() for x in line.split("::")]
                st.session_state.cards[q] = {
                    "answer": a,
                    "tag": tag,
                    "level": int(level)
                }
            except:
                st.warning(f"Skipped invalid line: {line}")
        save_cards(st.session_state.cards)
        st.success("Cards imported!")

    if st.button("💾 Save Progress"):
        save_cards(st.session_state.cards)
        st.success("Progress saved!")

# Select cards due today
due_cards = {
    q: d for q, d in st.session_state.cards.items()
    if d["level"] in st.session_state.today_levels
}

if not due_cards:
    st.success("✅ No cards due today!")
else:
    st.subheader(f"🧠 {len(due_cards)} card(s) to review")
    
    if st.session_state.current_card not in due_cards:
        st.session_state.current_card = random.choice(list(due_cards.keys()))
        st.session_state.answer_revealed = False

    q = st.session_state.current_card
    d = st.session_state.cards[q]
    
    st.markdown(f"**Q:** {q}")
    
    if not st.session_state.answer_revealed:
        user_answer = st.text_input("Your answer:")
        if st.button("Submit"):
            correct = user_answer.strip().lower() == d["answer"].strip().lower()
            if correct:
                st.success("✅ Correct!")
                d["level"] = min(d["level"] + 1, 7)
            else:
                st.error(f"❌ Incorrect. Correct answer: {d['answer']}")
                d["level"] = 1
            save_cards(st.session_state.cards)
            st.session_state.answer_revealed = True
    else:
        if st.button("Next Card"):
            st.session_state.current_card = random.choice(list(due_cards.keys()))
            st.session_state.answer_revealed = False
