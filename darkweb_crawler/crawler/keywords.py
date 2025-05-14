import csv
import os
import re
from fuzzywuzzy import fuzz, process
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import pandas as pd
from pathlib import Path

class KeywordDetector:
    def __init__(self, keywords_file=None):
        """Initialize keyword detector with an optional CSV file"""
        self.keywords = {}  # Category -> list of keywords
        self.threshold = 80  # Default fuzzy matching threshold
        
        # Download required NLTK data (if not already downloaded)
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            print("📚 Downloading NLTK data (first-time setup)...")
            nltk.download('punkt', quiet=True)
            
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords', quiet=True)
            
        self.stop_words = set(stopwords.words('english'))
        
        # If a keywords file is provided, load it
        if keywords_file:
            self.load_keywords(keywords_file)
            
    def load_keywords(self, file_path):
        """Load keywords from a CSV file
        
        Expected format:
        keyword,category
        drug,Drugs
        weapon,Weapons
        """
        if not os.path.exists(file_path):
            print(f"⚠️ Keyword file not found: {file_path}")
            return False
            
        try:
            df = pd.read_csv(file_path)
            
            # Simple case: CSV has 'keyword' and 'category' columns
            if 'keyword' in df.columns and 'category' in df.columns:
                for _, row in df.iterrows():
                    category = row['category']
                    keyword = str(row['keyword']).lower()
                    
                    if category not in self.keywords:
                        self.keywords[category] = []
                        
                    self.keywords[category].append(keyword)
                    
            # Alternative format: Each category is a column, keywords in rows
            else:
                for col in df.columns:
                    self.keywords[col] = []
                    for keyword in df[col].dropna():
                        self.keywords[col].append(str(keyword).lower())
                        
            print(f"✅ Loaded {sum(len(keywords) for keywords in self.keywords.values())} keywords in {len(self.keywords)} categories")
            return True
            
        except Exception as e:
            print(f"❌ Error loading keywords: {str(e)}")
            return False
    
    def detect_keywords(self, text, return_matches=False):
        """Detect keywords in text and return matching categories
        
        Args:
            text: The text to analyze
            return_matches: If True, return dict of matches, otherwise just categories
            
        Returns:
            dict: Category -> confidence score (0-100)
            or dict: Category -> list of (keyword, score, context) if return_matches=True
        """
        if not self.keywords:
            return {}
            
        # Normalize and clean text
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)  # Replace punctuation with spaces
        
        # Tokenize text into sentences for context
        sentences = sent_tokenize(text)
        
        # Process each category
        results = {}
        matches = {}
        
        for category, keywords in self.keywords.items():
            category_score = 0
            category_matches = []
            
            for keyword in keywords:
                # Simple exact match (fastest)
                if keyword in text:
                    # Find best sentence context
                    best_context = self._find_best_context(keyword, sentences)
                    category_matches.append((keyword, 100, best_context))
                    category_score = max(category_score, 100)
                    continue
                    
                # Check for fuzzy matches
                best_match, score = self._best_fuzzy_match(keyword, text)
                if score >= self.threshold:
                    best_context = self._find_best_context(best_match, sentences)
                    category_matches.append((keyword, score, best_context))
                    category_score = max(category_score, score)
            
            if category_matches:
                matches[category] = category_matches
                results[category] = category_score
        
        if return_matches:
            return matches
        return results
    
    def _best_fuzzy_match(self, keyword, text):
        """Find best fuzzy match of keyword in text"""
        # Split text into overlapping chunks
        chunks = self._get_overlapping_chunks(text, 100, 50)
        
        best_score = 0
        best_match = ""
        
        for chunk in chunks:
            # For multi-word keywords, use token set ratio
            if ' ' in keyword:
                score = fuzz.token_set_ratio(keyword, chunk)
            else:
                # For single words, partial ratio works better
                score = fuzz.partial_ratio(keyword, chunk)
                
            if score > best_score:
                best_score = score
                best_match = chunk
                
        return best_match, best_score
    
    def _get_overlapping_chunks(self, text, chunk_size=100, overlap=50):
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
            
        return chunks
    
    def _find_best_context(self, keyword, sentences, context_size=1):
        """Find best sentence context for a keyword match"""
        best_sentence = ""
        highest_score = 0
        
        for sentence in sentences:
            score = fuzz.partial_ratio(keyword, sentence.lower())
            if score > highest_score:
                highest_score = score
                best_sentence = sentence
        
        return best_sentence.strip()

    def get_categories(self):
        """Get list of all categories"""
        return list(self.keywords.keys()) 