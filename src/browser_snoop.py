import browser_history
import pandas as pd
from collections import Counter
from urllib.parse import urlparse
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import re
from typing import Dict, List, Tuple
import json

class UserProfiler:
    def __init__(self, history_limit: int = 500):
        """
        Initialize the User Profiler with necessary NLTK downloads and category mappings
        """
        # Download required NLTK data
        try:
            nltk.download("punkt", quiet=True)
            nltk.download("punkt_tab", quiet=True)
            nltk.download("stopwords", quiet=True)
        except Exception as e:
            print(f"Warning: NLTK download failed: {e}")

        # Define interest categories and their associated keywords
        self.interest_categories = json.load(open("snoopy.json"))["browser"]["categories"]

        # Time patterns for user behavior analysis
        self.time_patterns = {
            "early_bird": (5, 9),  # 5 AM - 9 AM
            "night_owl": (22, 4),  # 10 PM - 4 AM
            "work_hours": (9, 17),  # 9 AM - 5 PM
        }
        self.history_limit = history_limit

    def get_browser_tabs(self) -> pd.DataFrame:
        """
        Fetch recent browser history and convert to DataFrame
        
        Args:
            limit (int): Number of recent entries to fetch
            
        Returns:
            pd.DataFrame: DataFrame containing browser history
        """
        try:
            # Get browser history
            outputs = browser_history.get_history()
            history = outputs.histories
            
            # Create DataFrame and handle different column formats
            if len(history) > 0:
                if len(history[0]) == 3:  # If history has 3 columns
                    df = pd.DataFrame(history, columns=['timestamp', 'url', 'title'])
                else:  # Default to 2 columns
                    df = pd.DataFrame(history, columns=['timestamp', 'url'])
            else:
                return pd.DataFrame()  # Return empty DataFrame if no history
                
            # Add additional analyzed columns
            df['domain'] = df['url'].apply(lambda x: urlparse(x).netloc)
            df['hour'] = df['timestamp'].apply(lambda x: x.hour)
            df['day_of_week'] = df['timestamp'].apply(lambda x: x.strftime('%A'))
            
            # Sort and limit results
            return df.sort_values('timestamp', ascending=False).head(self.history_limit)
            
        except Exception as e:
            print(f"Error fetching browser history: {e}")
            print("Detailed error info:")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    def analyze_content_patterns(self, df: pd.DataFrame) -> Dict:
        """
        Analyze content patterns in URLs and domains
        
        Args:
            df (pd.DataFrame): Browser history DataFrame
            
        Returns:
            Dict: Analysis of content patterns
        """
        # Extract words from URLs
        words = []
        for url in df['url']:
            # Clean and tokenize URL
            clean_url = re.sub(r'[^\w\s]', ' ', url.lower())
            words.extend(word_tokenize(clean_url))
        
        # Remove stopwords and common URL terms
        stop_words = set(stopwords.words('english'))
        url_common_terms = {'com', 'www', 'http', 'https', 'org', 'net'}
        filtered_words = [word for word in words 
                         if word not in stop_words 
                         and word not in url_common_terms
                         and len(word) > 2]
        
        return {
            'common_terms': Counter(filtered_words).most_common(20),
            'domain_frequency': Counter(df['domain']).most_common(10)
        }

    def determine_interests(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate interest scores based on URL content
        
        Args:
            df (pd.DataFrame): Browser history DataFrame
            
        Returns:
            Dict[str, float]: Interest categories and their scores
        """
        # Initialize scores
        interest_scores = {category: 0 for category in self.interest_categories}
        
        # Analyze each URL
        for url in df['url']:
            url_lower = url.lower()
            for category, keywords in self.interest_categories.items():
                if any(keyword in url_lower for keyword in keywords):
                    interest_scores[category] += 1
        
        # Normalize scores
        total_matches = sum(interest_scores.values())
        if total_matches > 0:
            interest_scores = {k: v/total_matches for k, v in interest_scores.items()}
        
        return interest_scores

    def analyze_time_patterns(self, df: pd.DataFrame) -> Dict:
        """
        Analyze temporal patterns in browsing behavior
        
        Args:
            df (pd.DataFrame): Browser history DataFrame
            
        Returns:
            Dict: Analysis of temporal patterns
        """
        time_analysis = {
            'peak_hours': df['hour'].value_counts().head(3).to_dict(),
            'day_distribution': df['day_of_week'].value_counts().to_dict(),
            'user_type': []
        }
        
        # Determine user type based on activity patterns
        hour_counts = df['hour'].value_counts()
        
        if hour_counts.between(self.time_patterns['early_bird'][0], 
                             self.time_patterns['early_bird'][1]).sum() > len(df) * 0.3:
            time_analysis['user_type'].append('Early Bird')
            
        if hour_counts.between(self.time_patterns['night_owl'][0], 
                             self.time_patterns['night_owl'][1]).sum() > len(df) * 0.3:
            time_analysis['user_type'].append('Night Owl')
            
        return time_analysis

    def generate_user_profile(self) -> Dict:
        """
        Generate comprehensive user profile based on browser history
        
        Returns:
            Dict: Complete user profile analysis
        """
        # Get browser history
        df = self.get_browser_tabs()
        if df.empty:
            return {"error": "No browser history available"}

        # Perform various analyses
        content_patterns = self.analyze_content_patterns(df)
        interests = self.determine_interests(df)
        time_patterns = self.analyze_time_patterns(df)

        # Create personality insights based on patterns
        personality_insights = self._generate_personality_insights(
            interests, time_patterns, content_patterns
        )

        return {
            'interests': interests,
            'time_patterns': time_patterns,
            'content_patterns': content_patterns,
            'personality_insights': personality_insights,
            'data_summary': {
                'total_urls_analyzed': len(df),
                'date_range': {
                    'start': df['timestamp'].min(),
                    'end': df['timestamp'].max()
                }
            }
        }

    def _generate_personality_insights(self, interests: Dict, 
                                     time_patterns: Dict, 
                                     content_patterns: Dict) -> Dict:
        """
        Generate personality insights based on browsing patterns
        
        Args:
            interests (Dict): Interest analysis
            time_patterns (Dict): Temporal pattern analysis
            content_patterns (Dict): Content pattern analysis
            
        Returns:
            Dict: Personality insights
        """
        insights = {
            'traits': [],
            'learning_style': [],
            'work_style': []
        }

        # Analyze traits based on interests
        if interests.get('technology', 0) > 0.3:
            insights['traits'].append('Technically Inclined')
        if interests.get('academic', 0) > 0.2:
            insights['traits'].append('Intellectual Curious')
        if interests.get('entertainment', 0) > 0.3:
            insights['traits'].append('Entertainment-Focused')

        # Analyze work/study style
        if 'Early Bird' in time_patterns.get('user_type', []):
            insights['work_style'].append('Morning Productive')
        if 'Night Owl' in time_patterns.get('user_type', []):
            insights['work_style'].append('Night Productive')

        return insights

# Example usage
def main():
    profiler = UserProfiler(history_limit=500)
    profile = profiler.generate_user_profile()
    
    print("\n=== User Profile Analysis ===")
    print("\nTop Interests:")
    for category, score in sorted(profile['interests'].items(), key=lambda x: x[1], reverse=True):
        if score > 0:
            print(f"- {category}: {score:.2%}")
    
    print("\nBrowsing Patterns:")
    print(f"Most active times: {profile['time_patterns']['peak_hours']}")
    print(f"User type: {', '.join(profile['time_patterns']['user_type'])}")
    
    print("\nPersonality Insights:")
    for category, traits in profile['personality_insights'].items():
        if traits:
            print(f"- {category}: {', '.join(traits)}")

if __name__ == "__main__":
    main()