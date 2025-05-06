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
    with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ========== Utilities ==========
def get_today_day(start_date_str):
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    today = datetime.today()
    delta = (today - start_date).days
    return (delta % 64) + 1

def get_cards_for_today(terms, levels_today):
    return [card for card in terms if card["level"] in levels_today]

def promote(card):
    if card["level"] < 7:
        card["level"] += 1

def reset(card):
    card["level"] = 1

# ========== Main App ==========
def main():
    st.title("📘 Leitner Box Review")

    terms = load_terms()
    schedule_data = load_schedule()
    today_day = get_today_day(schedule_data["start_date"])
    levels_today = schedule_data["schedule"].get(str(today_day), [])
    st.subheader(f"📅 Day {today_day}: Reviewing Levels {levels_today}")

    if "completed_fronts" not in st.session_state:
        st.session_state.completed_fronts = []

    cards_today = [card for card in get_cards_for_today(terms, levels_today)
                   if card["front"] not in st.session_state.completed_fronts]

    if not cards_today:
        st.success("🎉 You finished all cards for today!")
    else:
        card = random.choice(cards_today)
        with st.form(key="card_form"):
            st.write(f"**{card['front']}**")
            user_answer = st.text_input("Your answer")
            submitted = st.form_submit_button("Submit")
            if submitted:
                if user_answer.strip().lower() == card["back"].strip().lower():
                    st.success("✅ Correct!")
                    promote(card)
                else:
                    st.error(f"❌ Incorrect. Answer: {card['back']}")
                    reset(card)
                st.session_state.completed_fronts.append(card["front"])
                save_terms(terms)
                st.experimental_rerun()

    st.divider()
    with st.sidebar:
        st.header("📥 Import Cards")
        import_input = st.text_area("Paste terms (Question::Answer::Tag::Level format)")
        if st.button("Import"):
            new_terms = []
            for line in import_input.strip().splitlines():
                if "::" in line:
                    try:
                        front, back, tag, level = [part.strip() for part in line.split("::")]
                        new_terms.append({
                            "front": front,
                            "back": back,
                            "tag": tag,
                            "level": int(level)
                        })
                    except:
                        continue
            terms += new_terms
            save_terms(terms)
            st.success(f"✅ Imported {len(new_terms)} new cards.")

        st.header("📊 Level Distribution")
        level_counts = {i: 0 for i in range(1, 8)}
        for card in terms:
            level_counts[card["level"]] += 1
        total = len(terms)
        for level, count in sorted(level_counts.items()):
            percent = (count / total * 100) if total > 0 else 0
            st.write(f"Level {level}: {count} cards ({percent:.1f}%)")

        if st.button("🔁 Reset Today's Session"):
            st.session_state.completed_fronts = []
            st.experimental_rerun()

if __name__ == "__main__":
    main()
