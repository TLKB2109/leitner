import streamlit as st
import json
import os
from datetime import datetime

DATA_FILE = "terms.json"
SCHEDULE_FILE = "schedule.json"

def load_schedule():
    if not os.path.exists(SCHEDULE_FILE):
        default = {str(i+1): [1, 2, 3, 4, 5] for i in range(64)}
        with open(SCHEDULE_FILE, "w") as f:
            json.dump(default, f)
        return default
    with open(SCHEDULE_FILE, "r") as f:
        return json.load(f)

def load_terms():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_terms(terms):
    with open(DATA_FILE, "w") as f:
        json.dump(terms, f, indent=2, ensure_ascii=False)

def get_today_day(start_date="2024-01-01"):
    delta = datetime.today() - datetime.strptime(start_date, "%Y-%m-%d")
    return (delta.days % 64) + 1

def get_cards_for_today(terms, schedule, day):
    levels = schedule.get(str(day), [])
    cards = [card for card in terms.values() if card.get("level", 1) in levels]
    return cards, levels

# --- UI Start ---
st.set_page_config(layout="wide")
st.title("📘 Leitner Box Flashcards")

schedule = load_schedule()
terms = load_terms()
today = get_today_day()
today_cards, today_levels = get_cards_for_today(terms, schedule, today)

# Session state
if "cards" not in st.session_state:
    st.session_state.cards = today_cards
if "index" not in st.session_state:
    st.session_state.index = 0

# Sidebar
st.sidebar.header("📥 Import / Save")
raw = st.sidebar.text_area("Paste cards (Question::Answer::Tag::Level):")

if st.sidebar.button("Import Cards"):
    count = 0
    for line in raw.strip().splitlines():
        parts = line.strip().split("::")
        if len(parts) >= 4:
            q, a, tag, lvl = parts[:4]
            terms[q] = {
                "question": q,
                "answer": a,
                "tag": tag,
                "level": int(lvl),
                "history": []
            }
            count += 1
    save_terms(terms)
    st.sidebar.success(f"✅ Imported {count} new cards.")
    st.rerun()

if st.sidebar.button("📤 Export Cards"):
    st.sidebar.download_button("Download terms.json", data=json.dumps(terms, indent=2, ensure_ascii=False), file_name="terms.json")

# Review UI
st.subheader(f"Today's Levels: {today_levels} (Day {today})")

if st.session_state.index < len(st.session_state.cards):
    card = st.session_state.cards[st.session_state.index]
    st.markdown(f"**Question:** {card['question']}")
    answer = st.text_input("Your Answer", key="answer")

    if st.button("Submit"):
        is_correct = answer.strip().lower() == card["answer"].strip().lower()
        st.markdown("✅ Correct!" if is_correct else f"❌ Incorrect. Correct answer: {card['answer']}")

        card.setdefault("history", []).append({
            "date": str(datetime.today().date()),
            "correct": is_correct
        })

        card["level"] = min(card["level"] + 1, 7) if is_correct else 1
        save_terms(terms)

        st.session_state.index += 1
        st.rerun()
else:
    st.success("🎉 You're done for today!")

# Level Stats
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Level Distribution")
counts = {i: 0 for i in range(1, 8)}
for t in terms.values():
    counts[t.get("level", 1)] += 1
for lvl, count in counts.items():
    st.sidebar.write(f"Level {lvl}: {count} card{'s' if count != 1 else ''}")
