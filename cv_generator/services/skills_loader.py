import sys


def load_skills(filepath: str) -> str:
    """Load skills file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"Loaded skills file: {filepath}")
        return content
    except Exception as e:
        print(f"Error loading skills file: {e}")
        sys.exit(1)
