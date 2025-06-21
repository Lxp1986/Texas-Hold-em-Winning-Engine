from deuces import Card, Evaluator, Deck

# Initialize evaluator globally as it's stateless and can be reused
evaluator = Evaluator()

def card_str_to_deuces_card(card_str):
    """
    Converts a card string like "As" or "Th" to a deuces.Card object.
    """
    if not card_str or len(card_str) != 2:
        raise ValueError(f"无效的卡牌字符格式: {card_str}") # "Invalid card string format"
    try:
        return Card.new(card_str)
    except Exception as e: # Catch errors from Card.new() like invalid rank/suit
        raise ValueError(f"无效卡牌: '{card_str}'. {e}") # "Invalid card"

def get_hand_strength(hole_cards_str, community_cards_str):
    """
    Calculates the strength of a poker hand.

    Args:
        hole_cards_str (list[str]): A list of two card strings (e.g., ["As", "Kd"]).
        community_cards_str (list[str]): A list of 3 to 5 card strings for community cards.

    Returns:
        tuple: (score, hand_class_str)
               - score (int): The numerical rank of the hand (lower is better, 1-7462).
               - hand_class_str (str): Human-readable string of the hand type (e.g., "Straight Flush").
    """
    if not hole_cards_str or len(hole_cards_str) != 2:
        raise ValueError("手牌必须是两张牌的列表。") # "Hole cards must be a list of two card strings."
    # Community cards can be 0, 3, 4, or 5. If 0, evaluator handles it.
    # For direct evaluation, deuces needs at least 3 community cards to make a 5 card hand with 2 hole cards.
    # However, our simulation will always fill it to 5.
    # This function is more for direct evaluation if needed, less so for the direct simulation path.
    # Let's adjust the check for community_cards_str for its direct usage:
    if not (0 <= len(community_cards_str) <= 5):
        raise ValueError("公共牌必须是0到5张牌的列表。") # "Community cards must be a list of 0 to 5 card strings."


    hole_cards_deuces = [card_str_to_deuces_card(c) for c in hole_cards_str]
    community_cards_deuces = [card_str_to_deuces_card(c) for c in community_cards_str]
    
    # If community cards are less than 3, evaluation is not meaningful for a 5-card hand from 7.
    # Deuces evaluator.evaluate expects a board and a hand.
    # If board has < 3 cards, it can still give a score, but it's based on what's available.
    # For our simulation, we always build a full 5-card board before evaluation.
    # This function as a standalone utility should probably reflect what deuces expects or how it behaves.
    # For now, let's assume it's called with enough cards for a standard evaluation context (e.g. river).

    score = evaluator.evaluate(community_cards_deuces, hole_cards_deuces)
    hand_class_int = evaluator.get_rank_class(score)
    hand_class_str = evaluator.class_to_string(hand_class_int)

    return score, hand_class_str

def get_full_deck_deuces():
    """Returns a list of all 52 deuces.Card objects."""
    return Deck().cards

def run_simulation(player_hands_str_initial, community_cards_str_initial, num_total_players, num_simulations):
    """
    Runs a Monte Carlo simulation to calculate poker odds.
    player_hands_str_initial: List of known hole cards for players.
                              For the revised app, this will often be like [["As", "Ks"], [], []]
                              where only the hero's hand is specified.
    """
    player_results = [{'wins': 0, 'ties': 0} for _ in range(num_total_players)]
    known_cards_deuces = set()
    
    player_hands_deuces_initial = []
    for p_idx in range(num_total_players):
        hand_deuces = []
        # Only process specified hands; others will be dealt randomly.
        if p_idx < len(player_hands_str_initial) and player_hands_str_initial[p_idx]:
            for card_s in player_hands_str_initial[p_idx]:
                if card_s: 
                    card_d = card_str_to_deuces_card(card_s)
                    if card_d in known_cards_deuces:
                        # This check is important.
                        raise ValueError(f"重复的卡牌: {card_s}") # "Duplicate card specified"
                    known_cards_deuces.add(card_d)
                    hand_deuces.append(card_d)
        player_hands_deuces_initial.append(hand_deuces) # Will be empty list [] for unspecified hands

    community_cards_deuces_initial = []
    for card_s in community_cards_str_initial:
        if card_s:
            card_d = card_str_to_deuces_card(card_s)
            if card_d in known_cards_deuces:
                raise ValueError(f"重复的卡牌: {card_s}")
            known_cards_deuces.add(card_d)
            community_cards_deuces_initial.append(card_d)

    if len(community_cards_deuces_initial) > 5:
        raise ValueError("公共牌不能超过5张。") # "Cannot have more than 5 community cards."

    for _ in range(num_simulations):
        current_deck_sim = Deck() # Fresh, shuffled deck for this simulation run
        
        sim_deck_cards_list = []
        known_card_ints = {int(c) for c in known_cards_deuces}
        
        for card_in_deck in current_deck_sim.cards:
            if int(card_in_deck) not in known_card_ints:
                sim_deck_cards_list.append(card_in_deck)
        
        current_deck_sim.cards = sim_deck_cards_list # The deck for this simulation run
        
        sim_player_hands = [list(h) for h in player_hands_deuces_initial] # Start with copies of known cards
        sim_community_cards = list(community_cards_deuces_initial)

        # Fill remaining player hole cards for ALL players (including hero if only 1 card specified)
        for p_idx in range(num_total_players):
            while len(sim_player_hands[p_idx]) < 2:
                try:
                    # Ensure current_deck_sim.draw(1) returns a list, so take [0] if it does, or handle if it returns single
                    drawn_card_obj = current_deck_sim.draw(1) # deuces.Deck.draw(N) returns N cards (or a single if N=1)
                    sim_player_hands[p_idx].append(drawn_card_obj)
                except IndexError:
                    raise Exception("牌堆在处理玩家手牌时意外用尽。") # "Deck ran out of cards unexpectedly while dealing player hands."

        # Fill remaining community cards
        while len(sim_community_cards) < 5:
            try:
                drawn_card_obj = current_deck_sim.draw(1)
                sim_community_cards.append(drawn_card_obj)
            except IndexError:
                raise Exception("牌堆在处理公共牌时意外用尽。") # "Deck ran out of cards unexpectedly while dealing community cards."

        player_scores = []
        for p_idx in range(num_total_players):
            score = evaluator.evaluate(sim_community_cards, sim_player_hands[p_idx])
            player_scores.append(score)

        min_score = min(player_scores)
        winners = [i for i, score in enumerate(player_scores) if score == min_score]

        if len(winners) == 1:
            player_results[winners[0]]['wins'] += 1
        else:
            for winner_idx in winners:
                player_results[winner_idx]['ties'] += 1
                
    final_results = []
    for res in player_results:
        final_results.append({
            'wins': (res['wins'] / num_simulations) * 100,
            'ties': (res['ties'] / num_simulations) * 100
        })
        
    return final_results

