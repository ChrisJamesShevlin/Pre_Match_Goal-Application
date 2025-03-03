import tkinter as tk
import math

def zip_probability(lam, k, p_zero=0.0):
    """
    Zero-inflated Poisson probability.
    p_zero is set to 0.0 here to remove extra weighting for 0 goals.
    """
    if k == 0:
        return p_zero + (1 - p_zero) * math.exp(-lam)
    return (1 - p_zero) * ((lam ** k) * math.exp(-lam)) / math.factorial(k)

def calculate_probabilities():
    try:
        # --- 1) Retrieve all inputs ---
        avg_goals_home_scored   = float(entries["entry_home_scored"].get())
        avg_goals_away_conceded = float(entries["entry_away_conceded"].get())
        avg_goals_away_scored   = float(entries["entry_away_scored"].get())
        avg_goals_home_conceded = float(entries["entry_home_conceded"].get())
        injuries_home           = int(entries["entry_injuries_home"].get())
        injuries_away           = int(entries["entry_injuries_away"].get())
        position_home           = int(entries["entry_position_home"].get())
        position_away           = int(entries["entry_position_away"].get())
        form_home               = int(entries["entry_form_home"].get())
        form_away               = int(entries["entry_form_away"].get())
        
        home_xg_scored   = float(entries["entry_home_xg_scored"].get())
        away_xg_scored   = float(entries["entry_away_xg_scored"].get())
        home_xg_conceded = float(entries["entry_home_xg_conceded"].get())
        away_xg_conceded = float(entries["entry_away_xg_conceded"].get())
        
        # Live odds for Under/Over 2.5
        live_under_odds = float(entries["entry_live_under_odds"].get())
        live_over_odds  = float(entries["entry_live_over_odds"].get())
        
        # --- 2) Calculate raw expected goals for each team ---
        # Increase or decrease the weighting if desired
        adjusted_home_goals = ((avg_goals_home_scored + home_xg_scored +
                                avg_goals_away_conceded + away_xg_conceded) / 4)
        
        # Reduced injury penalty from 5% to 3% per injury
        adjusted_home_goals *= (1 - 0.03 * injuries_home)
        
        # Reduced position penalty from 0.02 to 0.01
        adjusted_home_goals += form_home * 0.1 - position_home * 0.01
        
        adjusted_away_goals = ((avg_goals_away_scored + away_xg_scored +
                                avg_goals_home_conceded + home_xg_conceded) / 4)
        
        adjusted_away_goals *= (1 - 0.03 * injuries_away)
        adjusted_away_goals += form_away * 0.1 - position_away * 0.01
        
        # --- 3) Model probabilities for Under & Over 2.5 using Poisson ---
        goal_range = 10
        under_prob_model = 0.0
        for i in range(goal_range):
            for j in range(goal_range):
                if (i + j) <= 2:
                    prob_i = zip_probability(adjusted_home_goals, i)
                    prob_j = zip_probability(adjusted_away_goals, j)
                    under_prob_model += prob_i * prob_j
        
        over_prob_model = 1 - under_prob_model
        
        # --- 4) Convert live odds to implied probabilities and normalize them ---
        live_under_prob = 1 / live_under_odds if live_under_odds > 0 else 0
        live_over_prob  = 1 / live_over_odds  if live_over_odds  > 0 else 0
        
        sum_live_probs = live_under_prob + live_over_prob
        if sum_live_probs > 0:
            live_under_prob /= sum_live_probs
            live_over_prob  /= sum_live_probs
        
        # --- 5) Blend the model's probabilities with the live probabilities ---
        # e.g. 70% model, 30% market
        blend_factor = 0.3  # 30% from market, 70% from model
        final_under_prob = under_prob_model * (1 - blend_factor) + live_under_prob * blend_factor
        final_over_prob  = over_prob_model  * (1 - blend_factor) + live_over_prob  * blend_factor
        
        # Normalize final probabilities
        sum_final = final_under_prob + final_over_prob
        if sum_final > 0:
            final_under_prob /= sum_final
            final_over_prob  /= sum_final
        
        # --- 6) Convert final probabilities to final “Fair Odds” (blended) ---
        final_fair_under_odds = 1 / final_under_prob if final_under_prob > 0 else float('inf')
        final_fair_over_odds  = 1 / final_over_prob  if final_over_prob  > 0 else float('inf')
        
        # --- 7) Display the results side by side for each outcome ---
        result_label["text"] = (
            f"Under 2.5 Goals: Fair {final_fair_under_odds:.2f} vs Live {live_under_odds:.2f}\n"
            f"Over 2.5 Goals:  Fair {final_fair_over_odds:.2f}  vs Live {live_over_odds:.2f}"
        )
        
    except ValueError:
        result_label["text"] = "Please enter valid numerical values."

def reset_fields():
    for entry in entries.values():
        entry.delete(0, tk.END)
    result_label["text"] = ""

# --- GUI Layout ---
root = tk.Tk()
root.title("Odds Apex Pre-Market")

# Define input fields
entries = {
    "entry_home_scored":      tk.Entry(root),
    "entry_away_conceded":    tk.Entry(root),
    "entry_away_scored":      tk.Entry(root),
    "entry_home_conceded":    tk.Entry(root),
    "entry_injuries_home":    tk.Entry(root),
    "entry_injuries_away":    tk.Entry(root),
    "entry_position_home":    tk.Entry(root),
    "entry_position_away":    tk.Entry(root),
    "entry_form_home":        tk.Entry(root),
    "entry_form_away":        tk.Entry(root),
    "entry_home_xg_scored":   tk.Entry(root),
    "entry_away_xg_scored":   tk.Entry(root),
    "entry_home_xg_conceded": tk.Entry(root),
    "entry_away_xg_conceded": tk.Entry(root),
    "entry_live_under_odds":  tk.Entry(root),
    "entry_live_over_odds":   tk.Entry(root),
}

labels_text = [
    "Avg Goals Home Scored", "Avg Goals Away Conceded", "Avg Goals Away Scored",
    "Avg Goals Home Conceded", "Injuries Home", "Injuries Away", "Position Home",
    "Position Away", "Form Home", "Form Away", "Home xG Scored", "Away xG Scored",
    "Home xG Conceded", "Away xG Conceded", "Live Under 2.5 Odds", "Live Over 2.5 Odds"
]

for i, (key, label_text) in enumerate(zip(entries.keys(), labels_text)):
    label = tk.Label(root, text=label_text)
    label.grid(row=i, column=0, padx=5, pady=5, sticky="e")
    entries[key].grid(row=i, column=1, padx=5, pady=5)

# Result label
result_label = tk.Label(root, text="", justify="left")
result_label.grid(row=len(entries), column=0, columnspan=2, padx=5, pady=5)

# Buttons
calculate_button = tk.Button(root, text="Calculate Over/Under Odds", command=calculate_probabilities)
calculate_button.grid(row=len(entries)+1, column=0, columnspan=2, padx=5, pady=10)

reset_button = tk.Button(root, text="Reset All Fields", command=reset_fields)
reset_button.grid(row=len(entries)+2, column=0, columnspan=2, padx=5, pady=10)

root.mainloop()
