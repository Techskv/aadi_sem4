"""
LLM Evaluation Service — Uses Qwen 2.5 72B (via OpenAI-compatible API) for intelligent answer evaluation.
Supports any OpenAI-compatible provider: OpenRouter, DeepInfra, Alibaba DashScope, etc.
"""
import json
import logging
from typing import Dict, Optional, List

from app.config import get_settings
from app.services.rag_service import rag_service

settings = get_settings()
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Initialize OpenAI-compatible client (works with any provider)
# ─────────────────────────────────────────────────────────────
LLM_AVAILABLE = False
llm_client = None

try:
    from openai import OpenAI

    if settings.LLM_API_KEY and settings.LLM_BASE_URL:
        llm_client = OpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
        LLM_AVAILABLE = True
        masked_key = f"{settings.LLM_API_KEY[:6]}...{settings.LLM_API_KEY[-4:]}" if settings.LLM_API_KEY else "None"
        logger.info(
            f"LLM initialized with key {masked_key} "
            f"(model={settings.LLM_MODEL}, base_url={settings.LLM_BASE_URL})"
        )
    else:
        logger.warning("LLM_API_KEY or LLM_BASE_URL not set. LLM evaluation disabled.")
except ImportError:
    logger.warning("openai package not installed. LLM evaluation disabled.")
except Exception as e:
    logger.warning(f"LLM client initialization failed: {e}")


