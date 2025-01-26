#!/usr/bin/env python
import requests
from bs4 import BeautifulSoup

# Fetch the HTML
response = requests.get('https://docs.perplexity.ai/guides/model-cards')

# Parse the HTML
soup = BeautifulSoup(response.text, 'html.parser')

# Find the first and second tables
tables = soup.find_all('table')

# Function to print table rows as text, formatted as a table (lpad, rpad)
def print_table(table):
    for row in table.find_all('tr'):
       #print(' '.join(cell.text for cell in row.find_all('td')))        # simpler version
       cells = [cell.text for cell in row.find_all('td')]
       if len(cells) == 3:
           print(cells[0].ljust(36) + cells[1].rjust(10) + cells[2].rjust(18)) #+ cells[3].rjust(16))
#
# Print the first and second tables
if len(tables) > 0:
    print("Perplexity Sonar Models (support for citations):")
    print_table(tables[0])

if len(tables) > 1:
    print("\nLegacy Models (until 2025-02-22):")
    print_table(tables[1])
    print("Note: 'online' LLMs do not attend to any system prompts.")
