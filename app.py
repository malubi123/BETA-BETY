import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, send_from_directory, redirect, url_for
import zipfile

app = Flask(__name__)

# Konfiguracja katalogów
PROJECT_DIR = 'project'
os.makedirs(PROJECT_DIR, exist_ok=True)

def fetch_website_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Failed to fetch website data: Status code {response.status_code}")

def save_file(content, filename):
    with open(os.path.join(PROJECT_DIR, filename), 'w', encoding='utf-8') as file:
        file.write(content)

def update_project_with_website(url):
    html_content = fetch_website_data(url)
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Zapisz HTML
    save_file(str(soup), 'index.html')
    
    # Zapisz CSS i JS z HTML
    for link in soup.find_all('link', {'rel': 'stylesheet'}):
        css_url = link.get('href')
        if css_url:
            css_content = fetch_website_data(css_url)
            save_file(css_content, os.path.basename(css_url))
    
    for script in soup.find_all('script', {'src': True}):
        js_url = script.get('src')
        if js_url:
            js_content = fetch_website_data(js_url)
            save_file(js_content, os.path.basename(js_url))

def create_zip_file():
    zip_path = 'updated_project.zip'
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, dirs, files in os.walk(PROJECT_DIR):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), PROJECT_DIR))

@app.route('/')
def home():
    filenames = os.listdir(PROJECT_DIR)
    return render_template('index.html', filenames=filenames)

@app.route('/edit/<filename>', methods=['GET', 'POST'])
def edit_file(filename):
    file_path = os.path.join(PROJECT_DIR, filename)
    if request.method == 'POST':
        new_content = request.form['content']
        save_file(new_content, filename)
        return redirect(url_for('home'))
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    return render_template('edit.html', filename=filename, content=content)

@app.route('/files/<path:filename>')
def serve_files(filename):
    return send_from_directory(PROJECT_DIR, filename)

@app.route('/download')
def download():
    create_zip_file()
    return send_from_directory('.', 'updated_project.zip', as_attachment=True)

def main():
    url = input("Enter the URL of the website to scrape: ")
    update_project_with_website(url)
    app.run(port=5000, debug=True)

if __name__ == "__main__":
    main()
