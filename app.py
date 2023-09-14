from bokeh.palettes import Category20c
from bokeh.plotting import figure
from bokeh.transform import cumsum
from bokeh.embed import components
from cs50 import SQL
from flask import Flask, redirect, render_template, session, request, flash
from flask_session import Session
from functools import wraps
from math import pi
from pyoxr import OXRClient
from werkzeug.security import check_password_hash, generate_password_hash

import pandas as pd

app = Flask(__name__)
# OXRClient(app_id="281e3d3bb93840828f7da169c7279b65")

# Filters
def money(value):
    """Format value."""
    return f"{value:,.2f}"

app.jinja_env.filters["money"] = money

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL('sqlite:///database.db')
# CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL UNIQUE, hash TEXT NOT NULL)

def login_required(f):
    # login_required from finance
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
@login_required
def index():
    userid = session.get("user_id")
    if not isinstance(userid, int):
        userid = userid[0]["id"]
    
    expenses = db.execute("SELECT * FROM expenses WHERE userid = ? AND year = 2023 ORDER BY month, day", userid)
    graphdata = db.execute("SELECT month, SUM(cost) FROM expenses WHERE userid = ? AND year = 2023 GROUP BY month", userid)
    # prepare some data
    x = []
    y = []
    for graph in graphdata:
        x.append(graph['month'])
        y.append(graph['SUM(cost)'])
    
    # create a new plot with a title and axis labels
    p = figure(title="Expenses per Month", x_axis_label='month', y_axis_label='expense')
    
    # add a line renderer with legend and line thickness to the plot
    p.line(x, y, line_width=2)
    
    # show the results
    script, div = components(p)

    return render_template("index.html", expenses=expenses, script=script, div=div)


@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
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
    # Request via POST
    if request.method == "POST":
        # 
        username = request.form.get('username')
        password = request.form.get('password')
        confirmation = request.form.get('confirmation')
        defaultcurrency = request.form.get('currency')
        
        # Validate inputs
        if not username:
            return apology("must provide username", 400)

        users = db.execute('SELECT username FROM users')
        for user in users:
            if username in user.values():
                return apology("username already taken", 400)

        if not password or not confirmation:
            return apology("must provide password and confirmation", 400)

        if password != confirmation:
            return apology("passwords do not match", 400)
        
        # Check if currency exists

        # Register
        db.execute(
            "INSERT INTO users (username, hash, currency) VALUES (?, ?, ?)",
            username,
            generate_password_hash(password),
            defaultcurrency,
        )
        flash("Registration successful")

        # Login
        id = db.execute("SELECT id FROM users WHERE username = ?", username)
        session["user_id"] = id
        return redirect("/")

    # Request via GET
    oxr_cli = OXRClient(app_id="281e3d3bb93840828f7da169c7279b65")
    currencies = oxr_cli.get_currencies()
    
    return render_template("register.html", currencies=currencies)


@app.route("/input", methods=["GET", "POST"])
@login_required
def input():
    userid = session.get("user_id")
    if not isinstance(userid, int):
        userid = userid[0]["id"]
        
    oxr_cli = OXRClient(app_id="281e3d3bb93840828f7da169c7279b65")
    
    dc = db.execute("SELECT currency FROM users WHERE id = ?", userid)[0]["currency"]
    currencies = oxr_cli.get_currencies()
    
    # Request via POST
    if request.method == "POST":
        #         
        day = request.form.get('day')
        month = request.form.get('month')
        year = request.form.get('year')
        cost = request.form.get('cost')
        currency = request.form.get('currency')
        tag = request.form.get('tag')
        
        """Check for none"""
        
        # Default values
        if not year:
            year = 2023
            
        if not currency:
            currency = dc
        
        # Convert to appropriate currency
        if dc != currency:           
            rates = oxr_cli.get_latest()['rates']
            cost = round(float(cost) / float(rates[currency]) * float(rates[dc]), 2)
        
        # CREATE TABLE expenses (userid INTEGER NOT NULL, day INTEGER, month INTEGER, year INTEGER, cost REAL, tag TEXT, FOREIGN KEY(userid) REFERENCES users(id));
        db.execute("INSERT INTO expenses (userid, day, month, year, cost, tag) VALUES (?, ?, ?, ?, ?, ?)", 
                   userid, day, month, year, cost, tag)
        
        # Add to table
        flash("Entry added")
        return render_template("input.html", defaultcurrency=dc, currencies=currencies)
        
    # Request via GET   
    return render_template("input.html", defaultcurrency=dc, currencies=currencies)


@app.route("/graphs", methods=["GET", "POST"])
@login_required
def graphs():
    userid = session.get("user_id")
    if not isinstance(userid, int):
        userid = userid[0]["id"]

    taglist = db.execute('SELECT tag FROM expenses WHERE userid = ? GROUP BY tag', userid)
    tags = [ sub['tag'] for sub in taglist ]
    # Request via POST
    if request.method == "POST":
        # Export data
        # Create dict file for graph
        x = {}
        vars = db.execute('SELECT tag, SUM(cost) FROM expenses WHERE userid = ? GROUP BY tag', userid)
        for var in vars:
            if request.form.get(var['tag']):
                x[var['tag']] = var['SUM(cost)']

        if len(x) < 3:
            return apology("Please tick at least 3 tags", 400)
        
        # Create pie graph
        data = pd.Series(x).reset_index(name='value').rename(columns={'index': 'tag'})
        data['angle'] = data['value']/data['value'].sum() * 2*pi
        data['color'] = Category20c[len(x)]

        p = figure(height=350, title="Expense Distribution", toolbar_location=None,
                tools="hover", tooltips="@tag: @value", x_range=(-0.5, 1.0))

        p.wedge(x=0, y=1, radius=0.4,
                start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
                line_color="white", fill_color='color', legend_field='tag', source=data)

        p.axis.axis_label = None
        p.axis.visible = False
        p.grid.grid_line_color = None
        
        # show the results
        script, div = components(p)
        
        return render_template("graphs.html", script=script, div=div, tags=tags)
        
    # Request via GET
    script = ''
    div = ''
    return render_template("graphs.html", script=script, div=div, tags=tags)


@app.route("/split", methods=["GET", "POST"])
@login_required
def split():
    if request.method == 'POST':
        skills = request.form.getlist('field[]')
        print(skills)
        
        
    return render_template("split.html")

def apology(message, code=400):
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


if __name__ == "__main__":
    app.run(debug=True)