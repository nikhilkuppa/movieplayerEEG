from flask import Flask, jsonify, render_template, send_from_directory, request
import pandas as pd
import json

app = Flask(__name__)

def combine_metadata(row):
    return {
        'Soundtrack': 'Yes' if row['Soundtrack'] else 'No',
        'Special Effects': 'Yes' if row['Special_effects'] else 'No',
        'Sexual Scene': 'Yes' if row['Sexual_scene'] else 'No',
        'Action Scene': 'Yes' if row['Action_scene'] else 'No',
        'Transport Scene': 'Yes' if row['Transport_Scene'] else 'No',
        'Violence': 'Yes' if row['Violence'] else 'No',
        'People in Scene': 'Yes' if row['People_in_the_scene?'] else 'No',
        'Dialogue': 'Yes' if row['Dialogue'] else 'No',
        'Location of Climax': 'Yes' if row['Location_of_climax'] else 'No',
        'Eating / Food': 'Yes' if row['Eating_/_food'] else 'No',
        'Drinking Alcohol': 'Yes' if row['Drinking_alcohol'] else 'No',
        'Doing Drugs': 'Yes' if row['Doing_drugs'] else 'No'
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/movies')
def get_movies():
    df = pd.read_excel(r'T_movie_information.xlsx')
    df.rename(columns={'Gross worldwide': 'gross_worldwide', 'Opening weekend US & Canada' : 'openingweekend'}, inplace=True)
    df.fillna('N/A', inplace=True)
    print(df)
    return jsonify(df[['stimuli_id', 'stimuli_title', 'Intro', 'studio', 'iMDB', 'RT_Tomatometer', 'Year', 'gross_worldwide', 'budget', 'openingweekend']].to_dict(orient='records'))

@app.route('/api/scenes')
def get_scenes():
    stimuli_id = str(request.args.get('stimuli_id'))
    df = pd.read_excel(r'T_scene_combined.xlsx')
    df['stimuli_id'] = df['stimuli_id'].astype(str)
    df['metadata'] = df.apply(combine_metadata, axis=1)
    scenes = df[df['stimuli_id'] == stimuli_id][['scene_no', 'scene_start', 'scene_end', 'scene_duration', 'ISC_EEG', 'metadata']]
    scenes['metadata'] = scenes['metadata'].apply(json.dumps)
    return jsonify(scenes.to_dict(orient='records'))

@app.route('/mp4/<path:filename>')
def serve_file(filename):
    movie_name = filename.split('_scene')[0].strip().replace(' ', '_').rstrip('_')
    return send_from_directory(f'mp4/stimuli/Scenes_corrected/{movie_name}', filename)

if __name__ == '__main__':
    app.run(debug=True)

