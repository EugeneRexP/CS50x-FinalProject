
from cs50 import SQL
from datetime import datetime
from flask import Flask, redirect, render_template, session, request, flash
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import oex, money, login_required, line, pie, bar

app = Flask(__name__)

# Filter
app.jinja_env.filters["money"] = money

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL('sqlite:///database.db')
# CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, hash TEXT NOT NULL, currency TEXT NOT NULL, budget FLOAT NOT NULL)
# CREATE TABLE expenses (refid INTEGER PRIMARY KEY AUTOINCREMENT, userid INTEGER NOT NULL, day INTEGER NOT NULL, month INTEGER NOT NULL, year INTEGER NOT NULL, cost REAL NOT NULL, tag TEXT NOT NULL, remark TEXT, FOREIGN KEY(userid) REFERENCES users(id))

tags = ["Charity",
        "Clothing",
        "Education",
        "Food", 
        "Investment",
        "Leisure", 
        "Medical",
        "Miscellaneous",
        "Subscription", 
        "Transport", 
        "Utilities", 
        "CASH IN"]

months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

@app.route("/",  methods=["GET", "POST"])
@login_required
def index(): 
    # Get session ID & pref
    userid = session.get("user_id")
    if not isinstance(userid, int):
        userid = userid[0]["id"]
    currencypref = db.execute("SELECT currency FROM users WHERE id = ?", userid)[0]["currency"]
    year = 2023
    
    # Set year
    if request.method == "POST":
        year = request.form.get("year")
    if not year:
        year = 2023
    
    # Query expenses table
    expenses = db.execute("SELECT * FROM expenses WHERE userid = ? AND year = ? ORDER BY month, day", 
                          userid, year)
    
    # Compute budget left
    currentmonth = datetime.now().month
    monthexpense = db.execute("SELECT SUM(cost) FROM expenses WHERE userid = ? AND year = ? AND month = ? GROUP BY month", 
                              userid, 2023, currentmonth)
    budget = float(db.execute("SELECT budget FROM users WHERE id = ?", userid)[0]['budget'])
    # Calculate budget left
    if monthexpense:    
        monthexpense = float(monthexpense[0]['SUM(cost)'])
        budget = budget - monthexpense
    
    # Prepare data for graph
    graphdata = db.execute("SELECT month, SUM(cost) FROM expenses WHERE userid = ? AND year = ? AND tag != 'CASH IN' GROUP BY month", 
                           userid, year)
    x = [] 
    y = []
    for graph in graphdata:
        x.append(graph['month'])
        y.append(graph['SUM(cost)'])
    
    script, div = line(x, y)

    # Render template:
        # year: Year to list. Defaults to 2023
        # expenses: List of expenses given the year
        # script & div: Graph components
        # budget: Remaining budget for the current month
        # currencypref: Preferred currency of user
    return render_template("index.html", 
                           year=year, expenses=expenses, script=script, div=div, budget=budget, currencypref=currencypref)


@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()

    # Request via POST
    if request.method == "POST":
        # Ensure username and password was submitted
        if not request.form.get("username") or not request.form.get("password"):
            flash("Please provide username and password", "error")
            return render_template("login.html")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", 
                          request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("Invalid username and/or password", "error")
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        oex()

        # Redirect to input
        return redirect("/")

    # Request via GET
    else:
        return render_template("login.html")
    

@app.route("/logout")
def logout():
    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():
    """ Register users """
    currencies = session.get('currencies')
    
    # Request via POST
    if request.method == "POST":
        # Query inputs
        username = request.form.get('username')
        password = request.form.get('password')
        confirmation = request.form.get('confirmation')
        
        # Validate inputs
        if not username or not password or not confirmation:
            flash("Missing input", "error")
            return redirect("/register")

        users = db.execute('SELECT username FROM users')
        for user in users:
            if username in user.values():
                flash("Username already exists", "error")
                return redirect("/register")

        if password != confirmation:
            flash("Passwords do not match", "error")
            return redirect("/register")

        # Register the user
        db.execute(
            "INSERT INTO users (username, hash, currency, budget) VALUES (?, ?, 'USD', 0)",
            username,
            generate_password_hash(password),
        )
        flash("Registration successful")

        # Login the user
        id = db.execute("SELECT id FROM users WHERE username = ?", username)
        session["user_id"] = id
        oex()
        return redirect("/pref")

    # Request via GET
    return render_template("register.html", currencies=currencies)


