#!/usr/bin/env python
import requests
from bs4 import BeautifulSoup

# Fetch the HTML
#response = requests.get('https://docs.perplexity.ai/docs/model-cards')
response = requests.get('https://docs.perplexity.ai/guides/model-cards')

# Parse the HTML
soup = BeautifulSoup(response.text, 'html.parser')

# Find the tables by their preceding h2 IDs
h2_ids = ['perplexity-sonar-models', 'perplexity-chat-models', 'open-source-models']

tables = {}
for h2_id in h2_ids:
  h2_tag = soup.find('h2', {'id': h2_id})
  if h2_tag:
    # Find the next sibling table
    table_tag = h2_tag.find_next_sibling('table')
    if table_tag:
      tables[h2_id] = table_tag

# Function to print table rows as text, formatted as a table (lpad, rpad)
def print_table(table):
    for row in table.find_all('tr'):
       cells = [cell.text for cell in row.find_all('td')]
       #    print(' '.join(cell.text for cell in row.find_all('td')))        # simpler version
       if len(cells) == 4:
           print(cells[0].ljust(33) + cells[1].rjust(6) + cells[2].rjust(8) + cells[3].rjust(16))
i = 0

for t in tables:
  print(t)
  print_table(tables[t])
  # Print the first and second tables
  if t == 'perplexity-sonar-models':
    print("Note: 'online' LLMs do not attend to the system prompt given in 'instruction.txt'")
  print("")