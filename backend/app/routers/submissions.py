"""
Submissions router - Upload and manage answer sheet submissions.
Processing is done synchronously (no Celery/Redis required).
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import re
import logging
from datetime import datetime

from app.models.database import get_db, SessionLocal
from app.models.user import User, UserRole
from app.models.exam import Exam, AnswerKey
from app.models.submission import Submission, SubmissionStatus, ExtractedAnswer
from app.models.result import Result, TotalResult, EvaluationType
from app.schemas.schemas import SubmissionResponse
from app.utils.security import get_current_user, require_teacher
from app.config import get_settings
from app.services.ocr_service import ocr_service
from app.services.evaluation_service import evaluation_service
from app.services.llm_service import llm_evaluation_service, LLM_AVAILABLE


router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)


def get_upload_path():
    """Ensure upload directory exists and return path."""
    upload_dir = os.path.join(os.path.dirname(__file__), "..", "..", settings.UPLOAD_DIR)
    upload_dir = os.path.abspath(upload_dir)
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def parse_questions_from_text(full_text: str, num_questions: int) -> dict:
    """
    Heuristic to split OCR text into question-answer blocks.
    Supports formats like: "1. answer", "Q1. answer", "1) answer", "Q1) answer"
    """
    answers = {}
    text = full_text.replace('\r\n', '\n')
    lines = text.split('\n')
    current_q = 0
    current_text = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Match question number patterns
        match = re.match(r'^(?:Q|Ans|Answer|A)?\.?\s*(\d+)[\.\)\-\:\s]+(.*)$', line, re.IGNORECASE)
        if not match:
            match = re.match(r'^(\d+)[\.\)\-\:\s]+(.*)$', line)

        if match:
            # Save previous question
            if current_q > 0:
                answers[current_q] = '\n'.join(current_text).strip()

            current_q = int(match.group(1))
            remainder = match.group(2).strip() if match.group(2) else ''
            current_text = [remainder] if remainder else []
        else:
            if current_q > 0:
                current_text.append(line)

    # Save last question
    if current_q > 0:
        answers[current_q] = '\n'.join(current_text).strip()

    # Fallback: if no structure detected, treat whole text as Q1
    if not answers and text.strip():
        answers[1] = text.strip()

    return answers


def calculate_grade(percentage: float) -> str:
    """Calculate grade from percentage."""
    if percentage >= 90: return "A+"
    elif percentage >= 80: return "A"
    elif percentage >= 70: return "B+"
    elif percentage >= 60: return "B"
    elif percentage >= 50: return "C"
    elif percentage >= 40: return "D"
    else: return "F"


def process_submission_sync(submission_id: int):
    """
    Process a submission synchronously:
    1. Extract text (OCR / PDF text / plain text)
    2. Parse into question-answer blocks
    3. Evaluate against answer keys
    4. Store results
    """
    db: Session = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            logger.error(f"Submission {submission_id} not found")
            return

        # Update status -> PROCESSING
        submission.status = SubmissionStatus.PROCESSING.value
        db.commit()

        results = []

        # 1. Text Extraction
        try:
            full_text = ocr_service.process_submission(
                submission.file_path,
                submission.file_type
            )
        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            submission.status = SubmissionStatus.FAILED.value
            submission.error_message = str(e)
            submission.processed_at = datetime.utcnow()
            db.commit()
            return

        if not full_text or not full_text.strip():
            error_msg = "No text could be extracted from the document. Please ensure it is a clear PDF or image."
            logger.error(error_msg)
            submission.status = SubmissionStatus.FAILED.value
            submission.error_message = error_msg
            submission.processed_at = datetime.utcnow()
            db.commit()
            return


        # 2. Get exam and answer keys

        exam = db.query(Exam).filter(Exam.id == submission.exam_id).first()
        if not exam:
            logger.error("Exam not found")
            submission.status = SubmissionStatus.FAILED.value
            db.commit()
            return

        answer_keys = db.query(AnswerKey).filter(
            AnswerKey.exam_id == exam.id
        ).order_by(AnswerKey.question_no).all()

        # 3. Parse ALL answers from extracted text
        # Use a large number so parse_questions_from_text doesn't cut off
        parsed_answers = parse_questions_from_text(full_text, 9999)
        logger.info(f"Parsed {len(parsed_answers)} answers from student text")

        # Build answer key lookup dict
        ak_map = {ak.question_no: ak for ak in answer_keys}

        # Determine the full list of question numbers to evaluate
        # Use parsed answers as the source of truth — evaluate EVERY question the student answered
        all_question_nos = sorted(parsed_answers.keys())

        if not all_question_nos:
            logger.warning("No answers could be parsed from the extracted text.")
            # If we have answer keys but no parsed answers, try unstructured evaluation
            if answer_keys and LLM_AVAILABLE:
                logger.info("Attempting unstructured document evaluation via LLM")
                unstructured_results = llm_evaluation_service.evaluate_unstructured_document(exam.id, full_text)
                if unstructured_results:
                    for r_data in unstructured_results:
                        qno = r_data.get("question_no", 0)
                        max_m = r_data.get("max_marks", 10)
                        obtained = min(float(r_data.get("marks_obtained", 0)), max_m)
                        result = Result(
                            submission_id=submission.id,
                            question_no=qno,
                            marks_obtained=round(obtained, 2),
                            max_marks=max_m,
                            evaluation_type="llm",
                            auto_score=round(obtained, 2),
                            manual_score=None,
                            feedback=r_data.get("feedback", "Evaluated by AI"),
                            keywords_matched=None
                        )
                        db.add(result)
                        results.append(result)
                    db.flush()
                    total_obtained = sum(r.marks_obtained for r in results)
                    total_max = sum(r.max_marks for r in results)
                    percentage = (total_obtained / total_max * 100) if total_max > 0 else 0
                    grade = calculate_grade(percentage)
                    total_res = TotalResult(
                        submission_id=submission.id,
                        total_marks=total_obtained,
                        max_marks=total_max,
                        percentage=round(percentage, 2),
                        grade=grade,
                        is_published=1
                    )
                    db.add(total_res)
                    submission.status = SubmissionStatus.COMPLETED.value
                    submission.processed_at = datetime.utcnow()
                    db.commit()
                    logger.info(f"Unstructured eval done: {total_obtained}/{total_max} Grade: {grade}")
                    return
            submission.status = SubmissionStatus.REVIEW_REQUIRED.value
            submission.processed_at = datetime.utcnow()
            db.commit()
            return

        logger.info(f"Will evaluate question nos: {all_question_nos}")

        # 4. Store extracted answers
        extracted_full = ExtractedAnswer(
            submission_id=submission.id,
            question_no=0,
            extracted_text=full_text,
            confidence_score=0.9
        )
        db.add(extracted_full)
        for qno, text in parsed_answers.items():
            if text:
                db.add(ExtractedAnswer(
                    submission_id=submission.id,
                    question_no=qno,
                    extracted_text=text,
                    confidence_score=0.9
                ))

        # 5. Build the QA list covering ALL student questions
        qa_list = []
        for qno in all_question_nos:
            ak = ak_map.get(qno)
            qa_list.append({
                "question_no": qno,
                "question_text":  ak.question_text if ak else f"Question {qno}",
                "student_answer":  parsed_answers.get(qno, ""),
                "correct_answer":  ak.correct_answer if ak else "",  # LLM will judge without key
                "keywords":        ak.keywords if ak else [],
                "question_type":   ak.question_type if ak else "subjective",
                "max_marks":       ak.max_marks if ak else 10,
            })

        # 6. Evaluate ALL questions via chunked LLM (groups of 10)
        needs_review = False
        llm_results = None
        if LLM_AVAILABLE:
            logger.info(f"LLM evaluation of {len(qa_list)} questions (chunked by 10)")
            try:
                llm_results = llm_evaluation_service.evaluate_all_answers(exam.id, qa_list, exam.name)
                if not llm_results:
                    logger.warning("LLM returned no results — falling back to rule-based")
                else:
                    logger.info(f"LLM returned {len(llm_results)} results for {len(qa_list)} questions")
            except Exception as e:
                logger.error(f"LLM evaluation error: {e}", exc_info=True)
                llm_results = None
        else:
            logger.warning("LLM_AVAILABLE is False. Check LLM_API_KEY in .env")

        # 7. Build result records
        if llm_results and len(llm_results) == len(qa_list):
            logger.info("LLM evaluation successful — saving results")
            # Map by question_no for safety
            llm_map = {r["question_no"]: r for r in llm_results}
            for qa in qa_list:
                qno = qa["question_no"]
                ak = ak_map.get(qno)
                llm_r = llm_map.get(qno, {
                    "marks_obtained": 0,
                    "feedback": "LLM did not return a result for this question.",
                    "needs_review": True,
                    "matched_keywords": []
                })
                result = Result(
                    submission_id=submission.id,
                    question_no=qno,
                    marks_obtained=llm_r["marks_obtained"],
                    max_marks=qa["max_marks"],
                    evaluation_type="llm",
                    auto_score=llm_r["marks_obtained"],
                    manual_score=None,
                    feedback=llm_r.get("feedback", "Evaluated by AI"),
                    keywords_matched=",".join(llm_r.get("matched_keywords", [])) or None
                )
                if llm_r.get("needs_review"):
                    needs_review = True
                    result.evaluation_type = EvaluationType.HYBRID.value
                db.add(result)
                results.append(result)
        else:
            # Fallback: rule-based for questions with answer keys, 0 for others
            logger.info("Falling back to rule-based keyword evaluation")
            for qa in qa_list:
                qno = qa["question_no"]
                ak = ak_map.get(qno)
                student_text = parsed_answers.get(qno, "")
                if ak:
                    eval_result = evaluation_service.evaluate_answer(student_text, ak)
                else:
                    # No answer key — mark for manual review
                    eval_result = {
                        "marks_obtained": 0,
                        "feedback": "No answer key found for this question. Needs manual review.",
                        "evaluation_type": "manual",
                        "needs_review": True,
                        "matched_keywords": []
                    }
                result = Result(
                    submission_id=submission.id,
                    question_no=qno,
                    marks_obtained=eval_result["marks_obtained"],
                    max_marks=qa["max_marks"],
                    evaluation_type=eval_result["evaluation_type"],
                    auto_score=eval_result["marks_obtained"],
                    manual_score=None,
                    feedback=eval_result["feedback"],
                    keywords_matched=",".join(eval_result.get("matched_keywords", [])) or None
                )
                if eval_result.get("needs_review"):
                    needs_review = True
                    result.evaluation_type = EvaluationType.HYBRID.value
                db.add(result)
                results.append(result)

        db.flush()

        # 8. Calculate totals
        total_obtained = sum(r.marks_obtained for r in results)
        total_max = sum(r.max_marks for r in results)
        percentage = (total_obtained / total_max * 100) if total_max > 0 else 0
        grade = calculate_grade(percentage)

        # Create TotalResult
        total_res = TotalResult(
            submission_id=submission.id,
            total_marks=total_obtained,
            max_marks=total_max,
            percentage=round(percentage, 2),
            grade=grade,
            is_published=1
        )
        db.add(total_res)

        # 9. Update submission status
        if needs_review:
            submission.status = SubmissionStatus.REVIEW_REQUIRED.value
        else:
            submission.status = SubmissionStatus.COMPLETED.value

        submission.processed_at = datetime.utcnow()
        db.commit()

        logger.info(
            f"Submission {submission_id} processed: "
            f"{len(results)} questions, {total_obtained}/{total_max} ({percentage:.1f}%) Grade: {grade}"
        )

    except Exception as e:
        logger.error(f"Error processing submission {submission_id}: {str(e)}", exc_info=True)
        try:
            submission = db.query(Submission).filter(Submission.id == submission_id).first()
            if submission:
                submission.status = SubmissionStatus.FAILED.value
                submission.error_message = str(e)
                submission.processed_at = datetime.utcnow()
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


def get_or_create_smart_exam(db: Session) -> Exam:
    """Get the placeholder exam for direct AI evaluation or create it if missing."""
    smart_exam = db.query(Exam).filter(Exam.name == "Smart AI Evaluation").first()
    if not smart_exam:
        # We need a teacher ID for the created_by field. We'll pick any teacher or use a system ID.
        teacher = db.query(User).filter(User.role == UserRole.TEACHER).first()
        teacher_id = teacher.id if teacher else 1
        
        smart_exam = Exam(
            name="Smart AI Evaluation",
            subject="General",
            description="Automatic evaluation by AI without pre-defined answer keys.",
            created_by=teacher_id,
            is_active=1,
            total_marks=100
        )
        db.add(smart_exam)
        db.commit()
        db.refresh(smart_exam)
    return smart_exam


def process_direct_submission_sync(submission_id: int):
    """
    Direct evaluation: LLM finds questions and grades them without an answer key.
    """
    db: Session = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            return

        submission.status = SubmissionStatus.PROCESSING.value
        db.commit()

        # 1. Extraction
        try:
            full_text = ocr_service.process_submission(submission.file_path, submission.file_type)
            
            question_paper_text = None
            if submission.question_paper_path:
                logger.info(f"Extracting text from question paper: {submission.question_paper_path}")
                qp_ext = submission.question_paper_path.split(".")[-1].lower()
                question_paper_text = ocr_service.process_submission(submission.question_paper_path, qp_ext)
                
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            submission.status = SubmissionStatus.FAILED.value
            submission.error_message = str(e)
            db.commit()
            return

        if not full_text or not full_text.strip():
            error_msg = "No text could be extracted from the document. Please ensure it is a clear PDF or image."
            submission.status = SubmissionStatus.FAILED.value
            submission.error_message = error_msg
            db.commit()
            return

        # 2. LLM Evaluation
        logger.info(f"Using Direct LLM Evaluation for submission {submission_id}")
        results_data = llm_evaluation_service.evaluate_unstructured_document(submission.exam_id, full_text, question_paper_text)
        
        if not results_data:
            error_msg = "Direct LLM evaluation failed - no results. Check your LLM API Key and Base URL."
            logger.error(error_msg)
            submission.status = SubmissionStatus.FAILED.value
            submission.error_message = error_msg
            db.commit()
            return

        # 3. Save Results — with strict type casting and clamping
        db_results = []
        total_obtained = 0.0
        total_max = 0.0

        for r in results_data:
            # Safely parse marks — LLM may return strings or None
            try:
                obtained = float(r.get("marks_obtained") or 0)
            except (ValueError, TypeError):
                obtained = 0.0

            try:
                max_m = float(r.get("max_marks") or 10)
            except (ValueError, TypeError):
                max_m = 10.0

            # Clamp: marks cannot exceed max or go below 0
            obtained = max(0.0, min(obtained, max_m))

            db_res = Result(
                submission_id=submission.id,
                question_no=int(r.get("question_no") or 0),
                marks_obtained=round(obtained, 2),
                max_marks=round(max_m, 2),
                evaluation_type=EvaluationType.AUTOMATIC.value,
                feedback=str(r.get("feedback") or ""),
                keywords_matched=",".join(r.get("matched_keywords", [])) if r.get("matched_keywords") else None
            )
            db.add(db_res)
            db_results.append(db_res)
            total_obtained += obtained
            total_max += max_m
            logger.info(f"  Q{db_res.question_no}: {obtained}/{max_m}")

        # 4. Totals
        total_obtained = round(total_obtained, 2)
        total_max = round(total_max, 2)
        percentage = round((total_obtained / total_max * 100) if total_max > 0 else 0, 2)
        grade = calculate_grade(percentage)
        logger.info(f"Total: {total_obtained}/{total_max} = {percentage}% → {grade}")

        total_res = TotalResult(
            submission_id=submission.id,
            total_marks=total_obtained,
            max_marks=total_max,
            percentage=round(percentage, 2),
            grade=grade,
            is_published=1
        )
        db.add(total_res)
        db.flush()

        # 5. Generate AI Report Card
        try:
            student = db.query(User).filter(User.id == submission.student_id).first()
            exam = db.query(Exam).filter(Exam.id == submission.exam_id).first()
            
            # Convert db results to dict-like for prompt
            results_for_report = [
                {"question_no": r.question_no, "marks_obtained": r.marks_obtained, "max_marks": r.max_marks, "feedback": r.feedback}
                for r in db_results
            ]
            total_res_dict = {"total_marks": total_obtained, "max_marks": total_max, "percentage": percentage, "grade": grade}
            
            report_card = llm_evaluation_service.generate_report_card(
                student_name=student.name if student else "Student",
                exam_name=exam.name if exam else "General Exam",
                results=results_for_report,
                total_res=total_res_dict
            )
            total_res.ai_report_card = report_card
            logger.info(f"Generated AI Report Card for submission {submission_id}")
        except Exception as re:
            logger.error(f"Report card generation failed: {re}")
        
        # Save full text record too
        extracted_full = ExtractedAnswer(
            submission_id=submission.id,
            question_no=0,
            extracted_text=full_text,
            confidence_score=1.0
        )
        db.add(extracted_full)

        submission.status = SubmissionStatus.COMPLETED.value
        db.commit()
        logger.info(f"Direct evaluation completed for submission {submission_id}")

    except Exception as e:
        logger.error(f"Error in process_direct_submission_sync: {e}", exc_info=True)
        if submission:
            submission.status = SubmissionStatus.FAILED.value
            db.commit()
    finally:
        db.close()


@router.post("/direct-upload", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def upload_submission_direct(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    question_paper: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload an answer sheet for direct AI evaluation (No Exam ID required)."""
    # Validate file type
    file_ext = file.filename.split(".")[-1].lower() if file.filename else ""
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )

    # Read and check file size
    contents = await file.read()
    if len(contents) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size: {settings.MAX_FILE_SIZE_MB}MB"
        )

    # 1. Get or Create Smart Exam
    smart_exam = get_or_create_smart_exam(db)

    # 2. Save file
    upload_path = get_upload_path()
    unique_filename = f"direct_{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(upload_path, unique_filename)

    with open(file_path, "wb") as f:
        f.write(contents)

    # 3. Save Question Paper if provided
    qp_path = None
    qp_filename = None
    if question_paper:
        qp_ext = question_paper.filename.split(".")[-1].lower() if question_paper.filename else ""
        if qp_ext in settings.ALLOWED_EXTENSIONS:
            qp_contents = await question_paper.read()
            if len(qp_contents) <= settings.MAX_FILE_SIZE_MB * 1024 * 1024:
                qp_unique_filename = f"qp_{uuid.uuid4()}.{qp_ext}"
                qp_path = os.path.join(upload_path, qp_unique_filename)
                qp_filename = question_paper.filename
                with open(qp_path, "wb") as f:
                    f.write(qp_contents)

    # 4. Create submission record
    submission = Submission(
        student_id=current_user.id,
        exam_id=smart_exam.id,
        file_path=file_path,
        file_type=file_ext,
        original_filename=file.filename,
        question_paper_path=qp_path,
        question_paper_original_filename=qp_filename,
        status=SubmissionStatus.PENDING.value
    )

    db.add(submission)
    db.commit()
    db.refresh(submission)

    # 4. Process Direct Evaluation
    background_tasks.add_task(process_direct_submission_sync, submission.id)

    return submission


