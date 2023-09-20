# Expense Tracker
### Video Demo:  <URL HERE>
### Description:
This is a web-based application that uses Python, JavaScript, SQL with Flask and Jinja templating.

It is a basic expense tracker that asks the user to manually input expenses and/or incomes then the application presents graphical representations of the data provided.
### HTML Templates:
#### Layout:
Contained here is the layout to be used as the base of all pages used by the app utlizing Jinja blocks.
This includes the scripts and links for relevant resources including Bootstrap, Bokeh and the CSS stylesheet.

The navigation bar is also rendered here. This includes links for the "Index", "Input", "Graphs", and "Preferences" pages. 
Depending on the state of the session, a link for either "Log Out" or "Log In" and "Register" is created.

An alert functionality has been implemented using message flashing by Flask.

#### Register:
To start using the application, a user is required to register for an account to access the features. 

To do so, the register page creates three input fields:
- Username: The user needs to supply a unique username that has not yet been registered to the database.
- Password: The user then needs to provide a password.
- Confirmation: Then input the password again as confirmation.
The input fields are checked if they contain the needed data, the username is checked against the database for uniqueness and the confirmation is compared to the password provided. Once complete, the password is hashed using the Werkzeug library and inserted into the [database](#database) along with the username. Errors re-renders the register page.

Once registration is successful, the user is automatically logged in and redirected to the preferences page.

#### Login:
A login page. Checks the username and the hashed password, using Werkzeug, with the database. If a valid combination is submitted as input, the user is logged in and redirected to the input page. Failed attempts re-renders the login page.

#### Preferences:
Additional inputs needed from the user:
- Currency: The currency in which expenses will be recorded as. If not previously set, defaults to USD, otherwise defaults to set currency.
- Budget: The budget to compare the expenses against. Budget left is calculated only for the current month.
Setting a different currency updates the user's expense table by converting to the new value using rates from the [session](#session).
Once the inputs are accepted, the users database is updated with the new values.

#### Input:
This is where entries for the expenses are placed as input with the following details:
- Day: The date of the month. Accepts integers 1 - 31 regardless of month.
- Month: A select menu for the month. Defaults to January.
- Year: A select menu for the year. Defaults to 2023 and given only options [2023, 2024, 2025].
- Value: The cash amount incurred. Takes a positive number with up to 2 decimal places. If the user would like to input positive cash flow (or negative expense), they may instead change the tag to "CASH IN".
- Currency: The currency of the value given. Defaults to preference settings. Setting it to any other currency will automatically convert the value before inserting into the database.
- Tag: Category or nature of expense. Relevant information in the graphs to be created. A special tag called "CASH IN" is also included which denotes money coming in or a negative expense.
- Remark: Free space for the user for any info they wish to insert.
  
Note: I did not think it necessary to allow the input of other years and decided to just limit the choices here.
I also pondered on using a date selector instead of 3 different input fields but decided this was the better way for ease of input.

If all inputs are accepted, the entry is inserted into the database and the page is re-rendered.

#### Index:
This is where all the entries from the input page are displayed. The entries are first categorized by year and by default, displays the entries for 2023. 
These entries are then separated by month into individual accordions which can be opened by simply clicking. With each entry, a delete button is also created in the same row. Pressing the button permanently removes the entry from the database.

Incorporating Bokeh, a simple line graph is also displayed here. This takes the total amount of expenses incurred per month and plots that agains the months, basically creating a comparison of how much has been spent for each month. Note that this graph does not account for incoming cash.

#### Graphs:
The more complicated and informative graphs are created here. It is important to note that the page cannot be accessed when there is not enough entries from the input page. Specifically, there needs to be, at minimum, entries with three different tags, excluding "CASH IN".

Once successful, a pie chart and a bar chart is created and displayed using Bokeh.
- Pie: The pie chart plots the total amounts for the whole year, grouping and comparing them by tag. To the left is a list of the tags plotted in the chart. You may untick the boxes and press the "Generate" button to create a new pie chart with only the ticked tags.
- Bar: The bar chart stacks all the expenses per tag then plots them for each month.

### Scripts:
#### App.py:
Main python file for various application functions:
- index(): Provides functionality of the homepage (/index).
- login(): Provides functionality of the login page (/login).
- logout(): Clears userid from the session to "log out" the user.
- register(): Provides functionality of the register page (/register).
- input(): Provides functionality of the input page (/input).
- delete(): Removes an entry from the expenses table using the delete button in the homepage.
- graphs(): Provides functionality of the graphs page (/graphs).
- pref(): Provides functionality of the preferences page (/pref).

#### Helpers.py:
Other useful functions are created here for readability of the main python file:
- login_required(): Decorator function that redirects user to login if no user is logged in the session.
- oex(): accesses an external API to save list of currencies and rates in  the session.
- money(): simple filter for float with two decimal points.
These three uses [Bokeh](https://docs.bokeh.org/en/latest/) to create graphs.
- line(): accepts two lists to create a line graph. Returns a script and a div element.
- pie(): accepts a dict of {name: value} pairs to create a pie chart. Returns a script and a div element.
- bar(): accepts a separate dict of lists for the positive and negative values, as well as names for the stacks and axes to create a bar chart.

#### Pyoxyr.py:
This was directly lifted from a user-created script from Open Exchange Rates by [Github user massakai](https://github.com/massakai/pyoxr).
Slight changes have been made by removing irrelevant parts.

### Database:
Two tables are created and used inside the db file using SQL.

#### Users table:
This table lists all the registered users and contains the following columns:
- id: Auto-incremented primary key for easier identification of user.
- username: User provided indentifier
- hash: Hashed password (see: [login](#login))
- currency: Preferred currency (see: [preferences](#preferences))
- budget: Preferred budget (see: [preferences](#preferences))

#### Expenses table: 
This table is generally updated from the [input](#input) page and contains the following columns:
- refid: A unique identifier for each entry in the table.
- userid: A foreign key from the users table to connect the entry to a user.
And the following columns directly from the [input](#input) page:
- day
- month
- year
- cost
- tag
- remark

### Session:
The application uses Flask to handle its sessions, configured to use the filesystem instead of signed cookies.

The session stores the user logged in, as well as relevant data from OpenExchange obtained upon login.

### OpenExchange:
The API used to obtain the exchange rates and currencies is [Open Exchange Rates](https://openexchangerates.org/).

This is accessed using a free account, and is saved per session.

Note: Originally this was supposed to be accessed for every input, however, this signficantly slowed down the loading of pages. 
