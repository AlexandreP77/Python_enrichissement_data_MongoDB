import pandas as pd
from pymongo import MongoClient

male_df = pd.read_csv('data/male.csv')
female_df = pd.read_csv('data/female.csv')

male_df.drop(male_df.columns[0], axis=1, inplace=True)
female_df.drop(female_df.columns[0], axis=1, inplace=True)

uri = "mongodb+srv://"identifaint":"mot de passe"@cluster0.pcxwo.mongodb.net"
client = MongoClient(uri)

db = client['mortalite']
mortalite_collection = db['mortalite_collection']

# Insertion des données
mortalite_collection.insert_many(male_df.to_dict('records'))
mortalite_collection.insert_many(female_df.to_dict('records'))
