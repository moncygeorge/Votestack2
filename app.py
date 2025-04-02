from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
import random
import os  # <-- Make sure this import is present
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necessary for flash messages to work

# Path to the ssl certificate and key
ssl_cert = 'ssl/server.crt'
ssl_key = 'ssl/server.key'

# Path to the file containing usernames
usernames_file = 'usernames.txt'
names_file = 'choices.txt'
votes_file = 'votes.txt'
topic_file = 'current_topic.txt'  # New file to store current topic

# Load the current topic from the file when the app starts
def load_current_topic():
    try:
        with open(topic_file, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        return None  # Return None if no topic file exists

current_topic = load_current_topic()  # Load current topic from file on startup

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

    if not current_topic:
        flash("No topics available to vote for.", "danger")
        return redirect(url_for('admin_dashboard'))  # Redirect to admin dashboard if no topics exist

    # Get the current topic
    topic = current_topic

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

        # If the user has already voted for the current topic, notify them
        if any(vote.startswith(username + f":{current_topic}:") for vote in votes):
            flash(f"You have already voted for the topic '{current_topic}', {username}. You can only vote once per topic.", "danger")
            return redirect(url_for('vote'))  # Redirect back to voting page if they have already voted

        # Save the vote with the username and current topic (e.g., 'username: current_topic: name')
        with open(votes_file, 'a') as file:
            file.write(f"{username}:{current_topic}:{name}\n")  # Store username, topic, and vote

        flash(f"Your vote for {name} has been recorded for topic '{current_topic}'!", "success")
        return redirect(url_for('vote'))  # Stay on the voting page after voting

    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for('vote'))  # Redirect back to voting page if any error occurs

@app.route('/api/current_topic', methods=['GET'])
def get_current_topic_api():
    """API endpoint to get the current topic."""
    return jsonify({"topic": current_topic}), 200
@app.route('/view_topic', methods=['GET'])
def view_topic():
    if 'username' not in session or session['username'] != 'admin':
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('index'))  # Ensure only admin can access this route

    # If a topic exists, pass it to the template, otherwise show a message
    if current_topic:
        return render_template('view_topic.html', topic=current_topic)
    else:
        flash("No topic has been set.", "warning")
        return redirect(url_for('admin_dashboard'))  # Redirect to admin dashboard
@app.route('/api/submit_vote', methods=['POST'])
def submit_vote_api():
    """API endpoint for submitting votes."""
    data = request.get_json()

    if 'username' not in session:
        return jsonify({"error": "Please log in first."}), 401

    username = session['username']
    name = data.get('name')

    if not name:
        return jsonify({"error": "Please select a name to vote for."}), 400

    try:
        # Check if the user has already voted for the current topic by reading the votes file
        with open(votes_file, 'r') as file:
            votes = file.read().splitlines()

        # If the user has already voted for the current topic, notify them
        if any(vote.startswith(username + f":{current_topic}:") for vote in votes):
            return jsonify({"error": "You have already voted."}), 400

        # Save the vote with the username and current topic (e.g., 'username: current_topic: name')
        with open(votes_file, 'a') as file:
            file.write(f"{username}:{current_topic}:{name}\n")  # Store username, topic, and vote

        return jsonify({"message": f"Your vote for {name} has been recorded for topic '{current_topic}'!"}), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
# Route to view the current choices
@app.route('/view_choices', methods=['GET'])
def view_choices():
    if 'username' not in session or session['username'] != 'admin':
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('index'))  # Ensure only admin can access this route

    try:
        # Read the choices from the 'choices.txt' file
        with open(names_file, 'r') as file:
            choices = file.read().splitlines()

        if not choices:
            flash("No choices available.", "warning")  # Show a message if no choices are available

        return render_template('view_choices.html', choices=choices)  # Pass choices to template

    except FileNotFoundError:
        flash("Choices file not found.", "danger")
        return redirect(url_for('admin_dashboard'))  # Redirect to admin dashboard if file is missing

# Route to update the choices (allow admin to input new choices)
@app.route('/update_choices', methods=['POST'])
def update_choices():
    global choices
    if request.method == 'POST':
        # Get the choices from the form, split by new lines
        new_choices = request.form.get('choices').splitlines()

        # Update the existing choices with the new ones
        choices = new_choices

        # Save the updated choices to a file (or database)
        with open('choices.txt', 'w') as file:
            # Convert the list to a single string with each choice on a new line
            file.write("\n".join(new_choices))

        # Flash a success message
        flash("Choices have been updated successfully!", category='success')
        return redirect(url_for('admin_dashboard'))
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

