from tabulate import tabulate
import csv 
import os

def structure_metadata(input_file, search_term):

    output_file_txt = os.path.join('data', 'metadata', f'{search_term}_summary.txt')
    # output_file_csv = os.path.join('data', 'metadata', f'{search_term}_structured_metadata.csv')

    # Read the CSV file
    with open(input_file, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        # Prepare the data for tabulation
        table_data = []
        for row in reader:
            table_data.append([
                row['name'],
                row['owner'].split("'login': '")[1].split("'")[0],
                row['html_url'],
                row['description'],
                row['stargazers_count'],
                row['forks_count'],
                row['language'],
                row['open_issues_count'],
                row['created_at'],
                row['updated_at'],
                row['default_branch'],
                row['license'],
                row['topics'],
                row['private']
            ])

    # Define the headers for the table
    headers = ["Repository Name", "Owner", "URL", "Description", "Stars", "Forks", "Language", "Issues", "Created At", "Updated At", "Default Branch", "License", "Topics", "Private"]

    # Format the table using tabulate
    formatted_table = tabulate(table_data, headers=headers, tablefmt='pipe', stralign='center')

    # Save the formatted table to a text file
    with open(output_file_txt, mode='w', encoding='utf-8') as file:
        file.write(formatted_table)

    print("\nMetadata successfully saved!")

'''
    # Save the structured data to a CSV file
    with open(output_file_csv, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(headers)  # Write the headers
        writer.writerows(table_data)  # Write the data rows
'''

