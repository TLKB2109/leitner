import streamlit as st
import json
import os
from datetime import datetime
import random

DATA_FILE = "cards.json"
SCHEDULE_FILE = "schedule.json"

def load_cards():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_cards(cards):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)

def load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {"start_date": str(datetime.today().date()), "schedule": {}}

def get_today_levels(schedule):
    start_date = datetime.strptime(schedule["start_date"], "%Y-%m-%d")
    today = datetime.today()
    day_index = (today - start_date).days % 64 + 1
    return schedule["schedule"].get(str(day_index), [])

# Initialize session state
if "cards" not in st.session_state:
    st.session_state.cards = load_cards()
if "schedule" not in st.session_state:
    st.session_state.schedule = load_schedule()
if "quiz_done" not in st.session_state:
    st.session_state.quiz_done = False

# Sidebar menu
with st.sidebar:
    st.header("📂 Menu")
    uploaded_file = st.file_uploader("📥 Import Cards (.txt format)", type=["txt"])
    if uploaded_file is not None:
        lines = uploaded_file.read().decode("utf-8").strip().split("\n")
        for line in lines:
            try:
                q, a, tag, level = line.split("::")
                st.session_state.cards.append({
                    "question": q.strip(),
                    "answer": a.strip(),
                    "tag": tag.strip(),
                    "level": int(level.strip())
                })
            except:
                continue
        save_cards(st.session_state.cards)
        st.success("✅ Cards imported!")

    if st.button("📤 Export Cards"):
        export_text = "\n".join(
            f'{c["question"]}::{c["answer"]}::{c["tag"]}::{c["level"]}'
            for c in st.session_state.cards
        )
        st.download_button("Download", export_text, file_name="cards_export.txt")

    if st.button("🔁 Reset Today"):
        st.session_state.quiz_done = False
        st.success("🔄 Session reset.")

st.title("🧠 Leitner Box (Daily Review)")

# Filter today's cards
today_levels = get_today_levels(st.session_state.schedule)
cards_today = [c for c in st.session_state.cards if c["level"] in today_levels]

st.info(f"📅 Today’s levels: {today_levels} — Cards due: {len(cards_today)}")

if not cards_today:
    st.success("🎉 You're done for today!")
    st.session_state.quiz_done = True
else:
    card = random.choice(cards_today)
    st.subheader(f"Q: {card['question']}")
    user_input = st.text_input("Your Answer")
    if st.button("Submit"):
        if user_input.strip().lower() == card["answer"].strip().lower():
            st.success("✅ Correct!")
            card["level"] = min(card["level"] + 1, 7)
        else:
            st.error(f"❌ Incorrect. Answer: {card['answer']}")
            card["level"] = 1
        save_cards(st.session_state.cards)
        st.rerun()

# View all cards
with st.expander("📋 All Cards"):
    for card in st.session_state.cards:
        st.write(f"[{card['level']}] {card['question']} → {card['answer']} ({card['tag']})")
