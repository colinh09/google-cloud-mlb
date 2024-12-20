import requests
import json
from typing import Dict, Any
import pandas as pd
from collections import defaultdict

def fetch_schedule(year: int) -> Dict[str, Any]:
    """Fetch MLB schedule for a given year and return first game_pk"""
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&season={year}&gameType=R"
    response = requests.get(url)
    data = response.json()
    
    # Get the first game_pk we find
    if 'dates' in data and len(data['dates']) > 0:
        games = data['dates'][0]['games']
        if len(games) > 0:
            return games[0]['gamePk']
    return None

def fetch_game_data(game_pk: int) -> Dict[str, Any]:
    """Fetch detailed game data for a given game_pk"""
    url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
    response = requests.get(url)
    return response.json()

def analyze_data_structure(data: Dict[str, Any], prefix: str = '') -> Dict[str, set]:
    """Recursively analyze the structure of nested JSON data
    Returns a dict mapping each path to the set of data types found there"""
    structure = defaultdict(set)
    
    def _recurse(d: Dict[str, Any], current_prefix: str):
        for k, v in d.items():
            path = f"{current_prefix}.{k}" if current_prefix else k
            
            if isinstance(v, dict):
                _recurse(v, path)
            elif isinstance(v, list) and v and isinstance(v[0], dict):
                _recurse(v[0], path)  # Analyze structure of first item in list
            else:
                structure[path].add(type(v).__name__)
    
    _recurse(data, prefix)
    return structure

def compare_eras():
    # Sample years from different eras
    years = {
        'Statcast': 2023,
        'PitchFX': 2010,
        'Pre-tracking': 2000
    }
    
    era_structures = {}
    
    for era, year in years.items():
        print(f"\nAnalyzing {era} era (year: {year})")
        
        # Get a game from this year
        game_pk = fetch_schedule(year)
        if not game_pk:
            print(f"No games found for {year}")
            continue
            
        print(f"Using game_pk: {game_pk}")
        
        # Fetch and analyze game data
        game_data = fetch_game_data(game_pk)
        structure = analyze_data_structure(game_data)
        era_structures[era] = structure
    
    # Compare structures across eras
    all_paths = set().union(*[set(s.keys()) for s in era_structures.values()])
    
    # Create comparison DataFrame
    comparison_data = []
    for path in sorted(all_paths):
        row = {'path': path}
        for era in years.keys():
            if era in era_structures:
                types = era_structures[era].get(path, set())
                row[era] = ', '.join(sorted(types)) if types else 'N/A'
        comparison_data.append(row)
    
    df = pd.DataFrame(comparison_data)
    return df

if __name__ == "__main__":
    # Run analysis and display results
    comparison_df = compare_eras()
    
    # Show only differences between eras
    different_structures = comparison_df[comparison_df.apply(
        lambda x: len(set(x[1:])) > 1 if not x[1:].isna().all() else False, 
        axis=1
    )]
    
    print("\nFields that differ between eras:")
    print(different_structures.to_string())
    
    # Save results
    different_structures.to_csv('era_differences.csv', index=False)
    print("\nResults saved to era_differences.csv")