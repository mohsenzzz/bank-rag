from pathlib import Path
import os, re, json, time
import requests

BASE_DIR = Path.cwd()
PDF_DIR = BASE_DIR / "pdfs"
CACHE_DIR = BASE_DIR / "cache"
PDF_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)

LINKS_FILE = BASE_DIR / "links.txt"

def download_pdfs():
    urls=[]
    
    with open(LINKS_FILE, 'r') as file:
        lines = file.readlines()
        for line in lines:
            urls.append(line)
        downloaded = []
        
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "application/pdf,*/*;q=0.8",
        }
        with requests.Session() as session:
            session.headers.update(headers)
            for index, url in enumerate(urls):
                pdf_path = PDF_DIR / f"document_{index}.pdf"
            
                    
                url = url.strip()
                response = session.get(
                    url,
                    timeout=30,
                    allow_redirects=True
                )
            
                pdf_path.write_bytes(response.content)
                downloaded.append(pdf_path)
        return downloaded