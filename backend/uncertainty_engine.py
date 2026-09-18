from openai import OpenAI
from dotenv import load_dotenv
from duckduckgo_search import DDGS
from confidence_scorer import ConfidenceScorer
from datetime import datetime
import json

load_dotenv()

class UncertaintyEngine:
    def __init__(self, confidence_threshold=0.6):
        self.llm = OpenAI()
        self.scorer = ConfidenceScorer()
        self.confidence_threshold = confidence_threshold
    
    def search_question(self, question):
        """Search DuckDuckGo and return structured results"""
        try:
            results = DDGS().text(question, max_results=5)
            
            structured_results = []
            for result in results:
                structured_results.append({
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "content": result.get("body", ""),
                    "source_url": result.get("href", ""),
                    "fetched_at": datetime.now().isoformat()
                })
            
            return structured_results
        
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def _determine_source_type(self, url, title=""):
        """Use LLM to determine if source is official"""
        url_lower = url.lower()
        
        # Quick checks (fast path)
        if ".gov" in url_lower or ".edu" in url_lower:
            return "official_site"
        if "wikipedia" in url_lower:
            return "wikipedia"
        
        # Ask LLM for everything else
        try:
            response = self.llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": f"Is this source official/authoritative? URL: {url}\nTitle: {title}\nAnswer only: yes or no"
                }],
                temperature=0,
                max_tokens=10
            )
            
            answer = response.choices[0].message.content.strip().lower()
            return "official_site" if "yes" in answer else "blog"
        
        except Exception as e:
            print(f"LLM error: {e}")
            return "unknown"
    
    def extract_metadata(self, search_result):
        """Extract source_type, days_old, statement_clarity from search result"""
        try:
            url = search_result.get("source_url", "")
            title = search_result.get("title", "")
            content = search_result.get("content", "")
            
            # Determine source type
            source_type = self._determine_source_type(url, title)
            
            # Estimate days_old (heuristic approach)
            # For now: news sources = 1 day, blogs = 7 days, rest = 30 days
            if "news" in url.lower() or any(x in url.lower() for x in ["bbc", "cnn", "reuters"]):
                days_old = 1
            elif "blog" in source_type.lower():
                days_old = 7
            else:
                days_old = 30
            
            # Estimate statement clarity
            # Ask LLM: is this statement exact, approximate, or uncertain?
            response = self.llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": f"Rate this statement's clarity:\n'{content}'\nAnswer only one word: exact, approximate, or uncertain"
                }],
                temperature=0,
                max_tokens=5
            )
            
            clarity = response.choices[0].message.content.strip().lower()
            if clarity not in ["exact", "approximate", "uncertain"]:
                clarity = "approximate"  # default
            
            return {
                "source_type": source_type,
                "days_old": days_old,
                "statement_clarity": clarity,
                "url": url,
                "title": title
            }
        
        except Exception as e:
            print(f"Metadata extraction error: {e}")
            return {
                "source_type": "unknown",
                "days_old": 30,
                "statement_clarity": "uncertain",
                "url": search_result.get("source_url", ""),
                "title": search_result.get("title", "")
            }
    
    def calculate_confidence_score(self, source_type, days_old, clarity):
        """Calculate confidence using ConfidenceScorer"""
        return self.scorer.calculate_confidence(source_type, days_old, clarity)
    
    def query(self, question):
        """Main orchestration: search → extract → score → return answer"""
        
        # Step 1: Search
        search_results = self.search_question(question)
        
        if not search_results:
            return {
                "answer": "No sources found",
                "confidence": 0.0,
                "sources": [],
                "reasoning": "Search returned no results"
            }
        
        # Step 2: Extract metadata and score each result
        scored_results = []
        for result in search_results:
            metadata = self.extract_metadata(result)
            confidence = self.calculate_confidence_score(
                metadata["source_type"],
                metadata["days_old"],
                metadata["statement_clarity"]
            )
            
            scored_results.append({
                "content": result.get("content", ""),
                "title": result.get("title", ""),
                "url": result.get("source_url", ""),
                "confidence": confidence,
                "metadata": metadata,
                "breakdown": self.scorer.get_confidence_breakdown(
                    metadata["source_type"],
                    metadata["days_old"],
                    metadata["statement_clarity"]
                )
            })
        
        # Step 3: Find best result
        best_result = max(scored_results, key=lambda x: x["confidence"])
        
        # Step 4: Decide — answer or refuse based on threshold
        if best_result["confidence"] >= self.confidence_threshold:
            decision = "ANSWER"
        else:
            decision = "LOW_CONFIDENCE"
        
        return {
            "question": question,
            "answer": best_result["content"],
            "confidence": best_result["confidence"],
            "decision": decision,
            "sources": [
                {"url": r["url"], "title": r["title"], "confidence": r["confidence"]}
                for r in scored_results
            ],
            "best_result_breakdown": best_result["breakdown"]
        }