class LLMEvaluationService:
    """Evaluates student answers using Qwen 2.5 72B (OpenAI-compatible API)."""

    @property
    def MODEL(self) -> str:
        return settings.LLM_MODEL

    def evaluate_answer(
        self,
        exam_id: int,
        question_text: str,
        student_answer: str,
        correct_answer: Optional[str],
        keywords: Optional[List[str]],
        question_type: str,
        max_marks: float
    ) -> Dict:
        """
        Evaluate a single answer using LLM.

        Returns:
            Dict with marks_obtained, feedback, evaluation_type
        """
        if not LLM_AVAILABLE or not llm_client:
            return None  # Fallback to rule-based

        if not student_answer or not student_answer.strip():
            return {
                "marks_obtained": 0,
                "feedback": "No answer provided.",
                "evaluation_type": "automatic",
                "needs_review": False,
                "matched_keywords": []
            }

        try:
            # 1. Retrieve Context via RAG
            context = rag_service.query_context(exam_id, f"{question_text} {correct_answer}")

            # 2. Build Prompt
            prompt = self._build_evaluation_prompt(
                question_text=question_text,
                student_answer=student_answer,
                correct_answer=correct_answer,
                keywords=keywords,
                question_type=question_type,
                max_marks=max_marks,
                context=context
            )

            completion = llm_client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert academic evaluator. You evaluate student answers "
                            "accurately and fairly. You MUST respond ONLY with a valid JSON object. "
                            "No explanations outside JSON. No markdown formatting."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=512,
                top_p=1,
            )

            response_text = completion.choices[0].message.content.strip()
            result = self._parse_llm_response(response_text, max_marks)
            logger.info(f"LLM evaluation: {result['marks_obtained']}/{max_marks}")
            return result

        except Exception as e:
            logger.error(f"LLM evaluation failed: {str(e)}")
            return None  # Fallback to rule-based

    def evaluate_all_answers(
        self,
        exam_id: int,
        questions_and_answers: List[Dict],
        exam_name: str = ""
    ) -> List[Dict]:
        """
        Evaluate all answers, splitting into chunks of 10 if there are many questions.
        This ensures the LLM never gets overwhelmed and every question is evaluated.
        """
        if not LLM_AVAILABLE or not llm_client:
            return None

        if not questions_and_answers:
            return None

        total = len(questions_and_answers)
        logger.info(f"evaluate_all_answers: {total} questions to evaluate")

        # Chunk into groups of 10 to avoid token limits
        CHUNK_SIZE = 10
        all_results = []

        for chunk_start in range(0, total, CHUNK_SIZE):
            chunk = questions_and_answers[chunk_start : chunk_start + CHUNK_SIZE]
            chunk_num = chunk_start // CHUNK_SIZE + 1
            total_chunks = (total + CHUNK_SIZE - 1) // CHUNK_SIZE
            logger.info(f"Evaluating chunk {chunk_num}/{total_chunks} ({len(chunk)} questions)")

            try:
                chunk_results = self._evaluate_chunk(exam_id, chunk, exam_name)
                if chunk_results:
                    all_results.extend(chunk_results)
                else:
                    # Chunk failed — fill with 0-marks for review
                    for qa in chunk:
                        all_results.append({
                            "question_no": qa["question_no"],
                            "marks_obtained": 0,
                            "feedback": "Evaluation failed for this question. Needs manual review.",
                            "evaluation_type": "llm",
                            "needs_review": True,
                            "matched_keywords": []
                        })
            except Exception as e:
                logger.error(f"Chunk {chunk_num} failed: {e}")
                for qa in chunk:
                    all_results.append({
                        "question_no": qa["question_no"],
                        "marks_obtained": 0,
                        "feedback": f"Evaluation error: {str(e)}",
                        "evaluation_type": "llm",
                        "needs_review": True,
                        "matched_keywords": []
                    })

        logger.info(f"evaluate_all_answers: completed {len(all_results)}/{total} results")
        return all_results if len(all_results) == total else None

    def _evaluate_chunk(
        self,
        exam_id: int,
        questions_and_answers: List[Dict],
        exam_name: str = ""
    ) -> List[Dict]:
        """Evaluate a single chunk of up to 10 questions via one LLM call."""
        try:
            for qa in questions_and_answers:
                qa["rag_context"] = rag_service.query_context(
                    exam_id,
                    f"{qa.get('question_text')} {qa.get('correct_answer')}"
                )

            prompt = self._build_batch_prompt(questions_and_answers, exam_name)

            completion = llm_client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert academic evaluator. "
                            "You MUST evaluate EVERY question listed — do not skip any. "
                            "Respond ONLY with a valid JSON array containing one entry per question. "
                            "No markdown. No ```json. No extra text."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=2000,
                top_p=1,
            )

            response_text = completion.choices[0].message.content.strip()
            results = self._parse_batch_response(response_text, questions_and_answers)
            logger.info(f"LLM chunk evaluation: {len(results) if results else 0}/{len(questions_and_answers)} questions")
            return results

        except Exception as e:
            logger.error(f"LLM chunk evaluation failed: {e}", exc_info=True)
            return None

    def _build_evaluation_prompt(
        self,
        question_text: str,
        student_answer: str,
        correct_answer: Optional[str],
        keywords: Optional[List[str]],
        question_type: str,
        max_marks: float,
        context: Optional[str] = None
    ) -> str:
        """Build the evaluation prompt for a single question."""

        rag_part = f"\n**Reference Context (RAG):**\n{context}\n" if context else ""

        prompt = f"""Evaluate the following student answer. {rag_part}

**Question Type:** {question_type}
**Maximum Marks:** {max_marks}

**Question:** {question_text or 'Not provided'}

**Correct Answer / Model Answer:** {correct_answer or 'Not provided'}

**Keywords to look for:** {', '.join(keywords) if keywords else 'None specified'}

**Student's Answer:** {student_answer}

---

Evaluate the student's answer and respond with ONLY this JSON (no other text):
{{
    "marks_obtained": <number between 0 and {max_marks}>,
    "feedback": "<brief constructive feedback explaining the grade>",
    "matched_keywords": [<list of keywords the student covered>],
    "needs_review": <true if answer is ambiguous and needs teacher review, false otherwise>
}}"""
        return prompt

    def _build_batch_prompt(self, questions_and_answers: List[Dict], exam_name: str) -> str:
        """Build a batch evaluation prompt for all questions at once."""

        questions_text = ""
        for qa in questions_and_answers:
            keywords_str = ', '.join(qa.get('keywords') or []) if qa.get('keywords') else 'None'
            context_str = f"Context: {qa['rag_context']}" if qa.get("rag_context") else ""
            questions_text += f"""
--- Question {qa['question_no']} ---
Type: {qa['question_type']}
Max Marks: {qa['max_marks']}
Question: {qa.get('question_text', 'Not provided')}
Correct Answer: {qa.get('correct_answer', 'Not provided')}
{context_str}
Keywords: {keywords_str}
Student Answer: {qa.get('student_answer', 'No answer provided')}
"""

        prompt = f"""You are evaluating a student's exam submission{f' for "{exam_name}"' if exam_name else ''}.

Evaluate each question below fairly. For MCQ questions, check if the answer option matches. For short answers, check semantic correctness and keyword coverage. For subjective answers, evaluate depth, accuracy, and completeness.

{questions_text}

---

Respond with ONLY a JSON array (no markdown, no code blocks, just raw JSON):
[
    {{
        "question_no": <number>,
        "marks_obtained": <number between 0 and max_marks>,
        "feedback": "<brief constructive feedback>",
        "matched_keywords": [<list of keywords covered>],
        "needs_review": <boolean>
    }},
    ...
]"""
        return prompt

    def _parse_llm_response(self, response_text: str, max_marks: float) -> Dict:
        """Parse single question LLM response with robustness."""
        try:
            cleaned = response_text.strip()

            # Find the first { and last }
            start = cleaned.find('{')
            end = cleaned.rfind('}')

            if start != -1 and end != -1:
                json_str = cleaned[start:end+1]
                result = json.loads(json_str)
            else:
                logger.warning(f"No JSON object found in response: {response_text[:200]}")
                return None

            # Validate and clamp marks
            marks = float(result.get("marks_obtained", 0))
            marks = max(0, min(marks, max_marks))

            return {
                "marks_obtained": round(marks, 2),
                "feedback": result.get("feedback", "Evaluated by AI"),
                "evaluation_type": "llm",
                "needs_review": result.get("needs_review", False),
                "matched_keywords": result.get("matched_keywords", [])
            }
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse LLM response: {e}. Response: {response_text[:200]}")
            return None

    def _parse_batch_response(self, response_text: str, original_questions: List[Dict]) -> List[Dict]:
        """Parse batch LLM response with robustness (handling markdown and conversational text)."""
        try:
            cleaned = response_text.strip()

            # Find the first [ and last ]
            start = cleaned.find('[')
            end = cleaned.rfind(']')

            if start != -1 and end != -1:
                json_str = cleaned[start:end+1]
                results_list = json.loads(json_str)
            else:
                logger.warning(f"No JSON array found in response: {response_text[:300]}")
                return None

            if not isinstance(results_list, list):
                logger.warning("LLM response is not a list")
                return None

            # Map results by question_no
            results_map = {}
            for item in results_list:
                qno = item.get("question_no")
                if qno is not None:
                    results_map[qno] = item

            # Build final results aligned with original questions
            final_results = []
            for qa in original_questions:
                qno = qa["question_no"]
                max_m = qa["max_marks"]

                if qno in results_map:
                    r = results_map[qno]
                    marks_val = r.get("marks_obtained", 0)
                    try:
                        marks = float(marks_val)
                    except (ValueError, TypeError):
                        marks = 0

                    marks = max(0, min(marks, max_m))

                    final_results.append({
                        "question_no": qno,
                        "marks_obtained": round(marks, 2),
                        "feedback": r.get("feedback", "Evaluated by AI"),
                        "evaluation_type": "llm",
                        "needs_review": r.get("needs_review", False),
                        "matched_keywords": r.get("matched_keywords", [])
                    })
                else:
                    # Question not in LLM response — mark for review
                    final_results.append({
                        "question_no": qno,
                        "marks_obtained": 0,
                        "feedback": "LLM did not evaluate this question. Needs manual review.",
                        "evaluation_type": "llm",
                        "needs_review": True,
                        "matched_keywords": []
                    })

            return final_results

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse batch LLM response: {e}. Response: {response_text[:300]}")
            return None

    def evaluate_unstructured_document(self, exam_id: int, full_text: str, question_paper_text: Optional[str] = None) -> List[Dict]:
        """
        Evaluate a document where questions and answers are not pre-parsed.
        """
        if not LLM_AVAILABLE or not llm_client:
            return None

        # Try to find context for the entire document or key terms
        context = rag_service.query_context(exam_id, full_text[:1000], k=3)
        rag_info = f"\nReference Materials Context:\n---\n{context[:1000]}\n---\n" if context else ""

        ref_text = f"Reference Question Paper Text:\n---\n{question_paper_text[:3000]}\n---" if question_paper_text else ""
        prompt = f"""You are an expert academic examiner grading a student's handwritten answer sheet.

{rag_info}

STEP 1 — READ THE MARKS SCHEME FROM THE PAPER:
Look at the top of each section or next to each question number for marks allocation.
Common patterns to find:
  - Section headers: "Section A (2 marks each)", "Part B — 5 marks", "Unit III [10M]"
  - Per-question marks: "Q1 [5]", "1. (3 marks)", "Q.2 (5M)", "2. 10 marks"
  - Table headers with marks columns
If no marks are written, default to 10.

STEP 2 — IDENTIFY AND GRADE EVERY QUESTION:
For EACH question the student attempted:
  - Read the marks written next to it (or inherited from section header) → this is max_marks
  - Read exactly what the student wrote → student_answer
  - Judge correctness based on your knowledge → correct_answer
  - Award marks_obtained proportional to correctness (out of the actual max_marks, NOT out of 10)

CRITICAL RULES:
  - max_marks MUST reflect what is written in the paper (e.g. 5, 10, 2, 15), NOT always 10
  - marks_obtained MUST be a plain NUMBER (e.g. 3.5), NEVER a string like "3/5" or "3 out of 5"
  - marks_obtained MUST NOT exceed max_marks
  - If a question says [10 marks], max_marks=10 and marks_obtained is between 0 and 10
  - If a question says [5 marks], max_marks=5 and marks_obtained is between 0 and 5
  - Award partial credit fairly — don't give 0 if the student wrote something relevant

---
{full_text[:5000]}
---

{ref_text}

Respond with ONLY a raw JSON array — no markdown, no code blocks, no explanation:
[
    {{
        "question_no": 1,
        "question_text": "<the question as written or inferred>",
        "correct_answer": "<ideal answer>",
        "student_answer": "<what the student wrote>",
        "matched_keywords": ["keyword1", "keyword2"],
        "marks_obtained": 7,
        "max_marks": 10,
        "feedback": "<brief constructive feedback>",
        "needs_review": false
    }},
    {{
        "question_no": 2,
        "question_text": "<question>",
        "correct_answer": "<ideal>",
        "student_answer": "<student wrote>",
        "matched_keywords": [],
        "marks_obtained": 3,
        "max_marks": 5,
        "feedback": "<feedback>",
        "needs_review": false
    }}
]"""

        try:
            completion = llm_client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional academic examiner. "
                            "ALWAYS read the marks allocation written next to each question or at the top of sections. "
                            "Use those as max_marks — do NOT assume all questions are worth 10. "
                            "marks_obtained must be a plain float <= max_marks. "
                            "Respond with ONLY a valid raw JSON array."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=1500,
            )

            response_text = completion.choices[0].message.content.strip()
            cleaned = response_text.strip()
            start = cleaned.find('[')
            end = cleaned.rfind(']')
            if start == -1 or end == -1:
                logger.warning("No JSON array found in unstructured eval response")
                return None

            raw_list = json.loads(cleaned[start:end+1])
            if not isinstance(raw_list, list):
                return None

            # Validate and clamp every result before returning
            validated = []
            for item in raw_list:
                try:
                    obtained = float(item.get("marks_obtained") or 0)
                except (ValueError, TypeError):
                    obtained = 0.0
                try:
                    max_m = float(item.get("max_marks") or 10)
                    if max_m <= 0:
                        max_m = 10.0
                except (ValueError, TypeError):
                    max_m = 10.0

                obtained = max(0.0, min(obtained, max_m))
                item["marks_obtained"] = round(obtained, 2)
                item["max_marks"] = round(max_m, 2)
                validated.append(item)
                logger.info(
                    f"  Q{item.get('question_no')}: "
                    f"{item['marks_obtained']}/{item['max_marks']} — {item.get('question_text','')[:40]}"
                )

            logger.info(f"evaluate_unstructured_document: {len(validated)} questions graded")
            return validated

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in unstructured eval: {e}")
            return None
        except Exception as e:
            logger.error(f"Unstructured evaluation failed: {e}")
            return None

    def generate_report_card(self, student_name: str, exam_name: str, results: List[Dict], total_res: Dict) -> str:
        """
        Generate a comprehensive AI report card based on performance.
        """
        if not LLM_AVAILABLE or not llm_client:
            return "AI Report Card unavailable."

        results_summary = ""
        for r in results:
            results_summary += f"Q{r.get('question_no')}: {r.get('marks_obtained')}/{r.get('max_marks')} - {r.get('feedback')}\n"

        prompt = f"""Generate a professional and encouraging student report card.
        
Student Name: {student_name}
Exam: {exam_name}
Total Score: {total_res.get('total_marks')}/{total_res.get('max_marks')} ({total_res.get('percentage')}%)
Grade: {total_res.get('grade')}

Detailed Performance:
{results_summary}

---
Task:
Write a detailed report card that includes:
1. Executive Summary: Overall performance overview.
2. Strengths: Areas where the student performed well.
3. Improvement Areas: Specific topics or skills to work on.
4. Personalized Advice: Suggestions for study habits or specific focus points.
5. Final Verdict: A concluding encouraging remark.

Keep the tone academic, professional, and supportive. Use Markdown formatting.
"""

        try:
            completion = llm_client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a supportive and professional academic counselor."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1024,
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Report card generation failed: {e}")
            return "Error generating AI report card."


# Singleton instance
llm_evaluation_service = LLMEvaluationService()
