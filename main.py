import random, os, json
DATA_FOLDER = "data"


def load_lootboxes():
    lootboxes = {}
    for filename in os.listdir(DATA_FOLDER):
        if filename.endswith(".json"):
            with open(os.path.join(DATA_FOLDER, filename), "r") as f:
                data = json.load(f)
                lootboxes[data["name"]] = data["items"]
    return lootboxes
lootboxes = load_lootboxes()



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

