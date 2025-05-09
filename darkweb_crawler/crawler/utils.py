import logging

def setup_logging():
    """Basic logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('outputs/logs/crawler.log'),
            logging.StreamHandler()
        ] 
    )