from flask import Flask, jsonify, request, render_template, redirect
import pandas as pd
from pymongo import MongoClient
from bson import ObjectId
import matplotlib.pyplot as plt
import seaborn as sns
import base64
from io import BytesIO

app = Flask(__name__)


def connect_mongodb(uri):
    client = MongoClient(uri)
    return client

def create_database(client, db_name, collection_name):
    db = client[db_name]
    collection = db[collection_name]
    return collection

def insert_data_from_df(collection, df):
    data = df.to_dict('records')
    collection.insert_many(data)

def read_data_to_df(collection, query={}):
    cursor = collection.find(query)
    df = pd.DataFrame(list(cursor))
    return df

def read_data_life_expan(collection_expa, query={}):
    cursor = collection_expa.find(query)
    df_expa = pd.DataFrame(list(cursor))
    return df_expa

def update_data(collection, query, new_values):
    collection.update_many(query, {'$set': new_values})

def delete_data(collection, query):
    collection.delete_many(query)
    
@app.route('/graph')
def graph():
    # Lire les données de chaque collection dans des DataFrames
    data_mortalite = read_data_to_df(collection)
    data_expa = read_data_to_df(collection_expa)

    # Fusionner les DataFrames avec une fusion de type 'inner'
    data = pd.merge(data_mortalite, data_expa, left_on=['Location', 'Period'], right_on=['Entity', 'Year'], how='inner')
    data = data.drop(columns=['_id_y', 'Entity', 'Year'])

    # Calculer 'Adult Mortality Percentage' si nécessaire
    if 'Adult Mortality Percentage' not in data.columns:
        data['Adult Mortality Percentage'] = (data['Adult mortality rate'] / 1000) * data['Life expectancy']

    # Vérifier si la colonne 'Sex' existe
    if 'Sex' not in data.columns:
        print("'Sex' column is missing in the DataFrame")
        return "Erreur : La colonne 'Sex' requise n'existe pas"

    # Générer le graphique
    plt.figure(figsize=(10, 6))
    sns.barplot(x='Location', y='Adult Mortality Percentage', hue='Sex', data=data)
    plt.title('Taux de mortalité adulte par sexe et pays')
    plt.xlabel('Pays')
    plt.ylabel('Taux de mortalité adulte')
    plt.xticks(rotation=45)
    plt.legend(title='Sexe')

    # Sauvegarder le graphique dans un buffer
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    # Convertir le buffer en chaîne base64
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()

    return render_template('graph.html', image_base64=image_base64)




uri = "mongodb+srv://"identifiant":"ici mot de passe"@cluster0.pcxwo.mongodb.net"
client = connect_mongodb(uri)
collection = create_database(client, 'mortalite', 'mortalite_collection')
collection_expa = create_database(client, 'mortalite', 'Life_expectancy_Collection')


@app.route('/')
def index():
    data = read_data_to_df(collection)
    data2 = read_data_life_expan(collection_expa)

    # Création d'un dictionnaire pour un accès rapide aux données de data2
    data2_dict = {(row['Entity'], row['Year']): row for index, row in data2.iterrows()}

    # Ajout des colonnes de data2 à data si disponible
    for index, row in data.iterrows():
        key = (row['Location'], row['Period'])
        if key in data2_dict:
            for col in data2.columns:
                if col not in ['Entity', 'Year', '_id']:
                    data.at[index, col] = data2_dict[key][col]

    # Remplacement des valeurs NaN par 0
    data.fillna(0, inplace=True)

    # S'assurer que les colonnes sont de type numérique
    data['Adult Mortality Percentage'] = (pd.to_numeric(data['Adult mortality rate'], errors='coerce') / 1000) * data['Life expectancy']
    data['Life expectancy'] = pd.to_numeric(data['Life expectancy'], errors='coerce').fillna(0)


    # Calcul de 'Adult Mortality Percentage', en évitant la division par zéro
    data['Adult Mortality Percentage'] = data.apply(
        lambda row: (row['Adult mortality rate'] / row['Life expectancy']) * 100 if row['Life expectancy'] > 0 else 0, axis=1)

    return render_template('index.html', data=data.to_dict('records'), data2=data2.to_dict('records'))




@app.route('/insert', methods=['POST'])
def insert():
    ParentLocation = request.form['ParentLocation']
    Location = request.form['Location']
    Period = request.form['Period']
    Sex = request.form['Sex']
    Adult_mortality_rate = request.form['Adult mortality rate']
    DateModified = request.form['DateModified']
    

    data = pd.DataFrame({'ParentLocation': [ParentLocation], 'Location': [Location], 'Period': [Period], 'Sex': [Sex], 'Adult mortality rate':[Adult_mortality_rate], 'DateModified': [DateModified]})
                        
    insert_data_from_df(collection, data)

    # Rediriger vers la page d'index après avoir inséré les données
    return redirect('/')


@app.route('/read')
def read():
    data = read_data_to_df(collection)
    return render_template('index.html', data=data.to_dict('records'))


@app.route('/edit/<string:id>', methods=['GET', 'POST'])
def edit(id):

    data_to_edit = collection.find_one({'_id': ObjectId(id)})

    if request.method == 'POST':

        ParentLocation = request.form['ParentLocation']
        Location = request.form['Location']
        Period = request.form['Period']
        Sex = request.form['Sex']
        Adult_mortality_rate = request.form['Adult mortality rate']
        DateModified = request.form['DateModified']

        collection.update_one({'_id': ObjectId(id)}, {'$set': {'ParentLocation': ParentLocation, 'Location': Location, 'Period': Period, 'Sex': Sex, 'Adult mortality rate':Adult_mortality_rate, 'DateModified': DateModified}})
        return redirect('/')
    
    return render_template('edit.html', data=data_to_edit)


@app.route('/delete/<string:id>', methods=['GET', 'POST'])
def delete(id):

    data_to_delete = collection.find_one({'_id': ObjectId(id)})

    if request.method == 'POST':
 
        collection.delete_one({'_id': ObjectId(id)})
        
        return redirect('/')
    
    return render_template('delete.html', data=data_to_delete)


if __name__ == '__main__':
    app.run(debug=True)
