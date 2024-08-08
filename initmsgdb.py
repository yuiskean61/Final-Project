import sqlite3

#Connect to the db or create new if doesn't exist
connection = sqlite3.connect('messages.db')
cursor = connection.cursor()

#Create a table for storing messages
cursor.execute('''
               CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                username TEXT,
                message TEXT
               )
               ''')

#Commit the changes and close connection
connection.commit()
connection.close()

print("Database setup completed")