@app.route("/input", methods=["GET", "POST"])
@login_required
def input():
    # Query userid & pref
    userid = session.get("user_id")
    if not isinstance(userid, int):
        userid = userid[0]["id"]
    currencypref = db.execute("SELECT currency FROM users WHERE id = ?", userid)[0]["currency"]
    
    # Request via POST
    if request.method == "POST":
        # Query inputs    
        day = request.form.get('day')
        month = request.form.get('month')
        year = request.form.get('year')
        cost = request.form.get('cost')
        currency = request.form.get('currency')
        tag = request.form.get('tag')
        remark = request.form.get('remark')
        
        # Check inputs
        if tag == "CASH IN":
            cost = -float(cost)
        if not remark:
            remark = "-"
        
        """Check for none"""
        if not day or not month or not tag or not cost:
            flash("Missing input fields", "error")
            return redirect("/input")
        
        # Default values
        if not year:
            year = 2023 
        if not currency:
            currency = currencypref
        
        # Convert
        if currencypref != currency:
            rates = session.get('rates')           
            cost = round(float(cost) / float(rates[currency]) * float(rates[currencypref]), 2)
        
        # Add to table
        db.execute("INSERT INTO expenses (userid, day, month, year, cost, tag, remark) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                   userid, day, month, year, cost, tag, remark)

        # Return to input
        flash("Entry added")
        return redirect("/input")
        
    # Request via GET
    currencies = session.get('currencies')
    return render_template("input.html", currencypref=currencypref, currencies=currencies, tags=tags)


@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    refid = request.form.get('delete')
    db.execute('DELETE FROM expenses WHERE refid = ?', refid)
    return redirect('/')
    

@app.route("/graphs", methods=["GET", "POST"])
@login_required
def graphs():
    # Query userid
    userid = session.get("user_id")
    if not isinstance(userid, int):
        userid = userid[0]["id"]
        
    # Tags
    taglist = db.execute("SELECT tag FROM expenses WHERE userid = ? GROUP BY tag", userid)
    tags = [ sub['tag'] for sub in taglist ]
    if 'CASH IN' in tags:
        tags.remove('CASH IN')
    
    # Ensure enough data to plot
    if len(tags) < 3:
        flash('Not enough data', 'error')
        return redirect('/input')
    
    # Prepare data for Pie
    vars = db.execute('SELECT tag, SUM(cost) FROM expenses WHERE userid = ? AND tag != "CASH IN" GROUP BY tag', userid)
    x = {}
    for var in vars:
        x[var['tag']] = var['SUM(cost)']
    
    # Request via POST
    if request.method == "POST":
        # Remove axes
        x = {}
        for var in vars:
            if request.form.get(var['tag']):
                x[var['tag']] = var['SUM(cost)']
    
        # Validate inputs
        if len(x) < 3:
            flash("Tick at least three", "error")
            return redirect("/graphs")
      
    # Generate pie elements
    script_pie, div_pie = pie(x)
    
    """ Prepare data for Bar """    
    data = {'month' : months}
    for tag in tags:
        var = []
        for month in range(1,13):
            temp = db.execute("SELECT SUM(cost) FROM expenses WHERE userid = ? AND tag = ? AND month = ? GROUP BY tag", userid, tag, month)
            if temp:
                temp = float(temp[0]['SUM(cost)'])
            else:
                temp = 0
            var.append(temp)
        data.update({tag : var})  
    data_in = []
    for month in range(1,13):
        temp = db.execute("SELECT SUM(cost) FROM expenses WHERE userid = ? AND tag = 'CASH IN' AND month = ? GROUP BY tag", userid, month)
        if temp:
            temp = float(temp[0]['SUM(cost)'])
        else:
            temp = 0
        data_in.append(temp)
    
    # Generate bar elements
    script_bar, div_bar = bar(data, data_in, tags, months)
    
    script = script_pie + script_bar

    return render_template("graphs.html", script=script, div_pie=div_pie, div_bar=div_bar, tags=tags)


@app.route("/pref", methods=["GET", "POST"])
@login_required
def pref():
    """ Set defaults for user """
    # Query userid
    userid = session.get("user_id")
    if not isinstance(userid, int):
        userid = userid[0]["id"]
    # Query default currency
    currencypref = db.execute("SELECT currency FROM users WHERE id = ?", userid)[0]["currency"]
    
    # Prepare list of currencies    
    currencies = session.get('currencies')
    rates = session.get('rates')
    
    # Request via POST
    if request.method == 'POST':
        currency = request.form.get('currency')
        budget = request.form.get('budget')

        # Convert table
        if currency != currencypref:
            conversion = float(rates[currency]) / rates[currencypref]
            expenses = db.execute("SELECT refid, cost FROM expenses WHERE userid = ?", userid)
            try:
                for expense in expenses:
                    converted = expense['cost'] * conversion
                    db.execute("UPDATE expenses SET cost = ? WHERE refid = ?", converted, expense['refid'])
            except:
                print('error')
                
        # Insert into db
        flash("Preferences updated")
        db.execute("UPDATE users SET currency = ?, budget = ? WHERE id = ?", currency, budget, userid)
        
        # TODO: Convert expenses table 
        return redirect("/input")
    
    # Request via GET    
    return render_template("pref.html", currencies=currencies, currencypref=currencypref)


if __name__ == "__main__":
    app.run(debug=True)