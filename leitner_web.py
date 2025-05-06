import streamlit as st
import json
import os
from datetime import datetime
import random

DATA_FILE = "terms.json"
SCHEDULE_FILE = "schedule.json"

# ========== Loaders and Savers ==========

def load_terms():
    if not os.path.exists(DATA_FILE):
        return []
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
        return {
            "start_date": "2025-04-19",
            "schedule": {
                str(day): levels for day, levels in zip(
                    range(1, 65),
                    [[2, 1], [3, 1], [2, 1], [4, 1], [2, 1], [3, 1], [2, 1], [1], [2, 1], [3, 1], [2, 1], [5, 1],
                     [4, 2, 1], [3, 1], [2, 1], [1], [2, 1], [3, 1], [2, 1], [4, 1], [2, 1], [3, 1], [2, 1], [6, 1],
                     [2, 1], [3, 1], [2, 1], [5, 1], [4, 2, 1], [3, 1], [2, 1], [1], [2, 1], [3, 1], [2, 1], [4, 1],
                     [2, 1], [3, 1], [2, 1], [1], [2, 1], [3, 1], [2, 1], [5, 1], [4, 2, 1], [3, 1], [2, 1], [1],
                     [2, 1], [3, 1], [2, 1], [4, 1], [2, 1], [3, 1], [2, 1], [7, 1], [2, 1], [3, 1], [6, 2, 1],
                     [5, 1], [4, 2, 1], [3, 1], [2, 1], [1]]
                )
            }
        }

def get_today_day(start_date_str):
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    today = datetime.now().date()
    return (today - start_date).days % 64 + 1

def get_cards_for_today(terms, levels_today):
    return [t for t in terms if t["level"] in levels_today]

# ========== Streamlit App ==========

def main():
    st.title("🧠 Leitner Box (Daily Review)")
    schedule_data = load_schedule()
    terms = load_terms()
    today_day = get_today_day(schedule_data["start_date"])
    levels_today = schedule_data["schedule"].get(str(today_day), [])
    cards_today = get_cards_for_today(terms, levels_today)

    # Sidebar
    st.sidebar.header("📂 Menu")

    with st.sidebar.expander("📥 Import Cards"):
        import_text = st.text_area("Paste terms (Question::Answer::Tag::Level format)")
        if st.button("Import"):
            if import_text:
                new_terms = []
                for line in import_text.strip().split("\n"):
                    parts = line.strip().split("::")
                    if len(parts) == 4:
                        q, a, tag, lvl = parts
                        new_terms.append({
                            "question": q.strip(),
                            "answer": a.strip(),
                            "tag": tag.strip(),
                            "level": int(lvl),
                            "history": []
                        })
                terms.extend(new_terms)
                save_terms(terms)
                st.success(f"✅ Imported {len(new_terms)} new cards.")

    if st.sidebar.button("📤 Export Cards"):
        st.download_button(
            "Download terms.json",
            data=json.dumps(terms, indent=2, ensure_ascii=False),
            file_name="terms.json",
            mime="application/json"
        )

    # Level distribution
    st.sidebar.markdown("### 📊 Level Distribution")
    total = len(terms)
    for lvl in range(1, 8):
        count = sum(1 for t in terms if t["level"] == lvl)
        percent = (count / total * 100) if total > 0 else 0
        st.sidebar.write(f"Level {lvl}: {count} cards ({percent:.1f}%)")

    # Review Section
    st.subheader(f"📅 Today's levels: {levels_today} —")

    if cards_today:
        st.write(f"🃏 {len(cards_today)} card(s) due today.")
        random.shuffle(cards_today)
        for i, card in enumerate(cards_today):
            with st.form(key=f"card_{i}"):
                st.markdown(f"**{card['question']}** ({card['tag']})")
                answer = st.text_input("Your answer")
                submitted = st.form_submit_button("Submit")
                if submitted:
                    correct = answer.strip().lower() == card["answer"].strip().lower()
                    if correct:
                        st.success("✅ Correct!")
                        card["level"] = min(card["level"] + 1, 7)
                    else:
                        st.error(f"❌ Incorrect. Correct answer: {card['answer']}")
                        card["level"] = 1
                    card["history"].append({
                        "date": datetime.now().isoformat(),
                        "correct": correct
                    })
                    save_terms(terms)
                    st.rerun()
    else:
        st.success("🎉 You're done for today!")

if __name__ == "__main__":
    main()
