from browser_snoop import UserProfiler
from file_snoop import FileProfiler
import json
from typing import Dict

def generate_complete_profile():
    """Generate a comprehensive user profile combining browser and file analysis"""
    
    # Initialize profilers
    browser_profiler = UserProfiler(history_limit=500)
    file_profiler = FileProfiler(file_limit=100)
    
    # Generate profiles
    browser_profile = browser_profiler.generate_user_profile()
    file_profile = file_profiler.generate_profile()
    
    # Combine insights
    combined_profile = {
        'browser_activity': browser_profile,
        'file_activity': file_profile,
        'combined_insights': {
            'interests': _merge_interests(
                browser_profile.get('interests', {}),
                file_profile.get('interests', {})
            ),
            'user_patterns': _analyze_combined_patterns(
                browser_profile,
                file_profile
            )
        }
    }
    
    return combined_profile

def _merge_interests(browser_interests: Dict, file_interests: Dict) -> Dict:
    """Merge and normalize interests from both sources"""
    all_interests = set(browser_interests.keys()) | set(file_interests.keys())
    merged = {}
    
    for interest in all_interests:
        browser_score = browser_interests.get(interest, 0)
        file_score = file_interests.get(interest, 0)
        # Weight browser activity slightly higher (60/40 split)
        merged[interest] = (browser_score * 0.6 + file_score * 0.4)
    
    return merged

def _analyze_combined_patterns(browser_profile: Dict, file_profile: Dict) -> Dict:
    """Analyze patterns across both browser and file activity"""
    return {
        'activity_times': {
            'browser': browser_profile.get('time_patterns', {}).get('peak_hours', {}),
            'file_activity': file_profile.get('file_patterns', {})
                .get('temporal_patterns', {}).get('modification_hours', {})
        },
        'primary_categories': {
            'browser': [k for k, v in browser_profile.get('interests', {}).items() if v > 0.2],
            'files': [k for k, v in file_profile.get('interests', {}).items() if v > 0.2]
        }
    }

if __name__ == "__main__":
    profile = generate_complete_profile()
    
    # Save profile to JSON file
    with open('user_profile.json', 'w') as f:
        json.dump(profile, f, indent=2, default=str)
    
    print("Profile generated successfully!")
    print("\nTop Combined Interests:")
    for interest, score in sorted(
        profile['combined_insights']['interests'].items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]:
        print(f"- {interest}: {score:.2%}")