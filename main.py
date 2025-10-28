import random, os, json

DATA_FOLDER = "data"
PLAYERS_FOLDER = "players"


def load_lootboxes():#loade lootboxer som ligger i en annen fil
    lootboxes = {}
    for filename in os.listdir(DATA_FOLDER):
        if filename.endswith(".json"):
            with open(os.path.join(DATA_FOLDER, filename), "r") as f:
                data = json.load(f)
                lootboxes[data["name"]] = data["items"]
    return lootboxes
lootboxes = load_lootboxes()

def create_player(player_name, starting_balance=1000): #lage en player account og gir han en currency "auto magisk " sondre eller sindre idk
    # lage folder idk why. koffor ikke
    if not os.path.exists(PLAYERS_FOLDER):
        os.makedirs(PLAYERS_FOLDER)
        print(f"Created folder: {PLAYERS_FOLDER}")

    # path
    player_file = os.path.join(PLAYERS_FOLDER, f"{player_name}.json")

    # ingen frauds
    if os.path.exists(player_file):
        print(f"Player '{player_name}' already exists!")
        return

    player_data = {"balance": starting_balance}

    # jarvis"JSON" husk dette
    with open(player_file, "w") as f:
        json.dump(player_data, f, indent=4)

    print(f"Created new player '{player_name}' with balance {starting_balance}")

def open_lootbox(tier):
    if tier not in lootboxes:
        print("Invalid tier.")
        return

    items = lootboxes[tier]
    r = random.random()
    cumulative = 0
    for item in items:
        cumulative += item["chance"]
        if r<=cumulative:
            return item["item"]


def main():
    while True:
        print("\nWelcome to CardsharP")
        print("Type 'w' for lootboxes")
        print("Type 'p' for player options")
        print("Type 'q' to quit")

        choice = input("enter your choice: ")

        if choice == "w":
            open_lootbox_menu()
        elif choice == "p":
            profile_menu()
        elif choice == "q":
            break
        else:
            print("Invalid choice.")

        def open_lootbox_menu(current_player):
            # 1️⃣ Load player data
            player_data = load_player_data(current_player)  # your function to read JSON

            # 2️⃣ Display available lootboxes
            print("\n=== LOOTBOX MENU ===")
            for i, tier in enumerate(lootboxes.keys(), 1):
                print(f"{i}. {tier}")

            print(f"Balance: {player_data['balance']} coins")

            # 3️⃣ Ask the player to choose a lootbox
            choice = input("Enter number of lootbox to open (or 'b' to go back): ")
            if choice.lower() == 'b':
                return  # go back to main menu

            # 4️⃣ Convert choice to tier name safely
            try:
                selected_tier = list(lootboxes.keys())[int(choice) - 1]
            except (IndexError, ValueError):
                print("Invalid choice.")
                return

            # 5️⃣ Check if player has enough coins
            cost = get_lootbox_cost(selected_tier)  # define cost per tier
            if player_data['balance'] < cost:
                print("Not enough coins!")
                return

            # 6️⃣ Deduct cost and open lootbox
            player_data['balance'] -= cost
            prize = open_lootbox(selected_tier, lootboxes)  # your existing function

            # 7️⃣ Save updated balance
            save_player_data(current_player, player_data)  # your function to write JSON

            print(f"\n🎉 You opened a {selected_tier} lootbox and won: {prize}")


if __name__ == "__main__":
    main()

