#! /usr/bin/python3

# In the Monty Hall game, a contestant is shown 3 doors.
# Behind one door is a car and behind the other two are goats.
# The contestant first picks a door.
# The game host then reveals a goat behind one of the other two doors.
# The game host then asks the contestant if they want to their choice.
# Question: Should they?
# Answer: Statistically/probabilisticly - yes

# Let's prove this experimentally
# 1) Determine which door is a "win".
# 2) Random contestant selection.
# 3) Reveal non-selected, non-win door
# 4) If change_choice = true; update contestant selection; else don't
# 5) Determine if contestant won
# 6) Record result

import sys
import random

NUM_DOORS = 3
CHANGE = False

SEED = 42

MIN_DOORS = 3
MAX_DOORS = 5
NUM_ROUNDS = 100000
LOGGING = {
	"round": False,
	"run": False,
	"sweep": True
}

# initialize win door - randomly selected from door array
def determineWinDoor(doors):
	return random.choice(doors)

# contestant's choice - randomly selected from door array
def selectDoor(doors):
	return random.choice(doors)
	
# revealed door - MUST NOT be win_door or selected_door
# remove those from list then randomly select from remaining
def revealDoors(doors, win_door, selected_door, num_reveals):
	reveals = []
	doors.remove(selected_door)
	if win_door is not selected_door:
		doors.remove(win_door)
	for i in range(0, num_reveals):
		d = random.choice(doors)
		reveals.append(d)
		doors.remove(d)
	return reveals

# new selected door - MUST NOT be previous selected_door or revealed_door
# remove those from list then randomly select from remaining
def updateSelectedDoor(doors, selected_door, revealed_doors):
	doors.remove(selected_door)
	doors = [d for d in doors if d not in revealed_doors]
	return selectDoor(doors)

# A single iteration of the Monty Hall game simulation with logging so we can trace the steps.
def montyhall(doors, change, log=True, num_reveals=1):
	if(log): print(" ===== ===== ===== ===== ===== ")
		
	doors = [x for x in range(doors)] # Generate door range
	if(log): print(f"{doors} generated")
	
	win_door = determineWinDoor(doors) # Initialize win door
	selected_door = selectDoor(doors)  # Select contestant door
	if(log): print(f"Contestant selected door {selected_door}")
	
	revealed_doors = revealDoors(doors.copy(), win_door, selected_door, num_reveals) # Reveal a door
	if(log): 
		if(num_reveals == 1): print(f"Host revealed door {revealed_doors[0]}")
		else: print(f"Host revealed doors {revealed_doors}")
	
	# For the experiment, we must be able to check what happens when 
	#  contestants do not update their choice after the reveal
	if change:
		selected_door = updateSelectedDoor(doors.copy(), selected_door, revealed_doors)
		if(log): print(f"Contestant changed their selection to door {selected_door}")
	else:
		if(log): print(f"Contestant did not change their selected door")
		
	# Determine if the contestant won
	win = selected_door == win_door
	win_message = "wins!" if win else "looses..."
	if(log): print(f"Winning door was {win_door +1}: Contestant {win_message}")
	
	# Return results for further analysis
	return {
		"win": win,
		"selected_door": selected_door,
		"revealed_doors": revealed_doors,
		"win_door": win_door
	}

# Run multiple rounds of the Monty Hall game simulation and report the win rate
def run(doors=NUM_DOORS, change=CHANGE, num_rounds=1000, log={"round":False,"run":True}, num_reveals=1):
	change_state = "enabled" if change else "disabled"
	if(log["run"]): print(f"Simulating {num_rounds} of MontyHall games with {doors} doors and change {change_state}.")
	num_wins = 0
	for r in range(0, num_rounds):
		result = montyhall(doors, change, log["round"], num_reveals)
		if result["win"]:
			num_wins += 1
	win_rate = (num_wins/num_rounds) * 100
	if(log["run"]): print(f" - Contestant won {num_wins} rounds ({win_rate}%)")
	return num_wins
	
# Do a sweep of different door counts for the Monty Hall game simulation
#  and analyze the probabilistic behavior
def sweep(min_doors=3, max_doors=5, num_rounds=1000, log={"round":False,"run":False,"sweep":True}):
	if(log["sweep"]): 
		print(f"=== Running simulations for all Monty Hall-like cases with {min_doors}-{max_doors} doors ===")
		print("")
		print(" # Doors | Change? | # Wins | % Wins ")	
	metrics = []
	for num_doors in range(min_doors, max_doors+1):
		num_wins_with_change = run(num_doors, True, num_rounds, log)
		num_wins_without_change = run(num_doors, False, num_rounds, log)
		win_rate_with_change = round((num_wins_with_change/num_rounds) * 100, 2)
		win_rate_without_change = round((num_wins_without_change/num_rounds) * 100, 2)
		if(log["sweep"]):
			print(f" {num_doors: <7} |   False | {num_wins_without_change: <6} | {win_rate_without_change: <5}% ")
			print(f" {num_doors: <7} |    True | {num_wins_with_change: <6} | {win_rate_with_change: <5}% ")
		metrics.append({
		  "num_doors": num_doors,
		  "num_wins_with_change": num_wins_with_change,
		  "win_rate_with_change": win_rate_with_change,
		  "num_wins_without_change": num_wins_without_change,
		  "win_rate_without_change": win_rate_without_change
		})
	for metric in metrics:
		num_doors = metric["num_doors"]
		rate_difference = metric["win_rate_with_change"] - metric["win_rate_without_change"]
		percentage_redistributed = rate_difference * (num_doors -2)
		percentage_redistributed_confirmation = percentage_redistributed * num_doors
		print(f"For {num_doors}, a win probability of {percentage_redistributed}% is redistributed.")
	print("*The doors affected by the redistribution are those that are neither chosen nor revealed at the time of the reveal")
	
