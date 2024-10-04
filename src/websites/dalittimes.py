import os
import requests
from bs4 import BeautifulSoup
import pandas as pd

# set directory to root of project /Users/kushalkumar/Documents/india_dalit_violence/

os.chdir('/Users/kushalkumar/Documents/india_dalit_violence/') 


# Define the directory and file name for storing data
data_dir = 'data/raw/dalittimes'
data_file = os.path.join(data_dir, 'stories.csv')

# Create the directory if it doesn't exist
os.makedirs(data_dir, exist_ok=True)

def get_story_metadata_from_page(page_number):
    url = f"https://dalittimes.in/category/crime-2/page/{page_number}/" if page_number > 1 else "https://dalittimes.in/category/crime-2/"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve page {page_number}. Status code: {response.status_code}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    articles = soup.find_all('div', class_='post-item post-grid')
    
    metadata_list = []
    for article in articles:
        link_tag = article.find('a', class_='post-thumbnail')
        title_tag = article.find('h2', class_='entry-title')
        author_tag = article.find('li', class_='post-author')
        date_tag = article.find('li', class_='post-date')
        summary_tag = article.find('div', class_='post-content').find('p')

        link = link_tag['href'] if link_tag else ''
        title = title_tag.get_text(strip=True) if title_tag else ''
        author = author_tag.get_text(strip=True) if author_tag else ''
        date = date_tag.get_text(strip=True) if date_tag else ''
        summary = summary_tag.get_text(strip=True) if summary_tag else ''

        metadata_list.append({'title': title, 'author': author, 'date': date, 'summary': summary, 'link': link})

    return metadata_list

def scrape_all_pages():
    all_metadata = []

    # Load existing data if available
    if os.path.exists(data_file):
        existing_data = pd.read_csv(data_file)
        existing_links = set(existing_data['link'])
    else:
        existing_data = pd.DataFrame()
        existing_links = set()

    # Iterate over all 37 pages
    for page_number in range(1, 38):
        print(f"Scraping page {page_number}...")
        page_metadata = get_story_metadata_from_page(page_number)
        
        # Filter out already existing links
        new_metadata = [metadata for metadata in page_metadata if metadata['link'] not in existing_links]
        
        all_metadata.extend(new_metadata)

    # Convert to DataFrame and append new data to existing data
    new_data_df = pd.DataFrame(all_metadata)
    
    if not new_data_df.empty:
        updated_data_df = pd.concat([existing_data, new_data_df], ignore_index=True)
        updated_data_df.to_csv(data_file, index=False)
        print(f"Data updated with {len(new_data_df)} new stories.")
    else:
        print("No new stories found.")

if __name__ == "__main__":
    scrape_all_pages()