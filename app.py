from flask import Flask, request, render_template, send_file, redirect, url_for
import requests
import os
import shutil
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

app = Flask(__name__)

# Ścieżka do lokalnych plików
LOCAL_DIR = 'local_site'

def save_resource(url, base_url, folder):
    """Pobiera i zapisuje zasób ze strony."""
    try:
        resource_url = urljoin(base_url, url)
        parsed_url = urlparse(resource_url)
        resource_path = os.path.join(folder, parsed_url.path.lstrip('/'))
        os.makedirs(os.path.dirname(resource_path), exist_ok=True)
        
        response = requests.get(resource_url)
        with open(resource_path, 'wb') as file:
            file.write(response.content)
            
        return parsed_url.path
    except Exception as e:
        print(f"Nie udało się pobrać {url}: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fetch', methods=['POST'])
def fetch():
    url = request.form['url']
    response = requests.get(url)
    if response.status_code == 200:
        if os.path.exists(LOCAL_DIR):
            shutil.rmtree(LOCAL_DIR)
        os.makedirs(LOCAL_DIR, exist_ok=True)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        base_url = url
        
        # Pobierz wszystkie skrypty, arkusze stylów i inne zasoby
        for tag in soup.find_all(['script', 'link', 'img']):
            if tag.name == 'script' and tag.get('src'):
                src = tag['src']
                tag['src'] = save_resource(src, base_url, LOCAL_DIR)
            elif tag.name == 'link' and tag.get('href') and 'stylesheet' in tag.get('rel', []):
                href = tag['href']
                tag['href'] = save_resource(href, base_url, LOCAL_DIR)
            elif tag.name == 'img' and tag.get('src'):
                src = tag['src']
                tag['src'] = save_resource(src, base_url, LOCAL_DIR)

        # Zapisz zaktualizowany HTML
        with open(os.path.join(LOCAL_DIR, 'index.html'), 'w', encoding='utf-8') as file:
            file.write(str(soup))
            
        return render_template('edit.html', html=str(soup))
    else:
        return "Błąd podczas pobierania strony.", 400

@app.route('/edit', methods=['POST'])
def edit():
    new_html = request.form['html']
    with open(os.path.join(LOCAL_DIR, 'index.html'), 'w', encoding='utf-8') as file:
        file.write(new_html)
    return redirect(url_for('preview'))

@app.route('/preview')
def preview():
    return send_file(os.path.join(LOCAL_DIR, 'index.html'))

@app.route('/download')
def download():
    shutil.make_archive(LOCAL_DIR, 'zip', LOCAL_DIR)
    return send_file(f"{LOCAL_DIR}.zip", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
