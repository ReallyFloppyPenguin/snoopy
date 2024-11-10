import os
from pathlib import Path
from collections import Counter
from typing import Dict, List, Set, Tuple
import json
import magic  # for file type detection
import time
from datetime import datetime
import pandas as pd
import hashlib
from concurrent.futures import ThreadPoolExecutor

class FileProfiler:
    """
    Analyzes local files to build a comprehensive user profile based on file patterns,
    types, and usage.
    """
    def __init__(self, 
                 scan_paths: List[str] = None,
                 excluded_dirs: Set[str] = None,
                 file_limit: int = 10000):
        """
        Initialize the File Profiler with configuration settings
        
        Args:
            scan_paths: List of directory paths to scan. Defaults to user's home directory
            excluded_dirs: Set of directory names to exclude (e.g., 'node_modules')
            file_limit: Maximum number of files to analyze
        """
        # Set default scan paths if none provided
        self.scan_paths = scan_paths or [str(Path.home())]
        
        # Default excluded directories
        self.excluded_dirs = excluded_dirs or {
            'node_modules', 'venv', '.git', 'AppData',
            'Cache', 'cache', 'tmp', 'temp'
        }
        
        # Load category mappings
        self.file_categories = {
            'development': {'.py', '.js', '.java', '.cpp', '.h', '.cs', '.php', '.rb'},
            'documents': {'.pdf', '.doc', '.docx', '.txt', '.md', '.csv', '.xlsx'},
            'media': {'.jpg', '.png', '.mp4', '.mp3', '.wav', '.avi', '.mov'},
            'design': {'.psd', '.ai', '.fig', '.sketch', '.xd'},
            'data_science': {'.ipynb', '.r', '.mat', '.json', '.yaml'},
        }
        
        self.file_limit = file_limit
        self.mime_magic = magic.Magic(mime=True)

    def scan_files(self) -> pd.DataFrame:
        """
        Scan filesystem and collect file metadata
        
        Returns:
            pd.DataFrame: DataFrame containing file metadata
        """
        files_data = []
        processed_count = 0
        
        def process_file(file_path: Path) -> Dict:
            """Process a single file and return its metadata"""
            try:
                stat = file_path.stat()
                return {
                    'path': str(file_path),
                    'name': file_path.name,
                    'extension': file_path.suffix.lower(),
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime),
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'accessed': datetime.fromtimestamp(stat.st_atime),
                    'mime_type': self.mime_magic.from_file(str(file_path))
                }
            except Exception as e:
                return None

        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=4) as executor:
            for root_path in self.scan_paths:
                for root, dirs, files in os.walk(root_path):
                    # Skip excluded directories
                    dirs[:] = [d for d in dirs if d not in self.excluded_dirs]
                    
                    # Process files in parallel
                    file_paths = [Path(root) / f for f in files]
                    results = executor.map(process_file, file_paths)
                    
                    # Add valid results to our dataset
                    for result in results:
                        if result:
                            files_data.append(result)
                            processed_count += 1
                            
                        if processed_count >= self.file_limit:
                            break
                    
                    if processed_count >= self.file_limit:
                        break
        
        return pd.DataFrame(files_data)

    def analyze_file_patterns(self, df: pd.DataFrame) -> Dict:
        """
        Analyze patterns in file usage and types
        
        Args:
            df: DataFrame containing file metadata
            
        Returns:
            Dict containing various file pattern analyses
        """
        # Initialize analysis dictionary
        analysis = {
            'extension_counts': Counter(df['extension'].value_counts().to_dict()),
            'category_distribution': {},
            'temporal_patterns': {
                'creation_hours': df['created'].dt.hour.value_counts().to_dict(),
                'modification_hours': df['modified'].dt.hour.value_counts().to_dict(),
                'weekly_activity': df['modified'].dt.day_name().value_counts().to_dict()
            },
            'size_metrics': {
                'total_size': df['size'].sum(),
                'average_size': df['size'].mean(),
                'largest_files': df.nlargest(5, 'size')[['name', 'size', 'path']].to_dict('records')
            }
        }
        
        # Calculate category distribution
        for category, extensions in self.file_categories.items():
            category_files = df[df['extension'].isin(extensions)]
            analysis['category_distribution'][category] = len(category_files)
        
        return analysis

    def determine_user_interests(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate interest scores based on file types and patterns
        
        Args:
            df: DataFrame containing file metadata
            
        Returns:
            Dict containing interest categories and their scores
        """
        # Initialize interest scores
        interest_scores = {category: 0 for category in self.file_categories.keys()}
        
        # Calculate total files for normalization
        total_files = len(df)
        
        # Calculate scores based on file categories
        for category, extensions in self.file_categories.items():
            category_count = len(df[df['extension'].isin(extensions)])
            interest_scores[category] = category_count / total_files if total_files > 0 else 0
            
        return interest_scores

    def generate_profile(self) -> Dict:
        """
        Generate comprehensive user profile based on file analysis
        
        Returns:
            Dict containing complete file-based user profile
        """
        # Scan files
        df = self.scan_files()
        if df.empty:
            return {"error": "No files found or accessible"}

        # Perform analyses
        file_patterns = self.analyze_file_patterns(df)
        interests = self.determine_user_interests(df)

        # Generate insights
        insights = self._generate_insights(file_patterns, interests)

        return {
            'file_patterns': file_patterns,
            'interests': interests,
            'insights': insights,
            'summary': {
                'total_files_analyzed': len(df),
                'total_size_gb': file_patterns['size_metrics']['total_size'] / (1024**3),
                'date_range': {
                    'oldest_file': df['created'].min(),
                    'newest_file': df['created'].max()
                }
            }
        }

    def _generate_insights(self, patterns: Dict, interests: Dict) -> Dict:
        """
        Generate insights based on file patterns and interests
        
        Args:
            patterns: File pattern analysis
            interests: Interest analysis
            
        Returns:
            Dict containing various insights about the user
        """
        insights = {
            'primary_activities': [],
            'work_habits': [],
            'storage_habits': []
        }

        # Determine primary activities
        for category, score in interests.items():
            if score > 0.2:  # 20% threshold
                insights['primary_activities'].append(f"Active {category} user")

        # Analyze work habits
        hour_counts = patterns['temporal_patterns']['modification_hours']
        if max(hour_counts.values()) > len(hour_counts) * 0.3:
            peak_hour = max(hour_counts.items(), key=lambda x: x[1])[0]
            if 5 <= peak_hour <= 11:
                insights['work_habits'].append("Morning person")
            elif 20 <= peak_hour <= 23 or 0 <= peak_hour <= 4:
                insights['work_habits'].append("Night owl")

        # Analyze storage habits
        avg_size = patterns['size_metrics']['average_size']
        if avg_size > 100 * 1024**2:  # 100MB
            insights['storage_habits'].append("Handles large files frequently")
        
        return insights 