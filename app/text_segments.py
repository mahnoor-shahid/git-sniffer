import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from gensim.summarization import summarize
import requests

# Ensure you have the required NLTK resources
nltk.download('punkt')
nltk.download('stopwords')

def clean_readme(text):
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

def generate_summary(text):
    # Tokenize the text into sentences
    sentences = sent_tokenize(text)
    
    # If the text is too short, return it as is
    if len(sentences) < 10:
        return text
    
    # Use Gensim's summarize function
    try:
        summary = summarize(text, word_count=100)
        return summary
    except ValueError:
        return text  # If summarization fails, return the original text

def process_readme_file(readme_url):
    # Fetch the README content
    response = requests.get(readme_url)
    text = response.text
    
    # Clean the README content
    clean_text = clean_readme(text)
    
    # Generate a summary
    summary = generate_summary(clean_text)
    
    return summary

# Example usage
readme_url = "https://raw.githubusercontent.com/biopython/biopython/master/README.rst"
summary = process_readme_file(readme_url)
print("Repository Summary:")
print(summary)
