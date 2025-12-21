import re

class QueryParser:
    def __init__(self):
        # ORDER MATTERS: Specific patterns first!
        self.patterns = [
             # 1. RANKING (General "Best" or "Who to draft")
            ("ranking", [
                r"who (should|do) i draft",  # Explicit "Who should I draft"
                r"who (are|is) (the )?best", 
                r"top (\d+)?", 
                r"leaders", 
                r"rank", 
                r"which .* (are|is) best"
            ]),
            # 2. COMPARE (Specific "X vs Y")
            ("compare", [
                r"compare", 
                r" vs ", 
                r" or ", 
                r"better", 
                r"draft .* (or|vs)" # Only match "draft" if "or/vs" is present
            ]),
            # 3. SEARCH (Single player lookup)
            ("search", [
                r"who is", 
                r"tell me about", 
                r"show me", 
                r"stats for"
            ])
        ]
        
        # Metric Mapping
        self.metric_map = {
            "deep ball": "passing_yards", 
            "passing": "passing_yards",
            "rushing": "rushing_yards",
            "receiving": "receiving_yards",
            "fantasy": "fantasy_points",
            "scoring": "touchdowns"
        }

        # Stop words to clean out of names
        self.stop_words = ["who", "is", "the", "best", "compare", "draft", "or", "vs", "tell", "me", "about", "stats", "for", "should", "i", "\\?", "top", "rank", "and"]

    def parse(self, text):
        text = text.lower().strip()
        
        # 1. Detect Intent
        intent = "unknown"
        for key, regex_list in self.patterns:
            for pattern in regex_list:
                if re.search(pattern, text):
                    intent = key
                    break
            if intent != "unknown": break
            
        # 2. Extract Entities
        params = {
            "metric": "fantasy_points", 
            "position": None,
            "limit": 5,
            "player_names": []
        }
        
        # Detect Position
        if "qb" in text or "quarterback" in text: params["position"] = "QB"
        elif "rb" in text or "running" in text: params["position"] = "RB"
        elif "wr" in text or "receiver" in text: params["position"] = "WR"
        elif "te" in text or "tight" in text: params["position"] = "TE"
        
        # Detect Metric
        for key, val in self.metric_map.items():
            if key in text:
                params["metric"] = val
                break
                
        # 3. SMART NAME EXTRACTION (The Fix for Adoree Jackson)
        # We split FIRST, then clean. This keeps first/last names together.
        potential_names = []
        delimiter = None
        
        if " or " in text: delimiter = " or "
        elif " vs " in text: delimiter = " vs "
        elif " and " in text: delimiter = " and "
        
        if delimiter:
            chunks = text.split(delimiter)
            for chunk in chunks:
                cleaned = self.clean_chunk(chunk)
                if len(cleaned) > 1:
                    potential_names.append(cleaned)
        else:
            # If no delimiter, clean the whole text
            cleaned = self.clean_chunk(text)
            if len(cleaned) > 1:
                potential_names.append(cleaned)

        params["player_names"] = potential_names
        return intent, params

    def clean_chunk(self, text):
        """Removes stop words from a specific string chunk."""
        for word in self.stop_words:
            # \b matches word boundaries to protect parts of names
            text = re.sub(r'\b' + word + r'\b', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()