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
       cells = [cell.text for cell in row.find_all('td')]
       #    print(' '.join(cell.text for cell in row.find_all('td')))        # simpler version
       if len(cells) == 4:
           print(cells[0].ljust(32) + cells[1].rjust(5) + cells[2].rjust(8) + cells[3].rjust(16))

# Print the first and second tables
if len(tables) > 0:
    print("Perplexity Models:")
    print_table(tables[0])
    print("Note: 'online' LLMs do not attend to the system prompt given in 'instruction.txt'")

if len(tables) > 1:
    print("\nOpen-Source Models:")
    print_table(tables[1])
