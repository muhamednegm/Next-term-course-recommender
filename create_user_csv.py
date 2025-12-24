import pandas as pd
import os

# Load students.csv
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
students_csv_path = os.path.join(DATA_DIR, 'students.csv')
user_csv_path = os.path.join(DATA_DIR, 'user.csv')

print("Loading students.csv...")
students_df = pd.read_csv(students_csv_path, dtype=str)

# Create user.csv with university_id and password_hash columns
user_df = students_df[['university_id', 'password']].copy()
user_df.columns = ['university_id', 'password_hash']

# Save to user.csv
user_df.to_csv(user_csv_path, index=False)

print(f"user.csv created successfully with {len(user_df)} users")
print(f"Saved to: {user_csv_path}")
