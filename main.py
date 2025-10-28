import random


lootboxes = {
    "Common": [
        {"item": "Wooden Sword", "chance": 0.6},
        {"item": "Leather Armor", "chance": 0.3},
        {"item": "Small Potion", "chance": 0.1},
    ],
    "Rare": [
        {"item": "Iron Sword", "chance": 0.5},
        {"item": "Steel Shield", "chance": 0.3},
        {"item": "Large Potion", "chance": 0.2},
    ],
    "Epic": [
        {"item": "Flaming Axe", "chance": 0.4},
        {"item": "Magic Wand", "chance": 0.35},
        {"item": "Phoenix Feather", "chance": 0.25},
    ],
    "Legendary": [
        {"item": "Dragon Armor", "chance": 0.5},
        {"item": "Infinity Blade", "chance": 0.3},
        {"item": "Celestial Staff", "chance": 0.2},
    ],
}

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
    print("Welcome to the Lootbox!")
    print("choose what lootbox you want to buy")
    for i, tier in enumerate(lootboxes.keys(), 1):
        print(f"{i}. {tier}")

    choice = input("enter number: ")
    tiers = list(lootboxes.keys())

    try:
        selected_tier = tiers[int(choice)-1]
    except (IndexError, ValueError):
        print("Invalid tier.")
        return


    prize = open_lootbox(selected_tier)
    print(f"\n you opened a loot box {selected_tier} and won {prize}")


if __name__ == "__main__":
    main()

