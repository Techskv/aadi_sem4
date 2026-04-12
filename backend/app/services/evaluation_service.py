"""
Evaluation Service - Automatic answer evaluation logic.
"""
from typing import List, Dict, Optional, Tuple
from fuzzywuzzy import fuzz
import re

from app.models.exam import AnswerKey


class EvaluationService:
    """Service for evaluating extracted answers against answer keys."""
    
    def __init__(self):
        """Initialize evaluation service."""
        self.fuzzy_threshold = 80  # Minimum fuzzy match score
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        if not text:
            return ""
        # Lowercase, remove extra whitespace, strip
        text = text.lower().strip()
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def evaluate_mcq(
        self, 
        student_answer: str, 
        correct_answer: str,
        max_marks: float,
        negative_marks: float = 0
    ) -> Tuple[float, str]:
        """
        Evaluate MCQ/objective question.
        
        Returns:
            Tuple of (marks_obtained, feedback)
        """
        student = self.normalize_text(student_answer)
        correct = self.normalize_text(correct_answer)
        
        # Handle multiple formats: "A", "Option A", "(A)", etc.
        student_option = self._extract_option(student)
        correct_option = self._extract_option(correct)
        
        if student_option == correct_option:
            return max_marks, "Correct answer"
        elif student_option:
            return -negative_marks if negative_marks else 0, f"Incorrect. Correct: {correct_answer}"
        else:
            return 0, "No answer provided"
    
    def _extract_option(self, text: str) -> Optional[str]:
        """Extract option letter from various formats."""
        if not text:
            return None
        
        # Match patterns like "a", "(a)", "option a", "ans: a"
        match = re.search(r'(?:option\s*|ans[:\s]*)?[\(\[]?([a-d])[\)\]]?', text, re.IGNORECASE)
        if match:
            return match.group(1).lower()
        return None
    
    def evaluate_short_answer(
        self,
        student_answer: str,
        keywords: List[str],
        max_marks: float,
        correct_answer: Optional[str] = None
    ) -> Tuple[float, List[str], str]:
        """
        Evaluate short answer using keyword matching.
        
        Returns:
            Tuple of (marks_obtained, matched_keywords, feedback)
        """
        if not student_answer or not student_answer.strip():
            return 0, [], "No answer provided"
        
        student_text = self.normalize_text(student_answer)
        matched_keywords = []
        
        # Check each keyword
        for keyword in keywords:
            keyword_normalized = self.normalize_text(keyword)
            
            # Try exact match first
            if keyword_normalized in student_text:
                matched_keywords.append(keyword)
                continue
            
            # Try fuzzy match
            words = student_text.split()
            for word in words:
                if fuzz.ratio(word, keyword_normalized) >= self.fuzzy_threshold:
                    matched_keywords.append(keyword)
                    break
            
            # Try partial ratio for phrases
            if keyword not in matched_keywords:
                if fuzz.partial_ratio(keyword_normalized, student_text) >= self.fuzzy_threshold:
                    matched_keywords.append(keyword)
        
        # Calculate marks
        if keywords:
            score_ratio = len(matched_keywords) / len(keywords)
            marks = round(max_marks * score_ratio, 2)
        else:
            marks = 0
        
        # Generate feedback
        if marks == max_marks:
            feedback = "Complete answer - all key points covered"
        elif marks > 0:
            missing = [k for k in keywords if k not in matched_keywords]
            feedback = f"Partial marks. Missing: {', '.join(missing[:3])}"
        else:
            feedback = "Key points not found in answer"
        
        return marks, matched_keywords, feedback
    
    def evaluate_subjective(
        self,
        student_answer: str,
        rubric: Dict,
        max_marks: float
    ) -> Tuple[float, Dict, str, bool]:
        """
        Pre-evaluate subjective answer for teacher review.
        
        Returns:
            Tuple of (suggested_marks, rubric_scores, feedback, needs_review)
        """
        if not student_answer or not student_answer.strip():
            return 0, {}, "No answer provided", False
        
        student_text = self.normalize_text(student_answer)
        word_count = len(student_text.split())
        
        # Basic analysis
        rubric_scores = {}
        suggested_marks = 0
        
        for criterion, criterion_marks in rubric.items():
            # Simple heuristics - in production, use NLP
            if criterion.lower() in ['length', 'word_count']:
                # Check minimum word count
                score = min(criterion_marks, (word_count / 50) * criterion_marks)
                rubric_scores[criterion] = round(score, 2)
            elif criterion.lower() in ['introduction', 'intro']:
                # Check if answer has opening
                has_intro = any(w in student_text[:100] for w in ['firstly', 'introduction', 'begin'])
                rubric_scores[criterion] = criterion_marks if has_intro else 0
            elif criterion.lower() in ['conclusion', 'summary']:
                # Check if answer has closing
                has_conclusion = any(w in student_text[-100:] for w in ['therefore', 'conclusion', 'finally', 'thus'])
                rubric_scores[criterion] = criterion_marks if has_conclusion else 0
            else:
                # Default: placeholder for manual review
                rubric_scores[criterion] = 0
            
            suggested_marks += rubric_scores[criterion]
        
        # Cap at max marks
        suggested_marks = min(suggested_marks, max_marks)
        
        feedback = f"Auto-analysis: {word_count} words. Needs manual review for subjective criteria."
        
        return suggested_marks, rubric_scores, feedback, True
    
    def evaluate_answer(
        self,
        student_answer: str,
        answer_key: AnswerKey
    ) -> Dict:
        """
        Main entry point to evaluate an answer.
        
        Returns:
            Dict with marks_obtained, feedback, evaluation_type, needs_review, matched_keywords
        """
        question_type = answer_key.question_type.upper()
        
        if question_type == 'MCQ':
            marks, feedback = self.evaluate_mcq(
                student_answer,
                answer_key.correct_answer,
                answer_key.max_marks,
                answer_key.negative_marks
            )
            return {
                'marks_obtained': marks,
                'feedback': feedback,
                'evaluation_type': 'automatic',
                'needs_review': False,
                'matched_keywords': None
            }
        
        elif question_type == 'SHORT_ANSWER':
            keywords = answer_key.keywords or []
            marks, matched, feedback = self.evaluate_short_answer(
                student_answer,
                keywords,
                answer_key.max_marks,
                answer_key.correct_answer
            )
            return {
                'marks_obtained': marks,
                'feedback': feedback,
                'evaluation_type': 'automatic',
                'needs_review': marks < answer_key.max_marks,  # Flag for review if not full marks
                'matched_keywords': matched
            }
        
        elif question_type == 'SUBJECTIVE':
            rubric = answer_key.rubric or {}
            marks, rubric_scores, feedback, needs_review = self.evaluate_subjective(
                student_answer,
                rubric,
                answer_key.max_marks
            )
            return {
                'marks_obtained': marks,
                'feedback': feedback,
                'evaluation_type': 'automatic',
                'needs_review': True,  # Always needs teacher review
                'matched_keywords': None,
                'rubric_scores': rubric_scores
            }
        
        else:
            return {
                'marks_obtained': 0,
                'feedback': f"Unknown question type: {question_type}",
                'evaluation_type': 'automatic',
                'needs_review': True,
                'matched_keywords': None
            }


# Singleton instance
evaluation_service = EvaluationService()
