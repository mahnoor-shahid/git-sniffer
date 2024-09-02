
from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch
import re
import os
import csv

# Set up device and summarizer
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"\nUsing device: {device}")

# Initialize tokenizer and model
MAX_TOKEN_LENGTH = 1024  # T5 models typically have a max length of 512 tokens

tokenizer = T5Tokenizer.from_pretrained("Falconsai/medical_summarization", legacy=False)
model = T5ForConditionalGeneration.from_pretrained("Falconsai/medical_summarization").to(device)

def clean_readme(text):
    """
    Clean the README text by removing URLs, badge images, special characters, and extra spaces.
    """
    text = re.sub(r'http\S+|https\S+|www\S+', '', text)  # More robust URL removal
    text = re.sub(r'\.\. image::[^\n]*|\. \[.*\]:[^\n]*', '', text)  # Clean non-informative content
    text = re.sub(r'[^A-Za-z0-9\s]', ' ', text)  # Remove special characters
    text = re.sub(r'\s+', ' ', text).strip()  # Remove extra spaces
    return text

def split_text(text, max_length):
    """
    Splits the text into chunks of max_length tokens.
    """
    tokens = tokenizer.tokenize(text)
    # Ensure tokens do not exceed the model's maximum token length
    return [tokens[i:i + max_length] for i in range(0, len(tokens), max_length)]

def return_summary(text):
    summaries = []
    text_chunks = split_text(text, MAX_TOKEN_LENGTH)
    batch_size = 2  # Smaller batch size for large models

    for i in range(0, len(text_chunks), batch_size):
        batch = text_chunks[i:i + batch_size]
        batch_texts = [' '.join(chunk) for chunk in batch]

        try:
            inputs = tokenizer(batch_texts, return_tensors="pt", padding=True, truncation=True, max_length=MAX_TOKEN_LENGTH, return_attention_mask=True).to(device)
            summary_ids = model.generate(
                inputs['input_ids'],
                max_length=300,
                min_length=100,
                length_penalty=1.5,
                num_beams=5,
                early_stopping=True
            )

            batch_summaries = [tokenizer.decode(g, skip_special_tokens=True) for g in summary_ids]
            summaries.extend(batch_summaries)
        except RuntimeError as e:
            print(f"RuntimeError: {e}")
            if 'CUDA error' in str(e):
                print("CUDA error likely caused by incorrect tensor size or input dimensions.")
            raise  # Re-raise the exception for further investigation

    return ' '.join(summaries)


def generate_summary(src_dir, target_dir):
    """
    Process all README files in the source directory and save the summaries in the target directory.
    """
    summaries = {}

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    csv_file_path = os.path.join(target_dir, 'readme_summaries.csv')
    
    for filename in os.listdir(src_dir):
        if filename.lower().endswith("_readme.md"):
            file_path = os.path.join(src_dir, filename)
            
            # Read the README file content
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            
            # Clean the README content
            clean_text = clean_readme(text)
            
            # Generate a summary
            summary = return_summary(clean_text)
            
            # Append results to dictionary
            owner, repo = filename.split('_README.md')[0].split('++')
            summaries[f'{owner}/{repo}'] = {
                'Summary': summary
            }
            print(f"Successfully summarized {owner}/{repo}")

    # Write results to CSV
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['full_name', 'Summary']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for full_name, data in summaries.items():
            writer.writerow({'full_name': full_name, 'Summary': data['Summary']})
    
    print(f"\nSummaries and file names saved in {csv_file_path}")


def filter_common_phrases(texts, num_common=100):
    """
    Identify and filter out the most common phrases from the list of texts.
    """
    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))  # Unigrams and bigrams
    X = vectorizer.fit_transform(texts)
    
    # Get feature names and their average tf-idf scores across all documents
    feature_names = vectorizer.get_feature_names_out()
    avg_scores = X.mean(axis=0).A1
    sorted_indices = avg_scores.argsort()[::-1]
    
    # Get the top common phrases
    common_phrases = [feature_names[i] for i in sorted_indices[:num_common]]
    
    return common_phrases

