import os
import json
import random

DATA_FOLDER = "data"
PLAYERS_FOLDER = "players"


def load_lootboxes():
    #tar data fra DATA_FOLDER
    lootboxes = {}
    if not os.path.isdir(DATA_FOLDER):
        return lootboxes

    for filename in os.listdir(DATA_FOLDER):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(DATA_FOLDER, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            print(f"Warning: failed to read {path}")
            continue

        name = data.get("name")
        if not name:
            continue

        # pass paa at det er int 
        cost = data.get("cost", 0)
        try:
            cost = int(cost)
        except Exception:
            try:
                cost = int(float(cost))
            except Exception:
                cost = 0

        items = data.get("items", [])
        lootboxes[name] = {"cost": cost, "items": items}

    return lootboxes


def ensure_players_folder():
    if not os.path.exists(PLAYERS_FOLDER):
        os.makedirs(PLAYERS_FOLDER)


def player_file_path(player_name):
    ensure_players_folder()
    safe_name = f"{player_name}.json"
    return os.path.join(PLAYERS_FOLDER, safe_name)


def create_player(player_name, starting_balance=1000):
    path = player_file_path(player_name)
    if os.path.exists(path):
        print(f"Player '{player_name}' already exists.")
        return False

    player_data = {"name": player_name, "balance": starting_balance,"SPENT": 0, "inventory": []}
    with open(path, "w", encoding="utf-8") as f:#"bruk utf-8" chatGPT 
        json.dump(player_data, f, indent=4)
    print(f"Created player '{player_name}' with balance {starting_balance}")
    return True


def load_player(player_name):
    path = player_file_path(player_name)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_player(player_name, player_data):
    path = player_file_path(player_name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(player_data, f, indent=4)


def list_players():

    ensure_players_folder()
    players = []

    for filename in os.listdir(PLAYERS_FOLDER):
        if not filename.endswith(".json"):
            continue
        file_path = os.path.join(PLAYERS_FOLDER, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError): 
            continue

        name = filename[:-5]
        spent = data.get("SPENT", 0)
        try:
            spent = float(spent)
        except Exception:
            spent = 0

        players.append({"name": name, "spent": spent})

    players.sort(key=lambda x: x["spent"], reverse=True)

    results = []
    for i, p in enumerate(players, start=1):
        results.append(f"{i}. {p['name']} - Total Spent: {int(p['spent'])} coins")

    return results


def open_lootbox_choice(box_def):
    """Given a box definition (dict with items key), return a picked item using chance weights."""
    items = box_def.get("items", [])
    r = random.random()
    cumulative = 0.0
    for it in items:
        try:
            chance = float(it.get("chance", 0))
        except Exception:
            chance = 0.0
        cumulative += chance
        if r <= cumulative:
            return it.get("item")
    # fallback
    if items:
        return items[-1].get("item")
    return None


def print_main_menu(current_player):
    print("\n=== CardSharP Lootboxes ===")
    if current_player:
        print(f"Current player: {current_player}")
    else:
        print("No player selected")
    print("Type 'w' for lootboxes")
    print("Type 'p' for player options")
    print("Type 'q' to quit")


def profile_menu(state):
    # state is a dict holding current_player and lootboxes
    while True:
        print("\n--- Player Menu ---")
        print("1. List players")
        print("2. Create player")
        print("3. Select player")
        print("4. Show current player")
        print("b. Back")
        choice = input("Choice: ")
        if choice == "1":
            players = list_players()
            if not players:
                print("No players found")
            else:
                for p in players:
                    print(f"- {p}")
        elif choice == "2":




            name = input("Enter new player name: ")
            if name:
                create_player(name)
        elif choice == "3":
            name = input("Enter player name to select: ")
            if load_player(name) is None:
                print("Player not found")
            else:
                state["current_player"] = name
                print(f"Selected player: {name}")
        elif choice == "4":
            cp = state.get("current_player")
            if not cp:
                print("No player selected")
            else:
                pdata = load_player(cp)
                print(json.dumps(pdata, indent=2))
        elif choice.lower() == "b":
            return
        else:
            print("Invalid choice")


def open_lootbox_menu(state):
    current = state.get("current_player")
    if not current:
        print("No player selected. Go to player menu to select or create one.")
        return

    pdata = load_player(current)
    if pdata is None:
        print("Failed to load player data")
        return

    print("\n=== LOOTBOX MENU ===")
    boxes = list(state.get("lootboxes", {}).items())
    if not boxes:
        print("No lootboxes available.")
        return

    for i, (name, box) in enumerate(boxes, start=1):
        print(f"{i}. {name} - Cost: {box.get('cost', 0)}")

    print(f"Balance: {pdata.get('balance', 0)} coins")
    choice = input("Enter number of lootbox to open (or 'b' to go back): ")
    if choice.lower() == 'b':
        return

    try:
        idx = int(choice) - 1
        selected_name, selected_box = boxes[idx]
    except Exception:
        print("Invalid choice.")
        return
    #broke boi
    cost = selected_box.get('cost', 0)
    if pdata.get('balance', 0) < cost:
        print("Not enough coins!")
        return

    # TAKE THEIR MONEY
    pdata['balance'] = pdata.get('balance', 0) - cost
    pdata['SPENT'] = pdata.get('SPENT', 0) + cost
    prize = open_lootbox_choice(selected_box)
    if prize:
        pdata.setdefault('inventory', []).append(prize)

    save_player(current, pdata)
    print(f"\n you opened a {selected_name} lootbox and won: {prize}")


def main():
    lootboxes = load_lootboxes()
    state = {"current_player": None, "lootboxes": lootboxes}

    while True:
        print_main_menu(state.get("current_player"))
        choice = input("enter your choice: ")
        if choice == "w":
            open_lootbox_menu(state)
        elif choice == "p":
            profile_menu(state)
        elif choice == "q":
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
