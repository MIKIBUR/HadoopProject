import pandas as pd
import re 

# Read the CSV file with tab delimiter and suppress DtypeWarning
df = pd.read_csv('raw_data.csv', dtype=str, error_bad_lines=False)

# Function to extract politician names from tweet text
def extract_politician(tweet_text):
    if isinstance(tweet_text, str):  # Check if tweet_text is a string
        mention = re.search(r'\b(?:obama|trump|clinton)\b', tweet_text, flags=re.IGNORECASE)
        if mention:
            return mention.group(0).lower()  # Return the lowercase version of the politician's name
    return None

df['text'] = df['text'].str.replace(',', '')

# Add a new column "politician" and fill it with the name of the politician mentioned
df['politician'] = df['text'].apply(extract_politician)

# Remove rows with multiple politicians mentioned
df = df[df['politician'].notna()]  # Remove rows with no politician mentioned
df = df.drop_duplicates(subset=['text', 'politician'])  # Remove duplicates

# Discard tweets with no politician mentioned
df = df[df['politician'].notna()]

# Select only the "date", "text", and "politician" columns
df = df[['date', 'text', 'politician']]

# Convert "date" column to datetime format
df['date'] = pd.to_datetime(df['date'])

# Sort by the "date" column
df = df.sort_values(by='date')

# Write the modified data back to a new CSV file
df.to_csv('cleaned_file.csv', index=False)
