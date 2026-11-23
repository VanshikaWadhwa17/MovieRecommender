
import pandas as pd
import json

movies = pd.read_csv("data/tmdb/movies.csv")
credits = pd.read_csv("data/tmdb/credits.csv")

print("\n========== MOVIES DATASET ==========")
print("Total records:", len(movies))
print("Columns:", movies.columns.tolist())
print("\nFirst 2 records:")
print(movies.head(2).to_string())

print("\n========== CREDITS DATASET ==========")
print("Total records:", len(credits))
print("Columns:", credits.columns.tolist())
print("\nFirst 2 records:")
print(credits.head(2).to_string())

print("\n========== JSON STRUCTURE INSPECTION ==========")

# Inspect genres from movies.csv
print("\nGenres:")
print(movies["genres"].iloc[0])

# Inspect cast from credits.csv
print("\nCast:")
print(credits["cast"].iloc[0])

# Inspect crew from credits.csv
print("\nCrew:")
print(credits["crew"].iloc[0])

# Check whether movie IDs match
print("\n========== ID MATCHING ==========")
print("Movie ID:", movies["id"].iloc[0])
print("Credits movie ID:", credits["movie_id"].iloc[0])