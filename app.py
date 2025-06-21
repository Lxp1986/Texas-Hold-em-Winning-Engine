import tkinter as tk
from tkinter import ttk, messagebox
from poker_logic import run_simulation

# Card constants (DECK is used for refreshing dropdowns)
SUITS = ['H', 'D', 'C', 'S']  # Hearts, Diamonds, Clubs, Spades
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
DECK = sorted([r + s for r in RANKS for s in SUITS]) # Keep deck sorted for consistent dropdowns

class PokerOddsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("德州扑克胜率计算器") # Texas Hold'em Odds Calculator

        # --- Your Hand Frame (你的手牌) ---
        your_hand_frame = ttk.LabelFrame(self.root, text="你的手牌")
        your_hand_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.your_card_vars = [tk.StringVar(value="") for _ in range(2)]
        self.your_card_combos = []

        ttk.Label(your_hand_frame, text="第一张牌:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        combo1 = ttk.Combobox(your_hand_frame, textvariable=self.your_card_vars[0], values=[""] + DECK, width=7, state="readonly")
        combo1.grid(row=0, column=1, padx=5, pady=5)
        self.your_card_combos.append(combo1)

        ttk.Label(your_hand_frame, text="第二张牌:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        combo2 = ttk.Combobox(your_hand_frame, textvariable=self.your_card_vars[1], values=[""] + DECK, width=7, state="readonly")
        combo2.grid(row=0, column=3, padx=5, pady=5)
        self.your_card_combos.append(combo2)

        # --- Community Card Frame (公共牌) ---
        community_frame = ttk.LabelFrame(self.root, text="公共牌")
        community_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        
        self.community_card_vars = [tk.StringVar(value="") for _ in range(5)]
        self.community_card_combos = []
        community_labels = ["翻牌1", "翻牌2", "翻牌3", "转牌", "河牌"] # Flop1, Flop2, Flop3, Turn, River
        
        for i in range(5):
            ttk.Label(community_frame, text=community_labels[i] + ":").grid(row=i // 3, column=(i % 3) * 2, padx=5, pady=5, sticky="w")
            combo = ttk.Combobox(community_frame, textvariable=self.community_card_vars[i], values=[""] + DECK, width=7, state="readonly")
            combo.grid(row=i // 3, column=(i % 3) * 2 + 1, padx=5, pady=5)
            self.community_card_combos.append(combo)

        # --- Configuration Frame (设置) ---
        config_frame = ttk.LabelFrame(self.root, text="设置")
        config_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        ttk.Label(config_frame, text="对手数量:").grid(row=0, column=0, padx=5, pady=5, sticky="w") # Number of Opponents
        self.num_opponents_var = tk.StringVar(value="1")
        # Max opponents: 8 for a 9-handed game (1 hero + 8 opponents). Min 1 opponent.
        self.num_opponents_spinbox = ttk.Spinbox(config_frame, from_=1, to=8, textvariable=self.num_opponents_var, width=5) 
        self.num_opponents_spinbox.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # --- Controls Frame (控制) ---
        controls_frame = ttk.Frame(self.root)
        controls_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

        self.calculate_button = ttk.Button(controls_frame, text="计算胜率", command=self.calculate_odds) # Calculate Odds
        self.calculate_button.pack(side=tk.LEFT, padx=5)

        self.reset_button = ttk.Button(controls_frame, text="重置", command=self.reset_all) # Reset
        self.reset_button.pack(side=tk.LEFT, padx=5)

        # --- Results Display Frame (结果) ---
        results_frame = ttk.LabelFrame(self.root, text="结果")
        results_frame.grid(row=4, column=0, padx=10, pady=10, sticky="ew")

        self.win_percentage_var = tk.StringVar(value="胜率: 0.00%") # Win %
        self.tie_percentage_var = tk.StringVar(value="平局率: 0.00%") # Tie %

        ttk.Label(results_frame, textvariable=self.win_percentage_var).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        ttk.Label(results_frame, textvariable=self.tie_percentage_var).grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # Set up card selection callbacks
        for var in self.your_card_vars:
            var.trace_add("write", self.card_selected_callback)
        for var in self.community_card_vars:
            var.trace_add("write", self.card_selected_callback)

        self.refresh_all_card_dropdown_values() # Initial population of dropdowns

    def get_all_selected_cards(self):
        """Helper to get all currently selected cards from the UI."""
        selected = set()
        for var in self.your_card_vars:
            val = var.get()
            if val: selected.add(val)
        for var in self.community_card_vars:
            val = var.get()
            if val: selected.add(val)
        return selected

    def card_selected_callback(self, var_name, index, mode):
        """Called when a card selection changes. Refreshes all dropdowns."""
        self.refresh_all_card_dropdown_values()

    def refresh_all_card_dropdown_values(self):
        """Refreshes the 'values' list of all card Comboboxes."""
        selected_cards_on_ui = self.get_all_selected_cards()
        available_cards_for_all = [""] + sorted(list(set(DECK) - selected_cards_on_ui))

        all_combos = self.your_card_combos + self.community_card_combos
        all_vars = self.your_card_vars + self.community_card_vars

        for i, combo in enumerate(all_combos):
            current_var = all_vars[i]
            current_selection = current_var.get()
            
            if current_selection: # If a card is selected in this specific combo
                # Its list should be [empty, its_current_selection] + other_available_cards
                combo['values'] = ["", current_selection] + sorted(list(set(DECK) - (selected_cards_on_ui - {current_selection})))
            else: # If this combo is empty
                combo['values'] = available_cards_for_all
            # Ensure the variable retains its value if it's still valid, or clears if not
            # This should ideally not be necessary if logic is perfect, but as a safeguard:
            if current_selection not in combo['values']:
                 current_var.set("")


    def calculate_odds(self):
        your_hand = [var.get() for var in self.your_card_vars if var.get()]
        community_cards = [var.get() for var in self.community_card_vars if var.get()]

        if len(your_hand) == 0 : # Require at least one card for hero
             messagebox.showwarning("输入错误", "请至少为“你的手牌”选择一张牌。")
             return
        if len(your_hand) == 1: # If only one card is selected for hero, ensure the second is empty for processing
            if self.your_card_vars[0].get():
                your_hand_for_sim = [self.your_card_vars[0].get(), ""]
            else:
                your_hand_for_sim = ["", self.your_card_vars[1].get()]
        else:
            your_hand_for_sim = your_hand


        # Validate community cards (must be 0, 3, 4, or 5)
        num_community_cards = len(community_cards)
        if num_community_cards not in [0, 3, 4, 5]:
            messagebox.showwarning("输入错误", "公共牌必须是0张、3张（翻牌）、4张（转牌）或5张（河牌）。")
            return

        try:
            num_opponents = int(self.num_opponents_var.get())
            if not (1 <= num_opponents <= 8): # Max 8 opponents for a 9-handed game
                messagebox.showwarning("输入错误", "对手数量必须在 1 到 8 之间。")
                return
        except ValueError:
            messagebox.showwarning("输入错误", "对手数量必须是一个有效的数字。")
            return

        num_total_players = 1 + num_opponents
        # run_simulation expects a list of hands; only hero's hand is specified.
        player_hands_str_initial = [your_hand_for_sim] 
        # The simulation will fill the rest of the hands for opponents randomly.

        num_simulations = 5000  # Default, could be made configurable

        try:
            self.calculate_button.config(state=tk.DISABLED)
            self.root.update_idletasks()
            
            status_message = f"正在为你的手牌对{num_opponents}个对手进行{num_simulations}次模拟计算..."
            print(status_message) # Log to console, consider a status bar in UI for future

            results = run_simulation(
                player_hands_str_initial=player_hands_str_initial,
                community_cards_str_initial=community_cards,
                num_total_players=num_total_players,
                num_simulations=num_simulations
            )

            if results and len(results) > 0:
                hero_results = results[0] # Hero is always player 0
                self.win_percentage_var.set(f"胜率: {hero_results.get('wins', 0.0):.2f}%")
                self.tie_percentage_var.set(f"平局率: {hero_results.get('ties', 0.0):.2f}%")
                messagebox.showinfo("计算完成", "胜率计算已完成。")
            else:
                messagebox.showerror("计算错误", "模拟计算未能返回有效结果。")

        except ValueError as ve:
            messagebox.showerror("输入错误", f"发生错误: {ve}")
        except Exception as e:
            messagebox.showerror("未知错误", f"发生未知错误: {e}")
        finally:
            self.calculate_button.config(state=tk.NORMAL)


    def reset_all(self):
        for var in self.your_card_vars:
            var.set("")
        for var in self.community_card_vars:
            var.set("")
        
        self.win_percentage_var.set("胜率: 0.00%")
        self.tie_percentage_var.set("平局率: 0.00%")
        self.num_opponents_var.set("1") # Reset opponents to 1 (or a preferred default)
        
        # Crucially, refresh dropdowns to make all cards available again
        self.refresh_all_card_dropdown_values() 
        
        # messagebox.showinfo("提示", "所有选择已重置。") # Optional: can be a bit noisy
        print("所有选择已重置。")


if __name__ == '__main__':
    main_root = tk.Tk()
    app = PokerOddsApp(main_root)
    main_root.mainloop()
