from flask import Flask, render_template, request, redirect, url_for, session, flash
import main as core

app = Flask(__name__)
app.secret_key = "dev-secret-key-please-change"


@app.route("/")
def index():
    lootboxes = core.load_lootboxes()
    player = session.get("player")
    balance = None
    if player:
        pdata = core.load_player(player)
        if pdata:
            balance = pdata.get("balance", 0)
    return render_template("index.html", player=player, balance=balance, lootboxes=lootboxes)


@app.route("/players")
def players():
    scoreboard = core.list_players()
    return render_template("players.html", scoreboard=scoreboard)


@app.route("/players/create", methods=("GET", "POST"))
def create_player():
    if request.method == "POST":
        name = request.form.get("name")
        if not name:
            flash("Please provide a name")
            return redirect(url_for("create_player"))
        ok = core.create_player(name)
        if ok:
            flash(f"Created player {name}")
            session["player"] = name
            return redirect(url_for("index"))
        else:
            flash("Player already exists")
            return redirect(url_for("create_player"))
    return render_template("create_player.html")


@app.route("/players/select", methods=("POST",))
def select_player():
    name = request.form.get("name")
    if core.load_player(name) is None:
        flash("Player not found")
    else:
        session["player"] = name
        flash(f"Selected player {name}")
    return redirect(url_for("players"))


@app.route("/players/logout", methods=("POST",))
def logout():
    session.pop("player", None)
    flash("Logged out")
    return redirect(url_for("index"))


@app.route("/lootboxes")
def lootboxes():
    boxes = core.load_lootboxes()
    return render_template("lootboxes.html", boxes=boxes)


@app.route("/lootboxes/open/<box_name>", methods=("GET", "POST"))
def open_box(box_name):
    boxes = core.load_lootboxes()
    box = boxes.get(box_name)
    if box is None:
        flash("Lootbox not found")
        return redirect(url_for("lootboxes"))

    player = session.get("player")
    if not player:
        flash("Select or create a player first")
        return redirect(url_for("players"))

    pdata = core.load_player(player)
    if pdata is None:
        flash("Failed to load player data")
        return redirect(url_for("players"))

    if request.method == "POST":
        cost = box.get("cost", 0)
        if pdata.get("balance", 0) < cost:
            flash("Not enough coins")
            return redirect(url_for("open_box", box_name=box_name))

        pdata["balance"] = pdata.get("balance", 0) - cost
        pdata["SPENT"] = pdata.get("SPENT", 0) + cost
        prize = core.open_lootbox_choice(box)
        if prize:
            pdata.setdefault("inventory", []).append(prize)

        core.save_player(player, pdata)
        return render_template("open_result.html", prize=prize, player=player, balance=pdata.get("balance", 0))

    # GET: show confirmation
    return render_template("open_confirm.html", box_name=box_name, cost=box.get("cost", 0))


if __name__ == "__main__":
    app.run(debug=True)
