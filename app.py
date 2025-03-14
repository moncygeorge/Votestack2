from flask import Flask, render_template, request, redirect, url_for, flash, session
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necessary for flash messages to work

# Path to the file containing usernames
usernames_file = 'usernames.txt'
names_file = 'choices.txt'
votes_file = 'votes.txt'
# Store topics in memory (or it could be a file if persistence is needed)
current_topic = None  # Track the current topic for voting

# Store topics in memory (instead of positions.txt)
topics = []  # Will store the topics that admin can modify

@app.route('/', methods=['GET'])
def index():
    return render_template('login.html')  # Show the login form

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')  # Get the username from the form

    if not username:
        flash("Please enter a username.", "danger")
        return redirect(url_for('index'))  # If no username is provided, stay on login page

    # Allow admin to bypass username check
    if username == 'admin':
        session['username'] = username  # Store username in session
        flash(f"Welcome, {username}!", "success")
        return redirect(url_for('admin_dashboard'))  # Redirect to admin dashboard if username is admin

    try:
        # Check if username exists in 'usernames.txt'
        with open(usernames_file, 'r') as file:
            usernames = file.read().splitlines()  # Read all usernames into a list

        if username in usernames:
            session['username'] = username  # Store username in session
            flash(f"Welcome, {username}!", "success")
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

    if not topics:
        flash("No topics available to vote for.", "danger")
        return redirect(url_for('admin_dashboard'))  # Redirect to admin dashboard if no topics exist

    # Get the first topic (you can modify this to cycle through topics if needed)
    topic = topics[0] if topics else None

    try:
        # Read the names from 'choices.txt'
        with open(names_file, 'r') as file:
            names = file.read().splitlines()

        return render_template('vote.html', topic=topic, names=names)  # Pass topic and names to template

    except FileNotFoundError:
        flash("Names file not found.", "danger")
        return redirect(url_for('index'))  # Redirect to login if file is missing

@app.route('/submit_vote', methods=['POST'])
def submit_vote():
    if 'username' not in session:
        return redirect(url_for('index'))  # Redirect to login if not logged in

    name = request.form.get('name')  # Get the selected name from the form

    if not name:
        flash("Please select a name to vote for.", "danger")
        return redirect(url_for('vote'))  # Redirect back to the voting page if no name is selected

    username = session['username']

    try:
        # Check if the user has already voted for the current topic by reading the votes file
        with open(votes_file, 'r') as file:
            votes = file.read().splitlines()

        # Find the current topic to check if the user has voted for it
        global current_topic  # Use the global variable that tracks the current topic

        if current_topic is None:
            flash("No active topic available.", "danger")
            return redirect(url_for('vote'))  # Ensure there's a topic to vote for

        # If the user has already voted for the current topic, notify them
        if any(vote.startswith(username + f":{current_topic}:") for vote in votes):
            flash(
                f"You have already voted for the topic '{current_topic}', {username}. You can only vote once per topic.",
                "danger")
            return redirect(url_for('vote'))  # Redirect back to voting page if they have already voted

        # Save the vote with the username and current topic (e.g., 'username: current_topic: name')
        with open(votes_file, 'a') as file:
            file.write(f"{username}:{current_topic}:{name}\n")  # Store username, topic, and vote

        flash(f"Your vote for {name} has been recorded for topic '{current_topic}'!", "success")
        return redirect(url_for('vote'))  # Stay on the voting page after voting

    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for('vote'))  # Redirect back to voting page if any error occurs

@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'username' not in session or session['username'] != 'admin':
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('index'))  # Redirect if the user is not admin

    if request.method == 'POST':
        # New feature to add voters
        num_voters = request.form.get('num_voters')

        if not num_voters or not num_voters.isdigit() or int(num_voters) <= 0:
            flash("Please enter a valid number of voters.", "danger")
            return redirect(url_for('admin_dashboard'))

        num_voters = int(num_voters)

        # Generate random 4-digit numbers for voters
        generated_usernames = [str(random.randint(1000, 9999)) for _ in range(num_voters)]

        try:
            # Update the 'usernames.txt' file with the generated usernames
            with open(usernames_file, 'a') as file:
                for username in generated_usernames:
                    file.write(f"{username}\n")

            flash(f"{num_voters} new voters have been added.", "success")
        except Exception as e:
            flash(f"An error occurred while updating usernames: {str(e)}", "danger")

    return render_template('admin_dashboard.html')  # Show the dashboard for admin

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
            name = vote.split(":")[1]  # Extract the name from the vote
            if name in vote_count:
                vote_count[name] += 1
            else:
                vote_count[name] = 1

        return render_template('tally.html', tally=vote_count)  # Pass the tally data to the template

    except FileNotFoundError:
        flash("Votes file not found.", "danger")
        return redirect(url_for('admin_dashboard'))  # Redirect to admin dashboard if votes file is missing
@app.route('/enter_voters', methods=['POST'])
def enter_voters():
    if 'username' not in session or session['username'] != 'admin':
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('index'))  # Ensure only admin can access this route

    num_voters = request.form.get('num_voters')  # Get the number of voters from the form

    if not num_voters or not num_voters.isdigit() or int(num_voters) <= 0:
        flash("Please enter a valid number of voters.", "danger")
        return redirect(url_for('admin_dashboard'))  # Redirect to admin dashboard if invalid number

    num_voters = int(num_voters)

    # Generate random 4-digit numbers for voters
    generated_usernames = [str(random.randint(1000, 9999)) for _ in range(num_voters)]

    try:
        # Overwrite the 'usernames.txt' file with the new generated usernames
        with open(usernames_file, 'w') as file:  # 'w' mode overwrites the file
            for username in generated_usernames:
                file.write(f"{username}\n")

        flash(f"{num_voters} new voters have been added.", "success")
        return redirect(url_for('admin_dashboard'))  # Redirect back to admin dashboard

    except Exception as e:
        flash(f"An error occurred while updating usernames: {str(e)}", "danger")
        return redirect(url_for('admin_dashboard'))  # Redirect back to admin dashboard if an error occurs


@app.route('/update_topic', methods=['POST'])
def update_topic():
    if 'username' not in session or session['username'] != 'admin':
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('index'))  # Ensure only admin can access this route

    new_topic = request.form.get('new_topic')

    if not new_topic:
        flash("Topic cannot be empty.", "danger")
        return redirect(url_for('admin_dashboard'))  # Redirect back to the dashboard if no topic is entered

    global current_topic
    current_topic = new_topic  # Set the new current topic

    flash(f"The topic has been updated to '{new_topic}' successfully!", "success")
    return redirect(url_for('admin_dashboard'))  # Redirect back to the admin dashboard


@app.route('/view_usernames')
def view_usernames():
    if 'username' not in session or session['username'] != 'admin':
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('index'))  # Redirect if the user is not admin

    try:
        # Read the usernames from the 'usernames.txt' file
        with open(usernames_file, 'r') as file:
            usernames = file.read().splitlines()

        return render_template('view_usernames.html', usernames=usernames)  # Pass usernames to template

    except FileNotFoundError:
        flash("Usernames file not found.", "danger")
        return redirect(url_for('admin_dashboard'))  # Redirect back to admin dashboard if the file is missing

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)