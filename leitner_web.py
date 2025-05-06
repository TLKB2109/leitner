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
    default_schedule = {
        "start_date": "2025-04-19",
        "schedule": {str(day): [1] for day in range(1, 65)}
    }
    if not os.path.exists(SCHEDULE_FILE):
        return default_schedule
    with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ========== Helpers ==========

def get_today_day(start_date_str):
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    today = datetime.today()
    delta = (today - start_date).days
    return (delta % 64) + 1

def get_cards_for_today(terms, schedule_data):
    today_day = get_today_day(schedule_data["start_date"])
    levels_today = schedule_data["schedule"].get(str(today_day), [])
    due_cards = [card for card in terms if card["level"] in levels_today]
    return due_cards, today_day, levels_today

def update_card_level(card, correct):
    if correct:
        card["level"] = min(card["level"] + 1, 7)
    else:
        card["level"] = 1

# ========== App ==========

def main():
    st.title("📘 Leitner Box Review")

    schedule_data = load_schedule()
    terms = load_terms()
    due_cards, today_day, levels_today = get_cards_for_today(terms, schedule_data)

    # Sidebar: Import
    with st.sidebar:
        st.subheader("📥 Import Cards")
        import_input = st.text_area("Paste terms (Question::Answer::Tag::Level format)")
        if st.button("Import"):
            new_cards = []
            for line in import_input.strip().split("\n"):
                try:
                    q, a, tag, lvl = line.split("::")
                    new_cards.append({
                        "front": q.strip(),
                        "back": a.strip(),
                        "tag": tag.strip(),
                        "level": int(lvl.strip())
                    })
                except ValueError:
                    continue
            terms.extend(new_cards)
            save_terms(terms)
            st.success(f"✅ Imported {len(new_cards)} new cards.")

        # Sidebar: Level distribution
        st.subheader("📊 Level Distribution")
        levels = [card["level"] for card in terms]
        for lvl in range(1, 8):
            count = levels.count(lvl)
            pct = (count / len(terms) * 100) if terms else 0
            st.write(f"Level {lvl}: {count} cards ({pct:.1f}%)")

    st.subheader(f"📅 Day {today_day}: Reviewing Levels {levels_today}")
    st.write(f"Cards due today: {len(due_cards)}")

    if "completed_cards" not in st.session_state:
        st.session_state.completed_cards = []

    remaining = [card for card in due_cards if card["front"] not in st.session_state.completed_cards]

    if remaining:
        card = random.choice(remaining)
        st.markdown(f"**Q: {card['front']}**")
        if st.button("Show Answer"):
            st.markdown(f"**A: {card['back']}**")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ I got it right"):
                    update_card_level(card, True)
                    st.session_state.completed_cards.append(card["front"])
            with col2:
                if st.button("❌ I got it wrong"):
                    update_card_level(card, False)
                    st.session_state.completed_cards.append(card["front"])
            save_terms(terms)
            st.experimental_rerun()
    else:
        st.success("🎉 You finished all cards for today!")

if __name__ == "__main__":
    main()
