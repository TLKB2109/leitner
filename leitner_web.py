import streamlit as st
import json
import os
from datetime import datetime
import random

DATA_FILE = "terms.json"
SCHEDULE_FILE = "schedule.json"

# --------------- Loaders & Savers ---------------- #
def load_terms():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_terms(terms):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(terms, f, ensure_ascii=False, indent=2)

def load_schedule():
    default_schedule = {str(day): [] for day in range(1, 65)}
    for day in range(1, 65):
        if day % 2 == 1:
            default_schedule[str(day)].append(1)
        if day % 4 == 0:
            default_schedule[str(day)].append(2)
        if day % 6 == 0:
            default_schedule[str(day)].append(3)
        if day % 8 == 0:
            default_schedule[str(day)].append(4)
        if day % 10 == 0:
            default_schedule[str(day)].append(5)
        if day % 16 == 0:
            default_schedule[str(day)].append(6)
        if day % 32 == 0:
            default_schedule[str(day)].append(7)

    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return default_schedule

# --------------- Helpers ---------------- #
def get_today_day(start_date="2024-04-01"):
    today = datetime.today().date()
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    delta = (today - start).days
    return (delta % 64) + 1

def get_cards_for_today(terms, today_day, schedule):
    levels_today = schedule.get(str(today_day), [])
    cards_today = [card for card in terms if card.get("level", 1) in levels_today]
    return levels_today, cards_today

# --------------- Main App ---------------- #
def main():
    st.set_page_config(page_title="Leitner Box", layout="wide")
    st.title("🧠 Leitner Box (Daily Review)")

    terms = load_terms()
    schedule_data = load_schedule()
    today_day = get_today_day()
    levels_today, cards_today = get_cards_for_today(terms, today_day, schedule_data)

    if "index" not in st.session_state:
        st.session_state.index = 0
    if "answered" not in st.session_state:
        st.session_state.answered = False
    if "correct" not in st.session_state:
        st.session_state.correct = False

    # ---------- Sidebar ---------- #
    with st.sidebar:
        st.header("📂 Menu")

        # Paste-to-import
        with st.expander("📥 Import Cards"):
            input_data = st.text_area("Paste terms (Question::Answer::Tag::Level format)")
            if st.button("Import"):
                if input_data.strip():
                    for line in input_data.strip().split("\n"):
                        parts = line.strip().split("::")
                        if len(parts) == 4:
                            question, answer, tag, level = parts
                            terms.append({
                                "question": question,
                                "answer": answer,
                                "tag": tag,
                                "level": int(level),
                                "history": []
                            })
                    save_terms(terms)
                    st.success("✅ Imported terms!")

        if st.button("📤 Export Cards"):
            st.download_button("Download terms.json", json.dumps(terms, indent=2), "terms.json")

        # Remove broken Reset Today button
        st.markdown("---")
        st.subheader("📊 Level Distribution")
        level_counts = {lvl: 0 for lvl in range(1, 8)}
        for t in terms:
            lvl = t.get("level", 1)
            level_counts[lvl] += 1
        for lvl, count in sorted(level_counts.items()):
            st.write(f"Level {lvl}: {count} cards ({round(100 * count / len(terms), 1) if terms else 0}%)")

    # ---------- Main Review Section ---------- #
    st.subheader(f"📅 Today's levels: {levels_today} —")
    if cards_today and st.session_state.index < len(cards_today):
        card = cards_today[st.session_state.index]
        st.write(f"**Question:** {card['question']} ({card['tag']})")
        user_answer = st.text_input("Your Answer", key="user_answer")

        if st.button("Submit"):
            is_correct = user_answer.strip().lower() == card["answer"].strip().lower()

            if "history" not in card:
                card["history"] = []

            card["history"].append({
                "date": str(datetime.now()),
                "correct": is_correct
            })

            if is_correct:
                st.success("✅ Correct!")
                card["level"] = min(card.get("level", 1) + 1, 7)
            else:
                st.error(f"❌ Incorrect. Correct answer: {card['answer']}")
                card["level"] = 1

            save_terms(terms)
            st.session_state.index += 1
            st.rerun()
    else:
        st.success("🎉 You're done for today!")

if __name__ == "__main__":
    main()
