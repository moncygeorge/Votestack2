from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necessary for flash messages to work

# Path to the file containing usernames
usernames_file = 'usernames.txt'
positions_file = 'positions.txt'
names_file = 'names.txt'
votes_file = 'votes.txt'


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


@app.route('/vote', methods=['GET'])
def vote():
    if 'username' not in session:
        return redirect(url_for('index'))  # Redirect to login if not logged in

    try:
        # Read the positions from 'positions.txt' file (assuming only one position is displayed at a time)
        with open(positions_file, 'r') as file:
            positions = file.read().splitlines()

        # Get the first position (you can modify this to cycle through positions if needed)
        position = positions[0] if positions else None

        # Read the names from 'names.txt'
        with open(names_file, 'r') as file:
            names = file.read().splitlines()

        return render_template('vote.html', position=position, names=names)  # Pass position and names to template

    except FileNotFoundError:
        flash("Positions or Names file not found.", "danger")
        return redirect(url_for('index'))  # Redirect to login if file is missing


@app.route('/submit_vote', methods=['POST'])
def submit_vote():
    if 'username' not in session:
        return redirect(url_for('index'))  # Redirect to login if not logged in

    name = request.form.get('name')  # Get the selected name from the form

    if not name:
        flash("Please select a name to vote for.", "danger")
        return redirect(url_for('vote'))  # Redirect back to the voting page if no name is selected

    try:
        # Save the vote (this is a simple tally stored in a file)
        with open(votes_file, 'a') as file:
            file.write(name + '\n')  # Append the voted name to 'votes.txt'

        flash(f"Your vote for {name} has been recorded!", "success")
        return redirect(url_for('vote'))  # Stay on the voting page after voting

    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for('vote'))  # Redirect back to voting page if any error occurs


@app.route('/admin_dashboard', methods=['GET'])
def admin_dashboard():
    if 'username' not in session or session['username'] != 'admin':
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('index'))  # Redirect if the user is not admin

    return render_template('admin_dashboard.html')  # Show the dashboard for admin with the Generate Tally button


@app.route('/generate_tally', methods=['POST'])
def generate_tally():
    if 'username' not in session or session['username'] != 'admin':
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('index'))  # Ensure only admin can access this route

    try:
        # Read the votes from 'votes.txt'
        with open(votes_file, 'r') as file:
            votes = file.read().splitlines()

        # Count the votes for each name
        vote_count = {}
        for vote in votes:
            if vote in vote_count:
                vote_count[vote] += 1
            else:
                vote_count[vote] = 1

        return render_template('tally.html', tally=vote_count)  # Pass the tally data to the template

    except FileNotFoundError:
        flash("Votes file not found.", "danger")
        return redirect(url_for('admin_dashboard'))  # Redirect to admin dashboard if votes file is missing


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
