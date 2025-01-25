import sqlite3

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('coaches.db')
cursor = conn.cursor()

# Create the athletes table
cursor.execute('''
CREATE TABLE IF NOT EXISTS coaches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    availability TEXT NOT NULL,
    gender TEXT NOT NULL,
    gym TEXT NOT NULL
);
''')
# Insert data into the athletes table
fitness_coaches = [
    ('John Doe', 'Abu dhabi', 'Weekdays', 'Male', 'Gold’s Gym'),
    ('Jane Smith', 'Dubai', 'Weekends', 'Female', 'Equinox'),
    ('Mike Johnson', 'Abu dhabi', 'Weekdays', 'Male', 'LA Fitness'),
    ('Emily Davis', 'Dubai', 'Weekends', 'Female', 'Crunch Fitness'),
    ('Chris Brown', 'Abu dhabi', 'Weekends', 'Male', '24 Hour Fitness'),
    ('Sarah Wilson', 'Dubai', 'Weekends', 'Female', 'Planet Fitness'),
    ('David Lee', 'Abu dhabi', 'Weekdays', 'Male', 'YMCA'),
    ('Laura Taylor', 'Dubai', 'Weekdays', 'Female', 'Anytime Fitness'),
    ('James White', 'Abu dhabi', 'Weekdays', 'Male', 'Life Time Fitness'),
    ('Anna Martinez', 'Dubai', 'Weekends', 'Female', 'CrossFit Gym')
]

cursor.executemany('''
INSERT INTO coaches (name, location, availability, gender, gym)
VALUES (?, ?, ?, ?,?);
''', fitness_coaches)

# Commit the transaction
conn.commit()

# Close the connection
conn.close()

print("Database 'coaches.db' created and data inserted successfully.")