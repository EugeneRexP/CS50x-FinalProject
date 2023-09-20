# Expense Tracker
### Video Demo:  <URL HERE>
### Description:
This is a web-based application that uses Python, JavaScript, SQL with Flask and Jinja templating.

It is a basic expense tracker that asks the user to manually input expenses and/or incomes then the application presents graphical representations of the data provided.
### HTML Templates:
#### Layout:
Contained here is the layout to be used as the base of all pages used by the app utlizing Jinja templating. 
This includes the scripts and links for relevant resources including Bootstrap, Bokeh and the CSS stylesheet.

The navigation bar is also rendered here. This includes links for the "Index", "Input", "Graphs", and "Preferences" pages. Also, depending on the state of the session, a link for either "Log Out" or "Log In" and "Register".

#### Register:
To start using the application, a user is required to register for an account to access the features. 

To do so, access the register page from the navigation bar at the top or by going to "/register".
There are three input fields:
- Username: The user needs to supply a unique username that has not yet been registered to the database.
- Password: The user then needs to provide a password.
- Confirmation: Then input the password again as confirmation.
The input fields are checked if they contain the needed data, the username is checked against the database for uniqueness and the confirmation is compared to the password provided. Once complete, the password is hashed using the Werkzeug library and inserted into the database along with the username. 