@app.route('/generate_tally', methods=['GET', 'POST'])
def generate_tally():
    if 'username' not in session or session['username'] != 'admin':
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('index'))  # Ensure only admin can access this route

    try:
        # Read the names from 'choices.txt' (the available choices)
        with open(names_file, 'r') as file:
            choices = file.read().splitlines()

        # Initialize a dictionary to hold the tally for each topic and their choices
        tally = {}

        # Read the votes from 'votes.txt'
        with open(votes_file, 'r') as file:
            votes = file.read().splitlines()

        # Count the votes for each choice for each topic
        for vote in votes:
            try:
                username, topic, name = vote.split(":")
                if topic not in tally:
                    tally[topic] = {choice: 0 for choice in choices}  # Initialize a dict for the topic
                if name in tally[topic]:
                    tally[topic][name] += 1
            except ValueError:
                # Skip any malformed vote entries (in case there's a vote entry without the expected format)
                continue

        # Render the tally page with the vote counts for each topic
        return render_template('tally.html', tally=tally)  # Pass the tally data to the template

    except FileNotFoundError:
        flash("Votes file or choices file not found.", "danger")
        return redirect(url_for('admin_dashboard'))  # Redirect to admin dashboard if fi


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
        # Read existing usernames from the 'usernames.txt' file to avoid duplicates
        with open(usernames_file, 'r') as file:
            existing_usernames = set(file.read().splitlines())  # Use a set to avoid duplicates

        # Filter out usernames that already exist in 'usernames.txt'
        new_usernames = [username for username in generated_usernames if username not in existing_usernames]

        if not new_usernames:
            flash("All generated usernames already exist. No new usernames were added.", "warning")
            return redirect(url_for('admin_dashboard'))  # Redirect if no new usernames were generated

        # Update the 'usernames.txt' file with the new unique usernames
        with open(usernames_file, 'a') as file:
            for username in new_usernames:
                file.write(f"{username}\n")

        # Now, generate the PDF with the updated list of usernames
        all_usernames = list(existing_usernames) + new_usernames
        generate_pdf(all_usernames)

        flash(f"{len(new_usernames)} new voters have been added and a PDF has been generated.", "success")
        return redirect(url_for('admin_dashboard'))  # Redirect back to admin dashboard

    except Exception as e:
        flash(f"An error occurred while updating usernames: {str(e)}", "danger")
        print(f"Error: {str(e)}")  # Log the error for debugging
        return redirect(url_for('admin_dashboard'))  # Redirect back to admin dashb

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

    # Save the new topic to the file
    with open(topic_file, 'w') as file:
        file.write(new_topic)

    flash(f"The topic has been updated to '{new_topic}' successfully!", "success")
    return redirect(url_for('admin_dashboard'))  # Redirect back to the admin dashboard
def generate_users():
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
        # Read existing usernames from the 'usernames.txt' file to avoid duplicates
        with open(usernames_file, 'r') as file:
            existing_usernames = set(file.read().splitlines())  # Use a set to avoid duplicates

        # Filter out usernames that already exist in 'usernames.txt'
        new_usernames = [username for username in generated_usernames if username not in existing_usernames]

        if not new_usernames:
            flash("All generated usernames already exist. No new usernames were added.", "warning")
            return redirect(url_for('admin_dashboard'))  # Redirect if no new usernames were generated

        # Update the 'usernames.txt' file with the new unique usernames
        with open(usernames_file, 'a') as file:
            for username in new_usernames:
                file.write(f"{username}\n")

        # Now, generate the Word document with the updated list of usernames
        # Combine the old and new usernames
        all_usernames = list(existing_usernames) + new_usernames
        create_word_document(all_usernames)

        flash(f"{len(new_usernames)} new voters have been added and a Word document has been generated.", "success")
        return redirect(url_for('admin_dashboard'))  # Redirect back to admin dashboard

    except Exception as e:
        flash(f"An error occurred while updating usernames: {str(e)}", "danger")
        print(f"Error: {str(e)}")  # Log the error for debugging
        return redirect(url_for('admin_dashboard'))  # Redirect back to admin dashboard if an error occurs


