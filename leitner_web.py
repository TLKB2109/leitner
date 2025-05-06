import streamlit as st
import json
import os
from datetime import datetime
import random

DATA_FILE = "terms.json"
if os.path.exists("custom_schedule.json"):
    SCHEDULE_FILE = "custom_schedule.json"
else:
    SCHEDULE_FILE = "schedule.json"

# ================= Loaders and Savers ================= #

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

# ================= Helpers ================= #

def get_today_day(start_date_str):
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    today = datetime.now()
    return (today - start_date).days % 64 + 1

def get_cards_for_today(terms, schedule, today_day, completed_ids):
    today_levels = list(map(int, schedule[str(today_day)]))
    due_cards = [card for card in terms if card["level"] in today_levels and card["id"] not in completed_ids]
    random.shuffle(due_cards)
    return due_cards

def promote_card(card):
    if card["level"] < 7:
        card["level"] += 1

def reset_card(card):
    card["level"] = 1

def count_cards_by_level(terms):
    counts = {i: 0 for i in range(1, 8)}
    for card in terms:
        counts[card["level"]] += 1
    return counts

# ================= Main App ================= #

def main():
    st.title("📘 Leitner Box Review")

    terms = load_terms()
    schedule = load_schedule()
    today_day = get_today_day(schedule["start_date"])
    today_key = f"day_{today_day}"

    if "session_data" not in st.session_state:
        st.session_state.session_data = {}
    if today_key not in st.session_state.session_data:
        st.session_state.session_data[today_key] = {"completed": set()}

    completed_ids = st.session_state.session_data[today_key]["completed"]
    cards = get_cards_for_today(terms, schedule["schedule"], today_day, completed_ids)

    st.subheader(f"📅 Day {today_day}: Reviewing Levels {schedule['schedule'][str(today_day)]}")
    st.markdown(f"### Cards due today: {len(cards)}")

    if cards:
        card = cards[0]
        with st.form(key=f"review_form_{card['id']}"):
            st.write(f"**Question:** {card['question']}")
            show_answer = st.form_submit_button("Show Answer")
            if show_answer:
                st.success(f"**Answer:** {card['answer']}")
                correct = st.form_submit_button("✅ Got it right")
                wrong = st.form_submit_button("❌ Missed it")
                if correct:
                    promote_card(card)
                    completed_ids.add(card["id"])
                    save_terms(terms)
                    st.experimental_rerun()
                elif wrong:
                    reset_card(card)
                    completed_ids.add(card["id"])
                    save_terms(terms)
                    st.experimental_rerun()
    else:
        st.success("🎉 You finished all cards for today!")

    # Sidebar tools
    with st.sidebar:
        st.header("📥 Import Cards")
        upload_input = st.text_area("Paste terms (Question::Answer::Tag::Level format)")
        if st.button("Import"):
            new_cards = []
            existing_ids = {card["id"] for card in terms}
            for line in upload_input.splitlines():
                if "::" in line:
                    parts = line.strip().split("::")
                    if len(parts) == 4:
                        q, a, tag, lvl = parts
                        card_id = f"{q.strip()}::{a.strip()}"
                        if card_id not in existing_ids:
                            new_cards.append({
                                "id": card_id,
                                "question": q.strip(),
                                "answer": a.strip(),
                                "tag": tag.strip(),
                                "level": int(lvl)
                            })
            terms.extend(new_cards)
            save_terms(terms)
            st.success(f"✅ Imported {len(new_cards)} new cards.")

        st.header("📊 Level Distribution")
        counts = count_cards_by_level(terms)
        total = sum(counts.values())
        for level in range(1, 8):
            count = counts[level]
            pct = (count / total * 100) if total > 0 else 0
            st.write(f"Level {level}: {count} cards ({pct:.1f}%)")

        st.header("🛠 Manage Levels")
        all_ids = [card["id"] for card in terms]
        selected_id = st.selectbox("Select a card to move", all_ids) if all_ids else None
        if selected_id:
            selected_card = next(card for card in terms if card["id"] == selected_id)
            st.markdown(f"**{selected_card['question']} → {selected_card['answer']}**")
            new_level = st.selectbox("Move to level", list(range(1, 8)), index=selected_card["level"] - 1)
            if st.button("Update Level"):
                selected_card["level"] = new_level
                save_terms(terms)
                st.success("✅ Level updated!")

if __name__ == "__main__":
    main()
