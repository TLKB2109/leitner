def review_cards(card_list):
    if not card_list:
        st.success("🎉 All done for today!")
        return

    # How many cards left
    st.info(f"Cards left today: **{len(card_list) - st.session_state.get('current_card_index', 0)}**")

    if "current_card_index" not in st.session_state or st.session_state.current_card_index >= len(card_list):
        st.session_state.current_card_index = 0
        random.shuffle(card_list)

    card = card_list[st.session_state.current_card_index]

    st.markdown(f"### ❓ [Level {card['level']}] {card['front']}")
    if st.button("Show Answer"):
        st.session_state.show_answer = True

    if st.session_state.get("show_answer", False):
        st.markdown(f"**Answer:** {card['back']}")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Got it"):
                # Level up
                card['level'] = min(card['level'] + 1, MAX_LEVEL)
                card['last_reviewed'] = str(datetime.now().date())
                card['missed_count'] = 0
                save_cards(cards)

                st.session_state.reviewed_ids.add(id(card))
                st.session_state.current_card_index += 1
                st.session_state.show_answer = False
                st.rerun()

        with col2:
            if st.button("❌ Missed it"):
                # Reset to Level 1
                card['level'] = 1
                card['missed_count'] = card.get('missed_count', 0) + 1
                card['last_reviewed'] = str(datetime.now().date())
                save_cards(cards)

                st.session_state.reviewed_ids.add(id(card))
                st.session_state.current_card_index += 1
                st.session_state.show_answer = False
                st.rerun()
