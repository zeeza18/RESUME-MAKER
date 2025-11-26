#!/usr/bin/env python3
"""
Resume Automation Tool - Main Entry Point
Collects Job Description and Resume inputs from user
"""

import os
import sys
from resume_crew import ResumeCrew

def print_banner():
    """Print application banner"""
    print("="*60)
    print("🤖 AUTOMATED RESUME TAILOR")
    print("="*60)
    print("Tailors your resume to match job descriptions using AI")
    print("-"*60)

def get_multiline_input(prompt):
    """Get multiline input from user"""
    print(f"\n{prompt}")
    print("(Press Enter twice when finished, or type 'END' on a new line)")
    print("-" * 50)
    
    lines = []
    empty_line_count = 0
    
    while True:
        try:
            line = input()
            
            if line.strip().upper() == 'END':
                break
                
            if line.strip() == '':
                empty_line_count += 1
                if empty_line_count >= 2:
                    break
            else:
                empty_line_count = 0
            
            lines.append(line)
            
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            sys.exit(1)
    
    # Remove trailing empty lines
    while lines and lines[-1].strip() == '':
        lines.pop()
    
    return '\n'.join(lines)

def validate_input(text, input_type):
    """Validate user input"""
    if not text or len(text.strip()) < 50:
        print(f"❌ {input_type} seems too short. Please provide more detailed information.")
        return False
    return True

def save_to_file(content, filename):
    """Save content to file for reference"""
    try:
        os.makedirs('output', exist_ok=True)
        filepath = os.path.join('output', filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Saved to {filepath}")
    except Exception as e:
        print(f"⚠️  Warning: Could not save to file - {e}")

def main():
    """Main function to collect inputs and start resume processing"""
    
    print_banner()
    
    # Collect Job Description
    print("\n📋 STEP 1: Job Description")
    print("Please paste the job description you want to tailor your resume for:")
    
    job_description = get_multiline_input("📝 Enter Job Description:")
    
    if not validate_input(job_description, "Job Description"):
        print("Please restart and provide a more detailed job description.")
        return
    
    print(f"\n✅ Job Description captured ({len(job_description.split())} words)")
    
    # Collect Resume
    print("\n📄 STEP 2: Current Resume")
    print("Please paste your current resume content:")
    
    current_resume = get_multiline_input("📝 Enter Your Current Resume:")
    
    if not validate_input(current_resume, "Resume"):
        print("Please restart and provide a more detailed resume.")
        return
    
    print(f"\n✅ Resume captured ({len(current_resume.split())} words)")
    
    # Save inputs for reference
    print("\n💾 Saving inputs...")
    save_to_file(job_description, 'input_job_description.txt')
    save_to_file(current_resume, 'input_current_resume.txt')
    
    # Confirmation
    print("\n🔍 REVIEW:")
    print(f"- Job Description: {len(job_description.split())} words")
    print(f"- Current Resume: {len(current_resume.split())} words")
    
    confirm = input("\nProceed with resume tailoring? (y/n): ").lower().strip()
    
    if confirm != 'y' and confirm != 'yes':
        print("Operation cancelled. Your inputs have been saved in the 'output' folder.")
        return
    
    # Start the crew process
    print("\n🚀 Starting Resume Tailoring Process...")
    print("="*60)
    
    try:
        # Initialize and run the crew
        crew = ResumeCrew()
        result = crew.run_tailoring_process(
            job_description=job_description,
            current_resume=current_resume
        )
        
        print("\n" + "="*60)
        print("🎉 PROCESS COMPLETED!")
        print("="*60)
        print("Check the 'output' folder for your tailored resume and process logs.")
        
    except ImportError:
        print("\n❌ Error: crew.py not found or has issues.")
        print("Please make sure crew.py is implemented in the same directory.")
        print("Your inputs have been saved and you can run the crew separately.")
        
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        print("Your inputs have been saved in the 'output' folder.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGoodbye! 👋")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print("Please check your setup and try again.") 