import streamlit as st
import json
import os
from datetime import datetime, timedelta
import random

DATA_FILE = "terms.json"
SCHEDULE_FILE = "schedule.json"

# ---------------- Utility Functions ---------------- #

def load_terms():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_terms(terms):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(terms, f, ensure_ascii=False, indent=2)

def load_schedule():
    with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_today_day(start_date_str):
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    today = datetime.now().date()
    delta_days = (today - start_date).days
    return (delta_days % 64) + 1

def get_cards_for_today(terms, today_levels):
    return [card for card in terms if card["level"] in today_levels]

# ---------------- App Logic ---------------- #

def main():
    st.set_page_config(page_title="Leitner Box", layout="centered")
    st.title("📘 Leitner Box Review")
    schedule = load_schedule()
    terms = load_terms()

    today_day = get_today_day(schedule["start_date"])
    today_levels = schedule["schedule"].get(str(today_day), [])
    todays_cards = get_cards_for_today(terms, today_levels)

    st.subheader(f"📅 Day {today_day}: Reviewing Levels {today_levels}")
    st.write(f"Cards due today: **{len(todays_cards)}**")

    if "current_index" not in st.session_state:
        st.session_state.current_index = 0
        st.session_state.answered_cards = []

    if st.session_state.current_index >= len(todays_cards):
        st.success("✅ Review complete for today!")
        return

    current_card = todays_cards[st.session_state.current_index]
    st.markdown(f"**Question:** {current_card['question']}")
    with st.expander("Show Answer"):
        st.markdown(f"**Answer:** {current_card['answer']}")
        st.caption(f"Tag: {current_card['tag']} — Level {current_card['level']}")

    col1, col2 = st.columns(2)
    if col1.button("✅ Got it"):
        for term in terms:
            if term["question"] == current_card["question"]:
                term["level"] = min(term["level"] + 1, 7)
                break
        save_terms(terms)
        st.session_state.current_index += 1
        st.experimental_rerun()

    if col2.button("❌ Missed it"):
        for term in terms:
            if term["question"] == current_card["question"]:
                term["level"] = 1
                break
        save_terms(terms)
        st.session_state.current_index += 1
        st.experimental_rerun()

    if st.button("🔄 Restart Today's Review"):
        st.session_state.current_index = 0
        st.experimental_rerun()

    with st.expander("📥 Import New Cards"):
        uploaded = st.text_area("Paste new cards (Format: Question::Answer::Tag::Level)", height=200)
        if st.button("Import Cards"):
            lines = uploaded.strip().split("\n")
            for line in lines:
                parts = line.strip().split("::")
                if len(parts) == 4:
                    q, a, tag, lvl = parts
                    exists = any(card["question"] == q for card in terms)
                    if not exists:
                        terms.append({
                            "question": q.strip(),
                            "answer": a.strip(),
                            "tag": tag.strip(),
                            "level": int(lvl.strip())
                        })
            save_terms(terms)
            st.success("✅ Cards imported successfully!")
            st.experimental_rerun()

if __name__ == "__main__":
    main()