def generate_pdf(usernames, output_file='static/voters_list.pdf'):
    c = canvas.Canvas(output_file, pagesize=letter)
    width, height = letter

    # Set up margins and font size for labels
    margin = 50
    column_width = (width - 3 * margin) / 2  # Divide the page into two columns
    label_height = 50  # Increased height of each label for taller cells
    font_size = 12
    max_users_per_column = 10  # Adjusted to fit more height for each user, reduced the max users per column

    c.setFont("Helvetica", font_size)

    # Split the usernames into two groups (columns)
    left_column_users = usernames[:max_users_per_column]
    right_column_users = usernames[max_users_per_column:max_users_per_column*2]

    # Initial y-positions for two columns
    y_position_left = height - margin - label_height  # Starting position for the left column
    y_position_right = height - margin - label_height  # Starting position for the right column

    # Draw the usernames in the left column
    for i, username in enumerate(left_column_users):
        c.setStrokeColor(colors.black)
        c.setFillColor(colors.white)
        c.rect(margin, y_position_left - label_height, column_width, label_height, fill=1)
        c.setFillColor(colors.black)
        c.drawString(margin + 10, y_position_left - label_height + 15, username)
        y_position_left -= label_height + 5  # Move down for the next label

    # Draw the usernames in the right column
    for i, username in enumerate(right_column_users):
        c.setStrokeColor(colors.black)
        c.setFillColor(colors.white)
        c.rect(margin + column_width + margin, y_position_right - label_height, column_width, label_height, fill=1)
        c.setFillColor(colors.black)
        c.drawString(margin + column_width + margin + 10, y_position_right - label_height + 15, username)
        y_position_right -= label_height + 5  # Move down for the next label

    # If there's space left in either column, continue filling in the next page
    if y_position_left <= margin and y_position_right <= margin:
        c.showPage()
        y_position_left = height - margin - label_height
        y_position_right = height - margin - label_height

    c.save()



@app.route('/download_voters_pdf')
def download_voters_pdf():
    try:
        # Path to the generated voters PDF
        file_path = os.path.join('static', 'voters_list.pdf')

        # Check if the file exists
        if not os.path.exists(file_path):
            flash("Voters list PDF not found.", "danger")
            return redirect(url_for('admin_dashboard'))  # Redirect back to the dashboard if the file doesn't exist

        # Serve the file for download
        return send_file(file_path, as_attachment=True)

    except Exception as e:
        flash(f"An error occurred while downloading the file: {str(e)}", "danger")
        return redirect(url_for('admin_dashboard'))  # Redirect back to admin dashboard if an error occurs


@app.route('/view_usernames')
def view_usernames():
    if 'username' not in session or session['username'] != 'admin':
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('index'))  # Redirect if the user is not admin

    try:
        # Read the usernames from the 'usernames.txt' file
        with open(usernames_file, 'r') as file:
            usernames = file.read().splitlines()  # Read all usernames line by line

        if not usernames:
            flash("No usernames found.", "warning")  # Show a message if no users are found

        return render_template('view_usernames.html', usernames=usernames)  # Pass usernames to template

    except FileNotFoundError:
        flash("Usernames file not found.", "danger")
        return redirect(url_for('admin_dashboard'))  # Redirect back to admin dashboard if the file is missing
@app.route('/delete_all_voters', methods=['POST'])
def delete_all_voters():
    if 'username' not in session or session['username'] != 'admin':
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('index'))  # Ensure only admin can access this route

    try:
        # Clear the usernames list by overwriting the file with an empty list
        with open(usernames_file, 'w') as file:
            file.write("")  # Overwrite the file with nothing

        flash("All voters have been deleted.", "success")
    except FileNotFoundError:
        flash("Usernames file not found.", "danger")
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")

    return redirect(url_for('view_usernames'))  # Redirect back to the view_usernames
@app.route('/delete_voter/<username>', methods=['POST'])
def delete_voter(username):
    if 'username' not in session or session['username'] != 'admin':
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('index'))  # Ensure only admin can access this route

    try:
        # Read the current usernames from the 'usernames.txt' file
        with open(usernames_file, 'r') as file:
            usernames = file.read().splitlines()

        # If the username exists, remove it from the list
        if username in usernames:
            usernames.remove(username)

            # Save the updated usernames back to the file
            with open(usernames_file, 'w') as file:
                for username in usernames:
                    file.write(f"{username}\n")

            flash(f"Voter {username} has been removed.", "success")
        else:
            flash(f"Voter {username} not found.", "warning")

    except FileNotFoundError:
        flash("Usernames file not found.", "danger")
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")

    return redirect(url_for('view_usernames'))  # Redirect back to the view_usernames page


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, ssl_context=(ssl_cert, ssl_key))
