#!/usr/bin/env python3
"""
Resume Crew - Complete 3-tool iterative process
Tool 1: Keyword Extractor → Tool 2: Resume Tailor → Tool 3: Resume Evaluator
Runs 3 iterations: Tool2→Tool3→Tool2→Tool3→Tool2→Tool3
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional
from tools.tool1 import KeywordExtractor
from tools.tool2 import ResumeTailor
from tools.tool3 import ResumeEvaluator
from tools.tool4 import LatexResumeFormatter

class ResumeCrew:
    """Complete resume processor with all 3 tools and iterative process"""
    
    def __init__(self):
        """Initialize the crew with all 3 tools"""
        self.keyword_extractor = KeywordExtractor()
        self.resume_tailor = ResumeTailor()
        self.resume_evaluator = ResumeEvaluator()
        self.latex_formatter = LatexResumeFormatter()
        self.process_log = []
        
    def log_step(self, step, data):
        """Log each step of the process"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "data": data
        }
        self.process_log.append(log_entry)
        print(f"🔄 {step}")
    
    def save_process_log(self):
        """Save the complete process log"""
        try:
            os.makedirs('output', exist_ok=True)
            log_file = os.path.join('output', 'process_log.json')
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(self.process_log, f, indent=2, ensure_ascii=False)
            print(f"📋 Process log saved to {log_file}")
        except Exception as e:
            print(f"⚠️  Warning: Could not save process log - {e}")
    
    def save_content(self, content, filename):
        """Save content to file"""
        try:
            os.makedirs('output', exist_ok=True)
            filepath = os.path.join('output', filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"💾 Saved {filename}")
        except Exception as e:
            print(f"⚠️  Warning: Could not save {filename} - {e}")

    def run_tailoring_process(
        self,
        job_description,
        current_resume,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        """
        Complete 3-tool iterative process:
        1. Tool 1: Extract keywords once
        2. Iterate 3 times: Tool 2 (tailor) → Tool 3 (evaluate) → feedback → repeat
        """
        
        print("🎯 PHASE 1: Keyword Extraction with Claude Opus 4.5 (Tool 1)")
        print("=" * 60)
        
        # TOOL 1: Extract keywords from job description (run once)
        self.log_step("TOOL 1: Extracting keywords from job description", {})
        
        try:
            keyword_analysis = self.keyword_extractor.extract_keywords(job_description)
            
            # Save the keyword analysis
            self.keyword_extractor.save_analysis(keyword_analysis)
            
            self.log_step("Keywords extracted successfully", {
                "keywords_count": len(keyword_analysis.get('keywords', [])),
                "needs_count": len(keyword_analysis.get('needs', [])),
                "results_count": len(keyword_analysis.get('results', []))
            })
            
            print(f"✅ Extracted {len(keyword_analysis.get('keywords', []))} keywords")
            print(f"✅ Identified {len(keyword_analysis.get('needs', []))} needs")
            print(f"✅ Found {len(keyword_analysis.get('results', []))} result patterns")
            
        except Exception as e:
            print(f"❌ Error in keyword extraction: {e}")
            keyword_analysis = {
                "keywords": [], 
                "needs": [], 
                "results": [], 
                "error": str(e)
            }
            
        if progress_callback:
            progress_callback({
                "event": "keywords_extracted",
                "status": "keywords_extracted",
                "keyword_analysis": keyword_analysis,
                "job_description": job_description,
                "original_resume": current_resume
            })

        print(f"\n🔄 PHASE 2: Iterative Tailoring Process (3 Rounds)")
        print("=" * 60)
        print("Each round: Tool 2 (Tailor) → Tool 3 (Evaluate) → Feedback")
        
        # Track resumes and evaluations across rounds
        latest_resume = current_resume
        best_resume = current_resume
        best_score = -1
        best_round = 0
        best_evaluation = None
        all_evaluations = []

        # Run 3 iterations of Tool2 → Tool3
        for round_num in range(1, 4):
            print(f"\n{'='*20} ROUND {round_num} {'='*20}")
            
            # TOOL 2: Tailor Resume
            print(f"🎨 Round {round_num} - Tool 2: Tailoring Resume")
            print("-" * 40)
            
            self.log_step(f"ROUND {round_num} - TOOL 2: Tailoring resume", {})
            
            # Get feedback from previous round (if any)
            feedback = None
            if round_num > 1 and all_evaluations:
                previous_eval = all_evaluations[-1]
                feedback = previous_eval.get('feedback', '') + "\n" + "\n".join(previous_eval.get('recommendations', []))
                print(f"📝 Using feedback from Round {round_num-1}")
            
            try:
                tailored_data = self.resume_tailor.tailor_resume(
                    original_resume=latest_resume,
                    keywords=keyword_analysis,
                    job_description=job_description,
                    feedback=feedback,
                    round_number=round_num
                )
                
                # Save this version
                version_filename = f"tailored_resume_round_{round_num}.txt"
                self.resume_tailor.save_tailored_resume(tailored_data, version_filename)
                
                # Update current best
                latest_resume = tailored_data.get('tailored_resume', latest_resume)
                
                self.log_step(f"ROUND {round_num} - Resume tailored", {
                    "tailored_resume_length": len(latest_resume.split()),
                    "changes_made": len(tailored_data.get('change_log', [])),
                    "has_feedback": feedback is not None
                })
                
                print(f"✅ Round {round_num} tailoring complete!")
                print(f"📝 Changes made: {len(tailored_data.get('change_log', []))}")
                
            except Exception as e:
                print(f"❌ Error in Round {round_num} tailoring: {e}")
                tailored_data = {
                    "tailored_resume": latest_resume, 
                    "change_log": [f"Error: {str(e)}"]
                }
            
            # TOOL 3: Evaluate Resume
            print(f"\n📊 Round {round_num} - Tool 3: Evaluating Resume")
            print("-" * 40)
            
            self.log_step(f"ROUND {round_num} - TOOL 3: Evaluating resume", {})
            
            try:
                evaluation = self.resume_evaluator.evaluate_resume(
                    job_description=job_description,
                    tailored_resume=latest_resume,
                    keywords=keyword_analysis
                )
                
                # Save this evaluation
                eval_filename = f"evaluation_round_{round_num}.txt"
                self.resume_evaluator.save_evaluation(evaluation, eval_filename)
                
                all_evaluations.append(evaluation)
                
                self.log_step(f"ROUND {round_num} - Evaluation complete", {
                    "score": evaluation.get('score', 0),
                    "recommendations_count": len(evaluation.get('recommendations', []))
                })
                
                print(f"📊 Round {round_num} Score: {evaluation.get('score', 0)}/100")
                print(f"💡 Recommendations: {len(evaluation.get('recommendations', []))}")
                
                # Show top recommendations
                for i, rec in enumerate(evaluation.get('recommendations', [])[:2], 1):
                    print(f"   {i}. {rec[:80]}...")
                
            except Exception as e:
                print(f"❌ Error in Round {round_num} evaluation: {e}")
                evaluation = {
                    "score": 0, 
                    "feedback": f"Error: {str(e)}", 
                    "recommendations": []
                }
                all_evaluations.append(evaluation)

            score_value = evaluation.get("score", 0)
            try:
                score_value = float(score_value)
            except (TypeError, ValueError):
                score_value = 0

            if score_value > best_score:
                best_score = score_value
                best_resume = latest_resume
                best_evaluation = evaluation
                best_round = round_num

            if progress_callback:
                progress_callback({
                    "event": "round_complete",
                    "status": f"round_{round_num}_complete",
                    "round": round_num,
                    "keyword_analysis": keyword_analysis,
                    "tailored_resume": latest_resume,
                    "change_log": tailored_data.get('change_log', []),
                    "evaluation": evaluation,
                    "all_evaluations": list(all_evaluations),
                })

        if best_round == 0 and all_evaluations:
            best_round = len(all_evaluations)
            best_evaluation = all_evaluations[-1]
            try:
                best_score = float(best_evaluation.get('score', 0))
            except (TypeError, ValueError):
                best_score = 0
            best_resume = latest_resume

        if isinstance(best_score, (int, float)):
            best_score = int(round(best_score))
        else:
            best_score = 0

        print(f"\n🎉 PHASE 3: Final Results & Summary")
        print("=" * 60)
        
        # Save inputs
        self.save_content(job_description, "job_description.txt")
        self.save_content(current_resume, "original_resume.txt")
        
        # Save final best resume
        self.save_content(best_resume, "final_tailored_resume.txt")

        # TOOL 4: Convert final resume to LaTeX
        latex_summary = {"status": "skipped"}
        try:
            latex_result = self.latex_formatter.format_to_latex(best_resume)
            latex_document = latex_result.get("latex_document", "")
            latex_summary["raw_response_length"] = len(latex_result.get("raw_response", ""))

            if latex_document:
                project_root = Path(__file__).resolve().parent.parent  # Go up to RESUME-MAKER root
                docs_latex_path = project_root / "docs" / "latex" / "main.tex"
                output_tex_path = project_root / "output" / "final_tailored_resume.tex"

                # Ensure docs/latex directory exists
                docs_latex_path.parent.mkdir(parents=True, exist_ok=True)

                self.latex_formatter.save_latex(latex_document, docs_latex_path, create_backup=True)
                self.latex_formatter.save_latex(latex_document, output_tex_path, create_backup=False)

                latex_summary.update({
                    "status": "success",
                    "main_tex_path": str(docs_latex_path),
                    "output_tex_path": str(output_tex_path),
                    "latex_length": len(latex_document.split())
                })
            else:
                latex_summary.update({
                    "status": "failure",
                    "error": latex_result.get("raw_response", "Empty LaTeX output")
                })
        except Exception as exc:
            latex_summary.update({
                "status": "error",
                "error": str(exc)
            })
            print(f"Warning: Tool 4 LaTeX generation failed - {exc}")

        self.log_step("TOOL 4: LaTeX resume conversion", latex_summary)
        
        # Create summary report
        self._create_summary_report(keyword_analysis, all_evaluations, best_resume, best_round, best_score)
        
        # Log final results
        self.log_step("Complete process finished", {
            "jd_length": len(job_description.split()),
            "original_resume_length": len(current_resume.split()),
            "final_resume_length": len(best_resume.split()),
            "final_score": best_score,
            "best_round": best_round,
            "total_rounds": 3,
            "keyword_analysis": keyword_analysis,
            "all_evaluations": all_evaluations,
            "best_evaluation": best_evaluation
        })
        
        # Save process log
        self.save_process_log()
        
        # Show final summary
        final_score = best_score
        print(f"🏆 Best Score: {best_score}/100 (Round {best_round or 1})")
        print(f"📈 Score Progress: {' → '.join([str(eval.get('score', 0)) for eval in all_evaluations])}")
        print(f"📄 Final Resume: {len(best_resume.split())} words")
        
        print("\nOutput Files Created:")
        print("   - job_description.txt - Your input JD")
        print("   - original_resume.txt - Your original resume")
        print("   - keyword_analysis.txt - Extracted keywords (Tool 1)")
        print("   - tailored_resume_round_1.txt - Round 1 resume")
        print("   - evaluation_round_1.txt - Round 1 evaluation")
        print("   - tailored_resume_round_2.txt - Round 2 resume")
        print("   - evaluation_round_2.txt - Round 2 evaluation")
        print("   - tailored_resume_round_3.txt - Round 3 resume")
        print("   - evaluation_round_3.txt - Round 3 evaluation")
        print("   - final_tailored_resume.txt - Best final resume")
        if latex_summary.get("status") == "success":
            print(f"   - docs/latex/main.tex - LaTeX resume from best round (Round {best_round})")
            print("   - output/final_tailored_resume.tex - LaTeX export copy")
        else:
            print("   - docs/latex/main.tex - Not updated (Tool 4 encountered an issue)")
        print("   - process_summary.txt - Complete summary report")
        print("   - process_log.json - Detailed process log")
        
        return {
            "job_description": job_description,
            "original_resume": current_resume,
            "final_resume": best_resume,
            "keyword_analysis": keyword_analysis,
            "all_evaluations": all_evaluations,
            "final_score": final_score,
            "best_round": best_round,
            "best_evaluation": best_evaluation,
            "status": "complete_3_tool_process_finished",
            "latex_summary": latex_summary
        }
    
    def _create_summary_report(self, keyword_analysis, all_evaluations, final_resume, best_round, best_score):
        """Create a comprehensive summary report"""
        try:
            os.makedirs('output', exist_ok=True)
            filepath = os.path.join('output', 'process_summary.txt')
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("RESUME AUTOMATION PROCESS SUMMARY\n")
                f.write("=" * 60 + "\n\n")
                
                # Process Overview
                f.write("📋 PROCESS OVERVIEW\n")
                f.write("-" * 30 + "\n")
                f.write("✅ Tool 1: Keyword Extraction - COMPLETED\n")
                f.write("✅ Tool 2: Resume Tailoring - 3 ROUNDS COMPLETED\n")
                f.write("✅ Tool 3: Resume Evaluation - 3 ROUNDS COMPLETED\n\n")
                
                # Keywords Summary
                f.write("🎯 KEYWORDS EXTRACTED\n")
                f.write("-" * 30 + "\n")
                f.write(f"Keywords: {len(keyword_analysis.get('keywords', []))}\n")
                f.write(f"Needs: {len(keyword_analysis.get('needs', []))}\n")
                f.write(f"Results: {len(keyword_analysis.get('results', []))}\n\n")
                
                # Score Progress
                f.write("📈 SCORE PROGRESSION\n")
                f.write("-" * 30 + "\n")
                for i, eval_data in enumerate(all_evaluations, 1):
                    score = eval_data.get('score', 0)
                    f.write(f"Round {i}: {score}/100\n")
                
                if len(all_evaluations) > 1:
                    improvement = all_evaluations[-1].get('score', 0) - all_evaluations[0].get('score', 0)
                    f.write(f"\nTotal Improvement: +{improvement} points\n")
                
                if best_round:
                    f.write(f"Best Round: Round {best_round} (Score: {best_score}/100)\n")

                f.write("\n" + "=" * 60 + "\n")
                f.write("FINAL RECOMMENDATIONS\n")
                f.write("=" * 60 + "\n")
                
                final_eval = None
                if best_round and 0 < best_round <= len(all_evaluations):
                    final_eval = all_evaluations[best_round - 1]
                elif all_evaluations:
                    final_eval = all_evaluations[-1]

                if final_eval:
                    for i, rec in enumerate(final_eval.get('recommendations', []), 1):
                        f.write(f"{i}. {rec}\n")
                else:
                    f.write("No recommendations available.\n")

                f.write(f"\n🎉 Process completed successfully!\n")
                f.write(f"Final resume ready for submission.\n")
            
            print(f"📊 Summary report saved to {filepath}")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not create summary report - {e}")
