# Import necessary libraries
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os
import torch




# Check GPU availability
device = "cuda:0" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")




# Function to read sitemap XML files from local directory - modify if using Google Colab
def load_sitemaps(directory):
    file_contents = []
    for filename in os.listdir(directory):
        if filename.endswith(".xml"):
            with open(os.path.join(directory, filename), "r", encoding="utf-8") as f:
                file_contents.append(f.read())
    return file_contents



# Sitemap parsing to extract URLs
def parse_sitemap(file_content):
    soup = BeautifulSoup(file_content, 'xml')  # Use 'xml' parser for XML files
    return soup.find_all('loc')
    
def get_recipe_urls(locations):
    return [loc.text for loc in locations if '/recipe/' in loc.text]




# Load sitemaps from the "sitemaps" directory 
sitemap_directory = r"C:\%name%/<directory>"
sitemap_contents = load_sitemaps(sitemap_directory)


# Storing and processing recipe URLs
urlArray = []  
for content in sitemap_contents:
    locations = parse_sitemap(content)
    urlArray.extend(get_recipe_urls(locations))


#Testrun by uncommenting the following code 
#urlArray = urlArray[:10]



# Assign IDs to the URLs (optional, useful for tracking)
idArray = list(range(1, len(urlArray) + 1))

# Check if execution is working correctly 
print(f"Total number of recipe URLs found: {len(urlArray)}")
print(f"First 10 URLs: {urlArray[:10]}")



# Create an empty DataFrame to store results
columns = [
    'Recipe Name', 'Recipe URL', 'Ingredients', 'Instructions', 'Prep Time', 
    'Cook Time', 'Total Time', 'Servings', 'Yield', 'Calories', 'Fat', 'Carbs', 'Protein'
]
df = pd.DataFrame(columns=columns)

# Counter for processed recipes tracking (Since it is vast, gives clarity on time of execution)
processed_count = 0




# --- Actual Extraction of details begins here ---
# Function to extract nutrition data
def extract_nutrition(nutrition_facts):
    if not nutrition_facts:
        return {key: "N/A" for key in ['Calories', 'Fat', 'Carbs', 'Protein']}
    nutrition_rows = nutrition_facts.find_all('tr')
    return {
        row.find_all('td')[1].text.strip(): row.find_all('td')[0].text.strip()
        for row in nutrition_rows
    }

# User-Agent header for HTTP requests
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# The Recipe data Scrape segment
for currUrl in urlArray:
    try:
        r = requests.get(currUrl, headers=headers)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, 'html5lib')

        recipe_name = soup.find('h1')
        recipe_name = recipe_name.text.strip() if recipe_name else "N/A"

        ingredient_div = soup.find_all('li', attrs={'class': 'mm-recipes-structured-ingredients__list-item'})
        ingredients = ', '.join(
            ' '.join(span.text.strip() for span in row.find_all('span') if span.text.strip())
            for row in ingredient_div
        ) if ingredient_div else "N/A"

        instruction_div = soup.find_all('li', attrs={'class': 'comp mntl-sc-block mntl-sc-block-startgroup mntl-sc-block-group--LI'})
        instructions = ' '.join(
            row.p.text.strip().replace('\n', '') for row in instruction_div
        ) if instruction_div else "N/A"

        details = soup.find('div', class_='mm-recipes-details__content')
        prep_time = details.find('div', string='Prep Time:').find_next('div', class_='mm-recipes-details__value').text.strip() if details and details.find('div', string='Prep Time:') else "N/A"
        cook_time = details.find('div', string='Cook Time:').find_next('div', class_='mm-recipes-details__value').text.strip() if details and details.find('div', string='Cook Time:') else "N/A"
        total_time = details.find('div', string='Total Time:').find_next('div', class_='mm-recipes-details__value').text.strip() if details and details.find('div', string='Total Time:') else "N/A"
        servings = details.find('div', string='Servings:').find_next('div', class_='mm-recipes-details__value').text.strip() if details and details.find('div', string='Servings:') else "N/A"
        yield_value = details.find('div', string='Yield:').find_next('div', class_='mm-recipes-details__value').text.strip() if details and details.find('div', string='Yield:') else "N/A"

        # Extract nutrition facts
        nutrition_facts = soup.find('div', id='mm-recipes-nutrition-facts-summary_1-0')
        nutrition_data = extract_nutrition(nutrition_facts)

        df = pd.concat([df, pd.DataFrame([{
            'Recipe Name': recipe_name,
            'Recipe URL': currUrl,
            'Ingredients': ingredients,
            'Instructions': instructions,
            'Prep Time': prep_time,
            'Cook Time': cook_time,
            'Total Time': total_time,
            'Servings': servings,
            'Yield': yield_value,
            'Calories': nutrition_data.get('Calories', "N/A"),
            'Fat': nutrition_data.get('Fat', "N/A"),
            'Carbs': nutrition_data.get('Carbs', "N/A"),
            'Protein': nutrition_data.get('Protein', "N/A")
        }])], ignore_index=True)

        # Increment processed count and print progress for every 5 recipes achieved
        processed_count += 1
        if processed_count % 500 == 0:
            print(f"Processed {processed_count} recipes")

        print(f"Processed: {currUrl}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching {currUrl}: {e}")
        continue

# Save the final DataFrame to CSV
output_file = "Proj_data.csv"
df.to_csv(output_file, index=False)
print(f"Data saved to {output_file}. Total recipes processed: {len(df)}")
