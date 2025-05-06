import streamlit as st
import json
import os
import datetime
import random

DATA_FILE = "cards.json"
SCHEDULE_FILE = "schedule.json"

# Default schedule fallback
DEFAULT_SCHEDULE = {
    "start_date": "2025-04-19",
    "schedule": {
        str(i): [lvl for lvl in [2, 1] if (i % 16) in [1, 9, 17, 25, 33, 41, 49, 57]] + 
                [lvl for lvl in [3] if (i % 16) in [2, 10, 18, 26, 34, 42, 50, 58]] +
                [lvl for lvl in [4] if (i % 16) in [4, 12, 20, 28, 36, 44, 52, 60]] +
                [lvl for lvl in [5] if (i % 16) in [13, 21, 29, 37, 45, 53, 61]] +
                [lvl for lvl in [6] if i in [24, 59]] +
                [lvl for lvl in [7] if i in [56]] +
                [lvl for lvl in [1] if i % 8 == 0 or i % 64 == 0]
        for i in range(1, 65)
    }
}

def load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        try:
            with open(SCHEDULE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_SCHEDULE
    return DEFAULT_SCHEDULE

def save_cards(cards):
    with open(DATA_FILE, "w") as f:
        json.dump(cards, f, indent=2)

def load_cards():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def get_today_day(start_date):
    today = datetime.date.today()
    start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    delta = (today - start).days
    return (delta % 64) + 1

def get_today_levels(schedule, day):
    return list(map(int, schedule["schedule"].get(str(day), [1])))

# ---------------- STREAMLIT APP ----------------

st.set_page_config(page_title="Leitner Box", layout="wide")

st.title("📚 Leitner Box Flashcards")
cards = load_cards()
schedule = load_schedule()
today_day = get_today_day(schedule["start_date"])
today_levels = get_today_levels(schedule, today_day)

st.sidebar.header("📅 Today is Day {}".format(today_day))
st.sidebar.markdown("**Reviewing Levels:** {}".format(", ".join(map(str, today_levels))))

# Menu Bar
with st.expander("📥 Import Cards"):
    text_input = st.text_area("Paste terms (format: Question::Answer::Tag::Level)", height=200)
    if st.button("Import Cards"):
        count = 0
        for line in text_input.strip().split("\n"):
            parts = line.strip().split("::")
            if len(parts) >= 4:
                question, answer, tag, level = parts
                cards.append({
                    "question": question.strip(),
                    "answer": answer.strip(),
                    "tag": tag.strip(),
                    "level": int(level),
                    "streak": 0
                })
                count += 1
        save_cards(cards)
        st.success(f"✅ Imported {count} new cards.")

with st.expander("🗂 Organize Levels"):
    for i, card in enumerate(cards):
        col1, col2, col3 = st.columns([5, 2, 2])
        with col1:
            st.markdown(f"**{card['question']}**  \n*{card['tag']}*", unsafe_allow_html=True)
        with col2:
            new_level = st.selectbox(f"Level:", options=list(range(1, 8)), index=card["level"] - 1, key=f"level_{i}")
            card["level"] = new_level
        with col3:
            if st.button("❌ Delete", key=f"del_{i}"):
                cards.pop(i)
                save_cards(cards)
                st.experimental_rerun()
    save_cards(cards)

# Review Cards for Today
review_cards = [card for card in cards if card["level"] in today_levels]

st.subheader("📝 Review")
if review_cards:
    card = random.choice(review_cards)
    with st.form(key="quiz"):
        st.write(f"**Question:** {card['question']}")
        user_answer = st.text_input("Your Answer")
        submitted = st.form_submit_button("Submit")
        if submitted:
            if user_answer.strip().lower() == card["answer"].strip().lower():
                card["streak"] += 1
                if card["level"] < 7:
                    card["level"] += 1
                st.success("✅ Correct!")
            else:
                card["streak"] = 0
                card["level"] = 1
                st.error(f"❌ Incorrect! Answer was: {card['answer']}")
            save_cards(cards)
            st.experimental_rerun()
    st.caption(f"Remaining cards: {len(review_cards)}")
else:
    st.success("🎉 You're done for today! No cards to review.")

# Footer
st.markdown("---")
st.caption("Built with ❤️ for spaced repetition.")
