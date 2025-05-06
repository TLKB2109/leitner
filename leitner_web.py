import streamlit as st
import json
import os
from datetime import datetime
import random

DATA_FILE = "terms.json"
SCHEDULE_FILE = "schedule.json"

# ---------------- Loaders and Savers ---------------- #

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
    return ((today - start_date).days % 64) + 1

def get_cards_for_today(terms, levels_today):
    return [card for card in terms if card["level"] in levels_today]

# ---------------- Main App ---------------- #

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

    if st.session_state.current_index >= len(todays_cards):
        st.success("✅ You finished all cards for today!")
        return

    current = todays_cards[st.session_state.current_index]
    st.markdown(f"**Question:** {current['question']}")
    with st.expander("Show Answer"):
        st.markdown(f"**Answer:** {current['answer']}")
        st.caption(f"Tag: {current['tag']} — Level {current['level']}")

    col1, col2 = st.columns(2)
    if col1.button("✅ Got it"):
        for t in terms:
            if t["question"] == current["question"]:
                t["level"] = min(t["level"] + 1, 7)
        save_terms(terms)
        st.session_state.current_index += 1
        st.experimental_rerun()

    if col2.button("❌ Missed it"):
        for t in terms:
            if t["question"] == current["question"]:
                t["level"] = 1
        save_terms(terms)
        st.session_state.current_index += 1
        st.experimental_rerun()

    if st.button("🔁 Restart Today's Review"):
        st.session_state.current_index = 0
        st.experimental_rerun()

    # ---------------- Import Section ---------------- #
    with st.expander("📥 Import New Cards to Specific Levels"):
        text_input = st.text_area("Enter cards (format: `Question::Answer::Tag::Level`)", height=200)
        if st.button("📩 Import Cards"):
            count = 0
            for line in text_input.strip().split("\n"):
                parts = line.strip().split("::")
                if len(parts) == 4:
                    q, a, tag, lvl = map(str.strip, parts)
                    if not any(card["question"] == q for card in terms):
                        try:
                            level = int(lvl)
                            if level < 1 or level > 7:
                                continue
                            terms.append({
                                "question": q,
                                "answer": a,
                                "tag": tag,
                                "level": level
                            })
                            count += 1
                        except ValueError:
                            continue
            save_terms(terms)
            st.success(f"✅ Imported {count} new card(s).")
            st.experimental_rerun()

if __name__ == "__main__":
    main()