@router.post("/{exam_id}/upload", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def upload_submission(
    exam_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload an answer sheet for evaluation."""
    # Validate exam exists
    exam = db.query(Exam).filter(Exam.id == exam_id, Exam.is_active == 1).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Validate file type
    file_ext = file.filename.split(".")[-1].lower() if file.filename else ""
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )

    # Read and check file size
    contents = await file.read()
    if len(contents) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size: {settings.MAX_FILE_SIZE_MB}MB"
        )

    # Save file
    upload_path = get_upload_path()
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(upload_path, unique_filename)

    with open(file_path, "wb") as f:
        f.write(contents)

    # Create submission record
    submission = Submission(
        student_id=current_user.id,
        exam_id=exam_id,
        file_path=file_path,
        file_type=file_ext,
        original_filename=file.filename,
        status=SubmissionStatus.PENDING.value
    )

    db.add(submission)
    db.commit()
    db.refresh(submission)

    # Process in the background (FastAPI BackgroundTasks — no Redis needed)
    background_tasks.add_task(process_submission_sync, submission.id)

    return submission


@router.get("/", response_model=List[SubmissionResponse])
async def list_submissions(
    exam_id: int = None,
    status_filter: str = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List submissions (students see own, teachers see all)."""
    query = db.query(Submission)

    if current_user.role == UserRole.STUDENT:
        query = query.filter(Submission.student_id == current_user.id)

    if exam_id:
        query = query.filter(Submission.exam_id == exam_id)

    if status_filter:
        query = query.filter(Submission.status == status_filter)

    submissions = query.order_by(Submission.submitted_at.desc()).offset(skip).limit(limit).all()
    return submissions


@router.get("/{submission_id}", response_model=SubmissionResponse)
async def get_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get submission details."""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()

    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if current_user.role == UserRole.STUDENT and submission.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return submission


@router.post("/{submission_id}/reprocess", status_code=status.HTTP_202_ACCEPTED)
async def reprocess_submission(
    submission_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """Manually re-trigger processing for a submission (Teacher/Admin only)."""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()

    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Clear old results
    db.query(Result).filter(Result.submission_id == submission_id).delete()
    db.query(TotalResult).filter(TotalResult.submission_id == submission_id).delete()
    db.query(ExtractedAnswer).filter(ExtractedAnswer.submission_id == submission_id).delete()

    submission.status = SubmissionStatus.PENDING.value
    db.commit()

    background_tasks.add_task(process_submission_sync, submission.id)

    return {"message": "Reprocessing started", "submission_id": submission_id}
