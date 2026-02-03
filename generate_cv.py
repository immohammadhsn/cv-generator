#!/usr/bin/env python3
import os
import sys

from cv_generator.orchestrator import generate_cv

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_cv.py <job_url> [skills_file] [output_dir]")
        print("Example: python generate_cv.py https://example.com/job my-skills.md ./output")
        sys.exit(1)
    
    job_url = sys.argv[1]
    skills_file = sys.argv[2] if len(sys.argv) > 2 else "my-skills.md"
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "./output"
    
    print("=" * 70)
    print("CV GENERATOR - Powered by Groq AI")
    print("=" * 70)
    print(f"Working directory: {os.getcwd()}")
    print(f"Output directory: {os.path.abspath(output_dir)}")
    print("=" * 70)

    job_title, pdf_path = generate_cv(job_url, skills_file, output_dir)
    
    print("\n" + "=" * 70)
    print("✅ CV GENERATION COMPLETE!")
    print("=" * 70)
    print(f"📄 Job Title: {job_title}")
    print(f"📁 PDF Location: {pdf_path}")
    print(f"💡 Tip: Copy this path to open the file")
    print("=" * 70)

if __name__ == "__main__":
    main()
