import base64
import os
from datetime import datetime
import pdfplumber
import requests
from typing import List, Dict, Any

def generate_id(path: str) -> str:
    return base64.urlsafe_b64encode(path.encode()).decode().rstrip("=")

def generate_title_from_content(content: str) -> str:
    # Assume the title is the first line of the content
    title = content.split('\n', 1)[0].strip()
    return title if title else ''

def read_pdf(file_path: str) -> str:
    # Function to read text content from a PDF file
    with pdfplumber.open(file_path) as pdf:
        content = ""
        for page in pdf.pages:
            content += page.extract_text() + "\n"
    return content

def get_file_data(folder_path: str, base_path: str) -> List[Dict[str, Any]]:
    data_list = []
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path):
            if file_name.endswith('.pdf'):
                content = read_pdf(file_path)
            else:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
            relative_path = os.path.relpath(file_path, base_path)
            data_list.append({
                'id': generate_id(file_path),
                'content': content,
                'filepath': relative_path,
                'title': generate_title_from_content(content),
                'lastUpdated': datetime.fromtimestamp(os.path.getmtime(file_path)),
                'url': None
            })
        elif os.path.isdir(file_path):
            data_list.extend(get_file_data(file_path, base_path))  # Recursive call for directories
    return data_list

def fetch_url_content(url: str):
    """Fetch content from a URL and return it as a string."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for HTTP issues
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return ""

def add_urls_content(data_list: List[Dict[str, Any]], urls_file_path: str) -> None:
    """Read URLs from a file, fetch page content, and update the data_list."""
    if not os.path.isfile(urls_file_path):
        print(f"URLs file not found: {urls_file_path}")
        return

    with open(urls_file_path, 'r') as urls_file:
        urls = urls_file.readlines()

    for url in urls:
        url = url.strip()
        if url:
            content = fetch_url_content(url)
            data_list.append({
                'id': generate_id(url),
                'content': content,
                'filepath': None,
                'title': generate_title_from_content(content),
                'lastUpdated': datetime.now(),
                'url': url
            })

def get_all_data() -> List[Dict[str, Any]]:
    base_folder_path = os.path.join(os.path.dirname(__file__), '../data')
    data_list = get_file_data(base_folder_path, base_folder_path)
    urls_file_path = os.path.join(os.path.dirname(__file__), 'URL.txt')
    add_urls_content(data_list, urls_file_path)
    return data_list
