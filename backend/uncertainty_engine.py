from openai import OpenAI

class UncertaintyEngine:
    def __init__(self):
        # Initialize things that stay the same across ALL questions
        self.llm = ...        # Your LLM
        self.scorer = ConfidenceScorer()
        # DON'T initialize question, source_type, days, clarity, ans here
    
    def query(self, question):
        # Main method: orchestrates everything
        # Takes question → returns answer + confidence
        pass
    
    def search(self, question):
        # Search the web for answer
        pass
    
    def extract_metadata(self, search_result):
        # Ask LLM to extract source_type, days_old, clarity
        pass
    
    def get_confidence_score(self, source_type, days_old, clarity):
        # Use ConfidenceScorer to calculate
        pass