# --- Example Usage (for testing this file directly) ---
if __name__ == "__main__":
    print("--- 卡牌转换测试 ---")
    try:
        ace_spades_str = "As"
        ace_spades_deuces = card_str_to_deuces_card(ace_spades_str)
        Card.print_pretty_cards([ace_spades_deuces])
        king_hearts_str = "Kh"
        king_hearts_deuces = card_str_to_deuces_card(king_hearts_str)
        Card.print_pretty_cards([king_hearts_deuces])
    except ValueError as e:
        print(f"卡牌转换错误: {e}")
    print("-" * 30)

    print("\n--- 手牌评估测试 ---")
    hole_rf = ["As", "Ks"]
    board_rf = ["Qs", "Js", "Ts"] # Flop only for this test
    # Adjusting get_hand_strength to work with 3 community cards for this test
    score_rf, class_rf = get_hand_strength(hole_rf, board_rf) 
    print(f"手牌: {hole_rf}, 公共牌: {board_rf}, 结果: Score {score_rf}, Class {class_rf}")
    print("-" * 30)

    print("\n--- 蒙特卡洛模拟测试 ---")
    # Test 1: Hero (AA) vs 1 random opponent, pre-flop
    print("测试1: AA vs 1位随机对手 (翻牌前)")
    results_aa_vs_random = run_simulation(
        player_hands_str_initial=[["Ac", "Ad"]], # Hero's hand
        community_cards_str_initial=[],          # Pre-flop
        num_total_players=2,                     # Hero + 1 opponent
        num_simulations=5000
    )
    # We only care about Hero's results (player_results[0])
    print(f"AA vs 随机结果: {results_aa_vs_random[0]}") # Expected: AA wins ~85%

    # Test 2: Hero (KK) vs 3 random opponents, on a specific flop
    print("\n测试2: KK vs 3位随机对手 (翻牌 Ah 7d 2c)")
    results_kk_vs_3_random_flop = run_simulation(
        player_hands_str_initial=[["Kh", "Ks"]],
        community_cards_str_initial=["Ah", "7d", "2c"],
        num_total_players=4, # Hero + 3 opponents
        num_simulations=5000
    )
    print(f"KK vs 3对手 (Ah 7d 2c) 结果: {results_kk_vs_3_random_flop[0]}")

    # Test 3: Invalid card input (duplicate)
    print("\n测试3: 重复卡牌输入")
    try:
        run_simulation(
            player_hands_str_initial=[["As", "Ac"]], # Invalid: As used by hero, Ac specified for opponent
            community_cards_str_initial=["As", "Kd", "Jc"], # Invalid: As also on board
            num_total_players=2,
            num_simulations=100
        )
    except ValueError as e:
        print(f"捕获到预期错误: {e}") # "Caught expected error"

    print("\n测试4: 指定两手牌，翻牌前")
    # AA vs KK preflop
    results_aa_vs_kk = run_simulation(
        player_hands_str_initial=[["As", "Ah"], ["Ks", "Kh"]], 
        community_cards_str_initial=[],      
        num_total_players=2,
        num_simulations=5000 
    )
    print(f"AA vs KK (翻牌前) 结果: P1: {results_aa_vs_kk[0]}, P2: {results_aa_vs_kk[1]}")
    
    print("\n测试5: 你的手牌 vs 8个随机对手 (9人桌)")
    results_hero_vs_8_random = run_simulation(
        player_hands_str_initial=[["Qs", "Qh"]], # Hero QQ
        community_cards_str_initial=[],          # Pre-flop
        num_total_players=9,                     # Hero + 8 opponents
        num_simulations=2000 # Reduced for speed in a 9-handed test
    )
    print(f"你 (QQ) vs 8 随机对手: {results_hero_vs_8_random[0]}")
    # Expected: QQ win rate will be lower, around 1/9 + premium bonus. Maybe ~15-20%?
    # For example, any hand vs 8 random hands has a raw equity of 100/9 = ~11.1%. QQ is better than average.
    # Actual equity for QQ vs 8 random is ~18-19% preflop.
