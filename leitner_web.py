import streamlit as st
import json
import os
from datetime import datetime
import random

DATA_FILE = "terms.json"
SCHEDULE_FILE = "schedule.json"

# Default 64-day schedule
DEFAULT_SCHEDULE = {
    str(day): [level for level in range(1, 8) if (day - level) % 8 == 0]
    for day in range(1, 65)
}

# Loaders
def load_terms():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_terms(terms):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(terms, f, ensure_ascii=False, indent=2)

def load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return DEFAULT_SCHEDULE

# Helpers
def get_today_day(start_date_str="2024-01-01"):
    today = datetime.now().date()
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    day_number = (today - start_date).days % 64 + 1
    return str(day_number)

def get_cards_for_today(terms, schedule_data, today_day):
    levels_today = schedule_data.get(today_day, [])
    return {
        q: card for q, card in terms.items()
        if card.get("level", 1) in levels_today
    }, levels_today

# UI
st.set_page_config(page_title="Leitner Box", layout="wide")
st.title("📚 Leitner Box Flashcards")

# Load data
terms = load_terms()
schedule = load_schedule()
today_day = get_today_day()
today_cards, levels_today = get_cards_for_today(terms, schedule, today_day)

st.markdown(f"### Today's Levels: {levels_today} (Day {today_day})")

# Initialize session state
if "review_queue" not in st.session_state:
    st.session_state.review_queue = list(today_cards.items())
    random.shuffle(st.session_state.review_queue)

if "current" not in st.session_state and st.session_state.review_queue:
    st.session_state.current = st.session_state.review_queue.pop()

# Import
with st.sidebar:
    st.subheader("📥 Import / Save")
    import_box = st.text_area("Paste cards here (Question::Answer::Tag::Level format):", height=150)
    if st.button("Import Cards"):
        count = 0
        for line in import_box.strip().split("\n"):
            if "::" in line:
                parts = line.split("::")
                if len(parts) >= 4:
                    q, a, tag, level = parts[:4]
                    terms[q] = {
                        "answer": a,
                        "tag": tag,
                        "level": int(level),
                        "history": []
                    }
                    count += 1
        save_terms(terms)
        st.success(f"✅ Imported {count} cards.")

    if st.button("💾 Save Progress"):
        save_terms(terms)
        st.success("Progress saved.")

    # Card count
    st.subheader("📊 Level Distribution")
    level_counts = {i: 0 for i in range(1, 8)}
    for card in terms.values():
        lvl = card.get("level", 1)
        if lvl in level_counts:
            level_counts[lvl] += 1
    for lvl, count in level_counts.items():
        st.write(f"Level {lvl}: {count} cards")

# Review
if "current" in st.session_state:
    q, card = st.session_state.current
    st.subheader("📝 Review")
    st.markdown(f"**Question:** {q} ({card.get('tag', '')})")
    answer = st.text_input("Your Answer", key="answer_input")

    if st.button("Submit"):
        correct = answer.strip().lower() == card["answer"].strip().lower()
        st.markdown("✅ Correct!" if correct else f"❌ Incorrect. Answer was: **{card['answer']}**")

        # Init history if missing
        if "history" not in card:
            card["history"] = []

        # Log
        card["history"].append({
            "date": str(datetime.now().date()),
            "correct": correct
        })

        # Adjust level
        if correct:
            card["level"] = min(card.get("level", 1) + 1, 7)
        else:
            card["level"] = 1

        terms[q] = card
        save_terms(terms)

        # Move to next
        if st.session_state.review_queue:
            st.session_state.current = st.session_state.review_queue.pop()
        else:
            del st.session_state["current"]
            st.success("🎉 You're done for today!")

else:
    st.success("✅ You're done for today!")
