import re
import json
import os
from pathlib import Path
from collections import defaultdict
from .keywords import KeywordDetector

class CategoryClassifier:
    """Classifies dark web content into categories"""
    
    CATEGORIES = {
        "Drugs": {
            "severity": 3,
            "indicators": [
                r"\b(?:mdma|cocaine|heroin|lsd|meth|marijuana|cannabis|pills|opioids)\b",
                r"\b(?:pharmacy|drug|narcotic|substance|psychedelic|stimulant)\b"
            ]
        },
        "Weapons": {
            "severity": 4,
            "indicators": [
                r"\b(?:gun|rifle|pistol|ammunition|firearms|weapons|knives)\b",
                r"\b(?:assault|tactical|military|combat|explosive)\b"
            ]
        },
        "Fake_IDs": {
            "severity": 3,
            "indicators": [
                r"\b(?:passport|license|identity|document|certificate|SSN|forgery)\b",
                r"\b(?:fake|forged|counterfeit|false|falsified)\b"
            ]
        },
        "Hacking": {
            "severity": 3,
            "indicators": [
                r"\b(?:hack|crack|exploit|vulnerability|malware|trojan|botnet|virus)\b",
                r"\b(?:password|access|breach|backdoor|script|tool|rootkit)\b"
            ]
        },
        "Financial_Fraud": {
            "severity": 3,
            "indicators": [
                r"\b(?:credit\s*card|bank\s*account|paypal|bitcoin|crypto|wallet|transfer)\b",
                r"\b(?:carding|skimming|cloning|dump|fullz|cvv|fraud)\b"
            ]
        },
        "Human_Trafficking": {
            "severity": 5,
            "indicators": [
                r"\b(?:escort|service|massage|girl|boy|young|teen)\b",
                r"\b(?:trafficking|exploitation|abuse|child|minor)\b"
            ]
        }
    }
    
    def __init__(self, custom_categories_file=None, keywords_detector=None):
        """Initialize category classifier
        
        Args:
            custom_categories_file: Path to custom categories JSON file
            keywords_detector: Optional KeywordDetector instance
        """
        self.categories = self.CATEGORIES.copy()
        
        # Override with custom categories if provided
        if custom_categories_file and os.path.exists(custom_categories_file):
            self._load_custom_categories(custom_categories_file)
            
        # Set up keyword detector
        self.keyword_detector = keywords_detector
        
        # Optional toggle-able categories
        self.enabled_categories = set(self.categories.keys())
        
        print(f"🧠 Classifier initialized with {len(self.categories)} categories")
        
    def _load_custom_categories(self, file_path):
        """Load custom categories from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                custom_categories = json.load(f)
                
            for category, data in custom_categories.items():
                # Make sure category has proper format
                if isinstance(data, dict) and "indicators" in data:
                    # Update existing or add new category
                    self.categories[category] = data
                    
            print(f"✅ Loaded custom categories from {file_path}")
        except Exception as e:
            print(f"❌ Error loading custom categories: {str(e)}")
    
    def enable_category(self, category):
        """Enable a specific category"""
        if category in self.categories:
            self.enabled_categories.add(category)
            return True
        return False
        
    def disable_category(self, category):
        """Disable a specific category"""
        if category in self.enabled_categories:
            self.enabled_categories.remove(category)
            return True
        return False
        
    def get_category_list(self):
        """Get list of all categories with enabled status"""
        return {
            category: {
                "enabled": category in self.enabled_categories,
                "severity": data.get("severity", 1)
            }
            for category, data in self.categories.items()
        }
    
    def classify_content(self, text, url="", html=""):
        """Classify content into categories
        
        Args:
            text: Plain text content to analyze
            url: URL of the content (for additional context)
            html: Optional HTML content for more detailed analysis
            
        Returns:
            dict: Category matches with severity and evidence
        """
        results = {}
        
        # Only check enabled categories
        for category in self.enabled_categories:
            if category not in self.categories:
                continue
                
            category_data = self.categories[category]
            indicators = category_data.get("indicators", [])
            severity = category_data.get("severity", 1)
            
            # Check for indicator patterns
            matches = []
            for pattern in indicators:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    # Get surrounding context
                    start = max(0, match.start() - 40)
                    end = min(len(text), match.end() + 40)
                    context = text[start:end].strip()
                    
                    matches.append({
                        "pattern": pattern,
                        "matched_text": match.group(0),
                        "context": context
                    })
            
            # Also check URL for obvious indicators
            url_matches = []
            for pattern in indicators:
                if re.search(pattern, url, re.IGNORECASE):
                    url_matches.append({
                        "pattern": pattern,
                        "matched_text": url
                    })
            
            # If we found matches, add to results
            if matches or url_matches:
                confidence = min(len(matches) + len(url_matches) * 2, 10) * 10  # Scale to 0-100
                results[category] = {
                    "severity": severity,
                    "confidence": confidence,
                    "matches": matches,
                    "url_matches": url_matches
                }
        
        # Also use keyword detector if available
        if self.keyword_detector:
            keyword_matches = self.keyword_detector.detect_keywords(text, return_matches=True)
            
            for category, matches in keyword_matches.items():
                # Skip categories that are disabled
                if category not in self.enabled_categories:
                    continue
                    
                # Calculate confidence based on match quality
                match_scores = [score for _, score, _ in matches]
                avg_confidence = sum(match_scores) / len(match_scores) if match_scores else 0
                
                # Convert keyword matches to our format
                formatted_matches = []
                for keyword, score, context in matches:
                    formatted_matches.append({
                        "pattern": f"keyword:{keyword}",
                        "matched_text": keyword,
                        "context": context,
                        "score": score
                    })
                
                # If category already exists in results, merge
                if category in results:
                    results[category]["matches"].extend(formatted_matches)
                    results[category]["confidence"] = max(
                        results[category]["confidence"],
                        avg_confidence
                    )
                else:
                    # Get severity from our categories if it exists
                    severity = self.categories.get(category, {}).get("severity", 2)
                    
                    results[category] = {
                        "severity": severity,
                        "confidence": avg_confidence,
                        "matches": formatted_matches,
                        "url_matches": []
                    }
        
        return results 