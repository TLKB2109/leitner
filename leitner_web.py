import streamlit as st
import json
import os
from datetime import datetime
import random

DATA_FILE = "terms.json"
SCHEDULE_FILE = "schedule.json"

# ============ Loaders and Savers ============

def load_terms():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_terms(terms):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(terms, f, ensure_ascii=False, indent=2)

def load_schedule():
    if not os.path.exists(SCHEDULE_FILE):
        return {"start_date": "2025-04-19", "schedule": {}}
    with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ============ Helpers ============

def get_today_day(start_date_str):
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    today = datetime.now().date()
    delta = (today - start_date).days + 1
    return (delta - 1) % 64 + 1

def get_levels_for_today(schedule_data):
    today = get_today_day(schedule_data["start_date"])
    return schedule_data["schedule"].get(str(today), [])

def get_cards_for_today(terms, levels, completed_fronts):
    return [card for card in terms if card["level"] in levels and card["front"] not in completed_fronts]

def render_card(card):
    st.markdown(f"**Q:** {card['front']}")
    show = st.button("Show Answer")
    if show:
        st.success(f"A: {card['back']}")

def update_card_level(card, correct):
    if correct:
        card["level"] = min(card["level"] + 1, 7)
    else:
        card["level"] = 1

# ============ Streamlit App ============

def main():
    st.set_page_config(page_title="Leitner Box", layout="wide")
    st.title("🧠 Leitner Box (Daily Review)")

    schedule_data = load_schedule()
    levels_today = get_levels_for_today(schedule_data)
    st.subheader(f"📅 Today's levels: {levels_today} — ", divider="blue")

    # Session state for completed cards
    if "completed" not in st.session_state:
        st.session_state.completed = []

    # Load terms
    terms = load_terms()
    due_cards = get_cards_for_today(terms, levels_today, st.session_state.completed)

    if due_cards:
        random.shuffle(due_cards)
        current = due_cards[0]
        st.write(f"**{len(due_cards)} cards due**")
        st.markdown(f"**Q:** {current['front']}")
        if st.button("Show Answer"):
            st.info(f"A: {current['back']}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Correct"):
                    update_card_level(current, True)
                    st.session_state.completed.append(current["front"])
                    save_terms(terms)
                    st.experimental_rerun()
            with col2:
                if st.button("❌ Incorrect"):
                    update_card_level(current, False)
                    st.session_state.completed.append(current["front"])
                    save_terms(terms)
                    st.experimental_rerun()
    else:
        st.success("🎉 You're done for today!")

    st.sidebar.header("🗂️ Menu")

    # Import Cards
    st.sidebar.subheader("📥 Import Cards")
    raw_input = st.sidebar.text_area("Paste terms (Question::Answer::Tag::Level format)")
    if st.sidebar.button("Import"):
        new_cards = []
        for line in raw_input.strip().split("\n"):
            parts = line.strip().split("::")
            if len(parts) != 4:
                continue
            front, back, tag, level = parts
            new_cards.append({
                "front": front.strip(),
                "back": back.strip(),
                "tag": tag.strip(),
                "level": int(level)
            })
        terms += new_cards
        save_terms(terms)
        st.sidebar.success(f"✅ Imported {len(new_cards)} new cards.")

    # Export Cards
    if st.sidebar.button("📤 Export Cards"):
        st.sidebar.download_button("Download terms.json", json.dumps(terms, ensure_ascii=False, indent=2), file_name="terms.json")

    # Reset Today
    if st.sidebar.button("🔄 Reset Today"):
        st.session_state.completed = []
        st.experimental_rerun()

    # Level Distribution
    st.sidebar.subheader("📊 Level Distribution")
    level_counts = {i: 0 for i in range(1, 8)}
    for card in terms:
        level_counts[card["level"]] += 1
    total = len(terms)
    for level, count in level_counts.items():
        percent = (count / total * 100) if total else 0
        st.sidebar.write(f"Level {level}: {count} cards ({percent:.1f}%)")

if __name__ == "__main__":
    main()
