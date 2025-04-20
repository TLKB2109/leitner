import streamlit as st
import json
import os
import random
from datetime import datetime

DATA_FILE = 'leitner_cards.json'
MAX_LEVEL = 7

def load_cards():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_cards(cards):
    with open(DATA_FILE, 'w') as f:
        json.dump(cards, f, indent=2)

cards = load_cards()

def add_card():
    st.header("➕ Add a New Card")
    with st.form("add_card_form"):
        front = st.text_input("Question")
        back = st.text_input("Answer")
        submitted = st.form_submit_button("Add Card")
        if submitted and front and back:
            cards.append({
                "front": front,
                "back": back,
                "level": 1,
                "last_reviewed": str(datetime.now().date())
            })
            save_cards(cards)
            st.success("✅ Card added!")

def review_cards():
    st.header("🧠 Review Cards")
    review_pool = [c for c in cards]
    if not review_pool:
        st.info("No cards yet. Add some first!")
        return

    if "current_card" not in st.session_state:
        st.session_state.current_card = random.choice(review_pool)

    card = st.session_state.current_card
    st.markdown(f"### ❓ {card['front']} (Level {card['level']})")

    if st.button("Show Answer"):
        st.session_state.show_answer = True

    if st.session_state.get("show_answer", False):
        st.markdown(f"**Answer:** {card['back']}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Got it"):
                if card["level"] < MAX_LEVEL:
                    card["level"] += 1
                card["last_reviewed"] = str(datetime.now().date())
                save_cards(cards)
                st.session_state.show_answer = False
                st.session_state.current_card = random.choice(review_pool)
                st.experimental_rerun()
        with col2:
            if st.button("❌ Missed it"):
                card["level"] = 1
                card["last_reviewed"] = str(datetime.now().date())
                save_cards(cards)
                st.session_state.show_answer = False
                st.session_state.current_card = random.choice(review_pool)
                st.experimental_rerun()

def overview():
    st.header("📊 Overview by Level")
    for level in range(1, MAX_LEVEL + 1):
        level_cards = [c for c in cards if c["level"] == level]
        with st.expander(f"📘 Level {level} ({len(level_cards)} cards)"):
            for card in level_cards:
                st.write(f"- {card['front']} → {card['back']}")

page = st.sidebar.selectbox("📚 Menu", ["Add Card", "Review", "Overview"])
st.title("📱 Leitner Box")

if page == "Add Card":
    add_card()
elif page == "Review":
    review_cards()
elif page == "Overview":
    overview()