# Now for another question: How are the probabilities affected if the 
#  number of doors that are revealed is changed?
def advSweep(min_doors, max_doors, num_rounds=1000, log={"round":False,"run":False,"sweep":True}):
	if(log["sweep"]): 
		print(f"=== Running advanced simulations for all Monty Hall-like cases with {min_doors}-{max_doors} doors ===")
		print("")
		print(" # Doors | # Revealed | Change? | # Wins | % Wins ")	
	metrics = []
	for num_doors in range(min_doors, max_doors+1):
		for num_reveals in range(1, num_doors-1):
			num_wins_with_change = run(num_doors, True, num_rounds, log, num_reveals)
			num_wins_without_change = run(num_doors, False, num_rounds, log, num_reveals)
			win_rate_with_change = round((num_wins_with_change/num_rounds) * 100, 2)
			win_rate_without_change = round((num_wins_without_change/num_rounds) * 100, 2)
			if(log["sweep"]):
				print(f" {num_doors: <7} | {num_reveals: <10} |  False  | {num_wins_without_change: <6} | {win_rate_without_change: <5}% ")
				print(f" {num_doors: <7} | {num_reveals: <10} |  True   | {num_wins_with_change: <6} | {win_rate_with_change: <5}% ")
			metrics.append({
			  "num_doors": num_doors,
			  "num_reveals": num_reveals,
			  "num_wins_with_change": num_wins_with_change,
			  "win_rate_with_change": win_rate_with_change,
			  "num_wins_without_change": num_wins_without_change,
			  "win_rate_without_change": win_rate_without_change
			})
	for metric in metrics:
		num_doors = metric["num_doors"]
		num_reveals = metric["num_reveals"]
		available_doors = (num_doors -1 - num_reveals)
		rate_difference = metric["win_rate_with_change"] - metric["win_rate_without_change"]
		
		total_percentage_redistributed = rate_difference * available_doors
		per_reveal_percentage_redistributed = total_percentage_redistributed / num_reveals
		percentage_redistributed_confirmation = per_reveal_percentage_redistributed * num_doors # Should be close to 100
				
		original_per_door_percentage = 100.0 / num_doors
		post_reveal_per_door_percentage = (100.0 - original_per_door_percentage) / available_doors # Technically, this is only valid for the doors that have not been revealed or chosen
		theoretical_rate_difference = post_reveal_per_door_percentage - original_per_door_percentage
		theory_vs_experiment_difference = theoretical_rate_difference - rate_difference # Should be close to 0
		
		print(f"For {num_doors} with {num_reveals} revealed, a win probability of {total_percentage_redistributed}% is redistributed to {available_doors} door(s), increasing win chance by {rate_difference}%.")
		print(f"  (redistribution confirmation = {percentage_redistributed_confirmation}%; should be close to 100%)")
		print(f"  (diff btw theory & experiment = {theory_vs_experiment_difference}%; should be close to 0%)")
	print(" * The doors affected by the redistribution are those that are neither chosen nor revealed at the time of the reveal")

	
if __name__ == "__main__":
	
	if len(sys.argv) == 1:
		print("Usage: python3 main.py [round|run|sweep|adv]")
		sys.exit(0)
	
	# Basic Monty Hall run
	if sys.argv[1] == 'round':
		montyhall(NUM_DOORS, CHANGE, True)
	
	# Simulate many runs and calculate statistics
	if sys.argv[1] == 'run':
		run(NUM_DOORS, CHANGE, NUM_ROUNDS, { "round": False, "run": True })
	
	# Run a full sweep of multiple door sizes, changing or not changing choice, and print results as a table
	if sys.argv[1] == 'sweep':
		sweep(MIN_DOORS, MAX_DOORS, NUM_ROUNDS, LOGGING)
		
	# Run the advanced sweep that includes the host revealing more than one door
	if sys.argv[1] == 'adv':
		advSweep(MIN_DOORS, MAX_DOORS, NUM_ROUNDS, LOGGING)
	
# The fascinating - perhaps paradoxical part - is that the probability 
#  redistribution does not include the door chosen by the contestant.
	
# Very interesting results from the advanced sweep.  
#  The redistribution logic holds even in the case of 5 doors with 3 revealed!
#  Post reveal, the contestant's choice is not a 50/50 but an imbalanced 20/80!