def clean_and_filter_readme(text, common_phrases):
    """
    Clean the README text and filter out common phrases.
    """
    # Clean text
    text = clean_readme(text)
    
    # Remove common phrases
    for phrase in common_phrases:
        text = re.sub(r'\b' + re.escape(phrase) + r'\b', '', text, flags=re.IGNORECASE)
    
    return text

def extract_topics_from_summaries(target_dir, num_topics=1, num_common=1):
    """
    Process each summary file in the target directory, filter common phrases, and extract topics.
    """
    csv_file_path = os.path.join(target_dir, 'readme_summaries.csv')
    df = pd.read_csv(csv_file_path)
    
    # Extract summaries
    summaries = df['Summary'].tolist()
    filenames = df['Filename'].tolist()
    
    # Identify common phrases
    common_phrases = filter_common_phrases(summaries, num_common=num_common)
    
    # Initialize TfidfVectorizer
    vectorizer = TfidfVectorizer(stop_words='english')
    
    # Prepare to save the results
    topics_results = []

    for filename, summary in zip(filenames, summaries):
        # Clean and filter the summary
        clean_summary = clean_and_filter_readme(summary, common_phrases)
        
        # Transform the summary into TF-IDF features
        X = vectorizer.fit_transform([clean_summary])
        
        # Initialize LDA
        lda = LatentDirichletAllocation(n_components=num_topics, random_state=0)
        lda.fit(X)
        
        # Get topics and words
        feature_names = vectorizer.get_feature_names_out()
        topics = lda.components_
        
        def display_topics(model, feature_names, no_top_words):
            topics_keywords = []
            for topic_idx, topic in enumerate(model.components_):
                topic_keywords = " ".join([feature_names[i] for i in topic.argsort()[:-no_top_words - 1:-1]])
                topics_keywords.append(topic_keywords)
            return topics_keywords
        
        # Get and save topics for this summary
        topics_keywords = display_topics(lda, feature_names, no_top_words=10)
        topics_results.append({
            'Filename': filename,
            'Topics': "; ".join(topics_keywords)
        })
    
    # Save the topics to a new CSV file
    topics_csv_path = os.path.join(target_dir, 'readme_topics.csv')
    df_topics = pd.DataFrame(topics_results)
    df_topics.to_csv(topics_csv_path, index=False, encoding='utf-8')
    
    print(f"Topics extracted and saved in {topics_csv_path}")


from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

def extract_key_phrases(text, num_phrases=5):
    """
    Extract key phrases from text using TF-IDF.
    """
    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))  # Unigrams and bigrams
    X = vectorizer.fit_transform([text])
    feature_names = vectorizer.get_feature_names_out()
    scores = X.sum(axis=0).A1
    sorted_indices = scores.argsort()[::-1]
    top_phrases = [feature_names[i] for i in sorted_indices[:num_phrases]]
    return top_phrases

def generate_repository_name(summary):
    """
    Generate a repository name based on the summary content.
    """
    key_phrases = extract_key_phrases(summary)
    name = " ".join(key_phrases).title()
    return name if name else "Repository"

def extract_topics_from_summaries(target_dir):
    """
    Assign names to each repository based on summaries.
    """
    csv_file_path = os.path.join(target_dir, 'readme_summaries.csv')
    df = pd.read_csv(csv_file_path)
    
    # Add a new column for repository names
    df['Repository Name'] = df['Summary'].apply(generate_repository_name)
    
    # Save the results to a new CSV file


    topics_csv_path = os.path.join(target_dir, 'readme_topics.csv')

    df.to_csv(topics_csv_path, index=False, encoding='utf-8')
    
    print(f"Topics extracted and saved in {topics_csv_path}")

