import random
from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necessary for flash messages to work

# Path to the file containing usernames
usernames_file = 'usernames.txt'
names_file = 'choices.txt'
votes_file = 'votes.txt'

# Store topics in memory (instead of positions.txt)
topics = []  # Will store the topics that admin can modify

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('login.html')  # Show the login form

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')  # Get the username from the form

    if not username:
        flash("Please enter a username.", "danger")
        return redirect(url_for('index'))  # If no username is provided, stay on login page

    try:
        # Check if username exists in 'usernames.txt'
        with open(usernames_file, 'r') as file:
            usernames = file.read().splitlines()  # Read all usernames into a list

        if username in usernames:
            session['username'] = username  # Store username in session
            flash(f"Welcome, {username}!", "success")
            if username == 'admin':
                return redirect(url_for('admin_dashboard'))  # Redirect to admin dashboard if username is admin
            else:
                return redirect(url_for('vote'))  # Redirect to the voting page for regular users
        else:
            flash("Invalid username. Please try again.", "danger")
            return redirect(url_for('index'))  # Redirect back to login page if username is invalid

    except FileNotFoundError:
        flash("Usernames file not found.", "danger")
        return redirect(url_for('index'))  # Redirect back to login page if file is missing

@app.route('/admin_dashboard', methods=['GET'])
def admin_dashboard():
    if 'username' not in session or session['username'] != 'admin':
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('index'))  # Redirect if the user is not admin

    return render_template('admin_dashboard.html')  # Show the dashboard for admin with the Generate Tally button

@app.route('/enter_voters', methods=['POST'])
def enter_voters():
    if 'username' not in session or session['username'] != 'admin':
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('index'))  # Ensure only admin can access this route

    try:
        # Get the number of voters from the form
        num_voters = int(request.form.get('num_voters'))

        if num_voters <= 0:
            flash("Please enter a valid number of voters.", "danger")
            return redirect(url_for('admin_dashboard'))  # Redirect back to admin dashboard if invalid number

        # Generate the random 4-digit numbers for voters
        voter_numbers = [str(random.randint(1000, 9999)) for _ in range(num_voters)]

        # Open the usernames file and append the new voters
        with open(usernames_file, 'a') as file:
            for voter in voter_numbers:
                file.write(f"{voter}\n")  # Write each voter number to the file

        flash(f"{num_voters} voter numbers have been generated and added to the usernames file.", "success")
        return redirect(url_for('admin_dashboard'))  # Redirect back to the admin dashboard

    except ValueError:
        flash("Please enter a valid number.", "danger")
        return redirect(url_for('admin_dashboard'))  # Redirect back to admin dashboard if invalid input

    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for('admin_dashboard'))  # Handle any other unexpected errors

# Your existing routes go here...

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
