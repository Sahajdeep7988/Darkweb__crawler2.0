#!/usr/bin/env python3
"""
Unit tests for Dark Web Crawler components
"""

import unittest
import os
import json
import tempfile
import csv
from unittest.mock import patch
from crawler.keywords import KeywordDetector
from crawler.classifier import CategoryClassifier
from crawler.alerting import AlertLogger

class TestKeywordDetector(unittest.TestCase):
    """Test KeywordDetector functionality"""
    
    def setUp(self):
        # Create a temp CSV file for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.csv_path = os.path.join(self.temp_dir.name, "test_keywords.csv")
        
        with open(self.csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["keyword", "category"])
            writer.writerow(["test", "Test"])
            writer.writerow(["example", "Test"])
            writer.writerow(["sample", "Sample"])
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_load_keywords(self):
        """Test loading keywords from CSV"""
        detector = KeywordDetector()
        
        # Load keywords
        success = detector.load_keywords(self.csv_path)
        self.assertTrue(success)
        
        # Check categories
        categories = detector.get_categories()
        self.assertEqual(len(categories), 2)
        self.assertIn("Test", categories)
        self.assertIn("Sample", categories)
        
        # Check keywords
        self.assertEqual(len(detector.keywords["Test"]), 2)
        self.assertEqual(len(detector.keywords["Sample"]), 1)
        
    @patch('crawler.keywords.sent_tokenize')
    @patch('crawler.keywords.KeywordDetector._best_fuzzy_match')
    @patch('crawler.keywords.KeywordDetector._find_best_context')
    def test_detect_keywords(self, mock_find_context, mock_fuzzy_match, mock_sent_tokenize):
        """Test keyword detection with mocked dependencies"""
        # Set up mocks
        mock_sent_tokenize.return_value = ["This is a test document with example keyword."]
        mock_fuzzy_match.return_value = ("test", 95)
        mock_find_context.return_value = "This is a test document with example keyword."
        
        # Create detector
        detector = KeywordDetector(self.csv_path)
        
        # Test exact match
        text = "This is a test document with example keyword."
        results = detector.detect_keywords(text)
        
        # Since "test" is in the keywords, we should match it
        self.assertIn("Test", results)
        
        # Verify mock called
        mock_sent_tokenize.assert_called_once()

class TestCategoryClassifier(unittest.TestCase):
    """Test CategoryClassifier functionality"""
    
    def setUp(self):
        self.classifier = CategoryClassifier()
    
    def test_category_list(self):
        """Test getting category list"""
        categories = self.classifier.get_category_list()
        self.assertIsInstance(categories, dict)
        self.assertIn("Drugs", categories)
        self.assertIn("Weapons", categories)
        
    def test_classify_content(self):
        """Test content classification"""
        # Drug content
        drug_text = "Looking for premium cocaine and marijuana products. Best quality MDMA and pharmaceutical grade pills."
        results = self.classifier.classify_content(drug_text)
        self.assertIn("Drugs", results)
        
        # Weapons content
        weapon_text = "Military grade assault rifles and pistols for sale. High quality ammunition and tactical gear."
        results = self.classifier.classify_content(weapon_text)
        self.assertIn("Weapons", results)
        
        # Mixed content
        mixed_text = "We offer fake passports and IDs along with credit card dumps and CVV codes."
        results = self.classifier.classify_content(mixed_text)
        self.assertIn("Fake_IDs", results)
        self.assertIn("Financial_Fraud", results)
        
    def test_toggle_categories(self):
        """Test enabling/disabling categories"""
        # Disable Drugs category
        self.classifier.disable_category("Drugs")
        
        # Check it's disabled
        categories = self.classifier.get_category_list()
        self.assertFalse(categories["Drugs"]["enabled"])
        
        # Drug text shouldn't match now
        drug_text = "Premium cocaine and marijuana for sale"
        results = self.classifier.classify_content(drug_text)
        self.assertNotIn("Drugs", results)
        
        # Re-enable it
        self.classifier.enable_category("Drugs")
        
        # Check it's enabled
        categories = self.classifier.get_category_list()
        self.assertTrue(categories["Drugs"]["enabled"])
        
class TestAlertLogger(unittest.TestCase):
    """Test AlertLogger functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.alert_logger = AlertLogger(log_dir=self.temp_dir.name)
    
    def tearDown(self):
        # Close the logger to release file handles before cleanup
        self.alert_logger.close()
        self.temp_dir.cleanup()
    
    def test_log_alert(self):
        """Test logging alerts"""
        # Log an alert
        alert = self.alert_logger.log_alert(
            url="http://test.onion",
            category="Drugs",
            severity=3,
            snippet="Test drugs content"
        )
        
        self.assertIsInstance(alert, dict)
        self.assertEqual(alert["url"], "http://test.onion")
        self.assertEqual(alert["category"], "Drugs")
        self.assertEqual(alert["severity"], 3)
        
        # Check it was saved
        self.assertEqual(len(self.alert_logger.alerts), 1)
        
        # Check alerts file exists
        alert_files = [f for f in os.listdir(self.temp_dir.name) if f.endswith(".json")]
        self.assertGreater(len(alert_files), 0)
        
    def test_get_alerts(self):
        """Test retrieving alerts"""
        # Log multiple alerts
        self.alert_logger.log_alert(
            url="http://test1.onion",
            category="Drugs",
            severity=2,
            snippet="Test drugs content"
        )
        self.alert_logger.log_alert(
            url="http://test2.onion",
            category="Weapons",
            severity=4,
            snippet="Test weapons content"
        )
        self.alert_logger.log_alert(
            url="http://test3.onion",
            category="Drugs",
            severity=3,
            snippet="More drugs content"
        )
        
        # Get all alerts
        all_alerts = self.alert_logger.get_alerts()
        self.assertEqual(len(all_alerts), 3)
        
        # Filter by category
        drug_alerts = self.alert_logger.get_alerts(category="Drugs")
        self.assertEqual(len(drug_alerts), 2)
        
        # Filter by severity
        high_alerts = self.alert_logger.get_alerts(min_severity=3)
        self.assertEqual(len(high_alerts), 2)
        
    def test_get_alert_stats(self):
        """Test getting alert statistics"""
        # Log multiple alerts
        self.alert_logger.log_alert(
            url="http://test1.onion",
            category="Drugs",
            severity=2,
            snippet="Test drugs content"
        )
        self.alert_logger.log_alert(
            url="http://test2.onion",
            category="Weapons",
            severity=4,
            snippet="Test weapons content"
        )
        self.alert_logger.log_alert(
            url="http://test3.onion",
            category="Drugs",
            severity=3,
            snippet="More drugs content"
        )
        
        # Get stats
        stats = self.alert_logger.get_alert_stats()
        
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["categories"]["Drugs"], 2)
        self.assertEqual(stats["categories"]["Weapons"], 1)
        self.assertEqual(stats["severity_levels"][2], 1)
        self.assertEqual(stats["severity_levels"][3], 1)
        self.assertEqual(stats["severity_levels"][4], 1)

if __name__ == "__main__":
    unittest.main() 