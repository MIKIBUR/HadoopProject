import pandas as pd
import time

# Specify the columns to read
columns_to_read = ['candidate_id', 'tweet_text', 'created_at']

# Define chunk size (number of rows per chunk)
chunk_size = 10**6  # 1 Million
dataset_size = 61631193

# Initialize an empty list to store chunks
chunks = []

# Load the CSV file in chunks
file_path = '2016_US_election_tweets.csv'
# Save the resulting DataFrame to a new CSV file
output_file = 'filtered_tweets.csv'
total_rows = 0  # Counter to track total rows processed

# Candidate mapping
candidate_mapping = {1: 'clinton', 2: 'trump', 3: 'obama', 4: 'sanders'}

# Start the timer for the whole program
start_time = time.time()

# Load the CSV file in chunks
for chunk in pd.read_csv(file_path, usecols=columns_to_read, chunksize=chunk_size):
    # Map candidate_id to actual candidate names

    # Append the filtered chunk to the list
    chunks.append(chunk)

    # Update total rows processed
    total_rows += len(chunk)

    # Print progress with time
    elapsed_time = time.time() - start_time
    print(f"Processed {total_rows/chunk_size} M rows so far... | Elapsed Time: {elapsed_time:.2f} seconds")
    print(f"Equals to {total_rows/dataset_size*100:.2f} %")

# Concatenate all chunks into a single DataFrame
df_filtered = pd.concat(chunks, ignore_index=True)
print(f"DataFrame created | Elapsed Time: {time.time() - start_time:.2f} seconds")

# Drop rows where 'tweet_text' is NaN
df_filtered.dropna(subset=['tweet_text'], inplace=True)
df_filtered.rename(columns={'tweet_text': 'text'}, inplace=True)
print(f"NaNs dropped | Elapsed Time: {time.time() - start_time:.2f} seconds")

df_filtered['politician'] = df_filtered['candidate_id'].map(candidate_mapping)
df_filtered.drop(columns=['candidate_id'], inplace=True)
print(f"Politicians mapped | Elapsed Time: {time.time() - start_time:.2f} seconds")

df_filtered['text'] = df_filtered['text'].str.replace(',', '', regex=False)
print(f"Comas deleted | Elapsed Time: {time.time() - start_time:.2f} seconds")

# Convert 'created_at' to timestamp
df_filtered['date'] = pd.to_datetime(df_filtered['created_at'])

# Drop the original 'created_at' column 
df_filtered.drop(columns=['created_at'], inplace=True)
print(f"created_at converted to datetime | Elapsed Time: {time.time() - start_time:.2f} seconds")

df_filtered = df_filtered[['date', 'text', 'politician']]
print(f"Columns reordered | Elapsed Time: {time.time() - start_time:.2f} seconds")

# Sort the DataFrame by 'timestamp' in ascending order
df_sorted = df_filtered.sort_values(by='date', ascending=True)
print(f"DataFrame sorted | Elapsed Time: {time.time() - start_time:.2f} seconds")

# Print first and last date in human-readable format
first_date = pd.to_datetime(df_sorted['date'].iloc[0], unit='s')
last_date = pd.to_datetime(df_sorted['date'].iloc[-1], unit='s')

print(f"Total number of rows in the DataFrame: {len(df_filtered)}")
print(f"First date: {first_date.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Last date: {last_date.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Elapsed Time: {time.time() - start_time:.2f} seconds")

# Overwrite the original file with the sorted DataFrame
df_sorted.to_csv(output_file, index=False, header=False)
print(f"\nSorted data has been saved to {output_file} | Total Elapsed Time: {time.time() - start_time:.2f} seconds.")
