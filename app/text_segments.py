import os
import re
from nltk.tokenize import sent_tokenize
from sumy.parsers.plaintext import PlaintextParser
from sumy.summarizers.lsa import LsaSummarizer
from sumy.nlp.tokenizers import Tokenizer
import csv 

def clean_readme(text):
    """
    Clean the README text by removing URLs, badge images, special characters, and extra spaces.
    """
    # Remove URLs
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'https\S+', '', text)
    text = re.sub(r'www\S+', '', text)
    
    # Remove badge images and other non-informative text
    text = re.sub(r'\.\. image::[^\n]*', '', text)
    text = re.sub(r'\.\. \[.*\]:[^\n]*', '', text)
    
    # Remove special characters
    text = re.sub(r'[^A-Za-z0-9\s]+', ' ', text)
    
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def tokenize_and_summarize(text):
    """
    Summarize the cleaned text using Sumy.
    """
    # Tokenize the text into sentences
    sentences = sent_tokenize(text)
    
    # If the text is too short, return it as is
    # if len(sentences) < 10:
        # return text
    
    # Create a PlaintextParser object
    parser = PlaintextParser.from_string(text, Tokenizer('english'))
    
    # Initialize the LsaSummarizer
    summarizer = LsaSummarizer()
    
    # Generate a summary
    summary = summarizer(parser.document, 5)  # Summarize into 10 sentences
    
    # Convert summary sentences to a string
    summary_text = ' '.join(str(sentence) for sentence in summary)
    
    return summary_text

def generate_summary(src_dir, target_dir):
    """
    Process all README files in the source directory and save the summaries in the target directory.
    """
    summaries = {}
    
    # Ensure the target directory exists
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    
    # CSV file path
    csv_file_path = os.path.join(target_dir, 'readme_summaries.csv')
    
    # Iterate over files in the source directory
    for filename in os.listdir(src_dir):
        # Match files in the format {repo_owner}++{repo_name}_README.md
        if filename.lower().endswith("_readme.md"):
            file_path = os.path.join(src_dir, filename)
            
            # Read the README file content
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            
            # Clean the README content
            clean_text = clean_readme(text)
            
            # Generate a summary
            summary = tokenize_and_summarize(clean_text)
            
            # Store the summary in the dictionary
            summaries[filename] = summary
    
    # Write summaries to a CSV file
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Filename', 'Summary']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for filename, summary in summaries.items():
            writer.writerow({'Filename': filename, 'Summary': summary})
    
    print(f"\nSummaries and file names saved in {os.path.join(target_dir, 'readme_summaries.csv')}")

