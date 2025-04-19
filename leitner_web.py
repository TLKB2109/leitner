def review_cards(card_list):
    if not card_list:
        st.info("No cards to review.")
        return

    # Lock the current card in session state
    if "current_card" not in st.session_state or st.session_state.current_card not in card_list:
        st.session_state.current_card = random.choice(card_list)

    card = st.session_state.current_card

    st.markdown(f"### ❓ [Box {card['box']}] {card['front']}")
    if st.button("Show Answer"):
        st.session_state.show_answer = True

    if st.session_state.get("show_answer", False):
        st.markdown(f"**Answer:** {card['back']}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Got it"):
                if card['box'] < BOX_COUNT:
                    card['box'] += 1
                card['missed_count'] = 0
                card['last_reviewed'] = str(datetime.now().date())
                save_cards(cards)
                st.session_state.current_card = random.choice(card_list)
                st.session_state.show_answer = False
                st.success(f"Moved to Box {card['box']}")
                st.experimental_rerun()

        with col2:
            if st.button("❌ Missed it"):
                card['box'] = 1
                card['missed_count'] = card.get('missed_count', 0) + 1
                card['last_reviewed'] = str(datetime.now().date())
                save_cards(cards)
                st.session_state.current_card = random.choice(card_list)
                st.session_state.show_answer = False
                st.error("Moved to Box 1")
                st.experimental_rerun()
