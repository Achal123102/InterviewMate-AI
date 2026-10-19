import os
import json
import urllib.request
import urllib.error
import re

DEFAULT_GEMINI_KEY = "AQ.Ab8RN6KOEutFnKFOjTNbdG3en-xl1ofEPyMJUwMZZhJcgZTIxw"

def get_api_key():
    return os.environ.get("GEMINI_API_KEY", "").strip()

def call_gemini(prompt, system_instruction=None, json_mode=True, model=None):
    api_key = get_api_key()
    if not api_key:
        return None

    # Preferred models in order of capability & availability
    models_to_try = [model] if model else ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-flash-latest"]
    
    for m in models_to_try:
        if not m:
            continue
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
        
        contents = []
        if system_instruction:
            contents.append({
                "role": "user",
                "parts": [{"text": f"SYSTEM INSTRUCTION: {system_instruction}"}]
            })
            contents.append({
                "role": "model",
                "parts": [{"text": "Understood. I will strictly adhere to these instructions."}]
            })
        
        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })

        payload = {"contents": contents}
        if json_mode:
            payload["generationConfig"] = {
                "responseMimeType": "application/json",
                "temperature": 0.3
            }
        else:
            payload["generationConfig"] = {
                "temperature": 0.3
            }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=25.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                candidates = data.get("candidates", [])
                if candidates and "content" in candidates[0] and "parts" in candidates[0]["content"]:
                    text = candidates[0]["content"]["parts"][0]["text"]
                    return text
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            print(f"Gemini API ({m}) HTTP {e.code}: {err_body[:200]}")
            continue
        except Exception as exc:
            print(f"Gemini API ({m}) error: {exc}")
            continue

    return None

def gemini_evaluate_answer(question, answer, interview_type, role):
    """
    Evaluate candidate's mock interview answer using Gemini.
    """
    if not answer or not answer.strip():
        return None
        
    prompt = f"""Evaluate this mock interview answer fairly and constructively.
Role: {role}
Interview Type: {interview_type}
Question: {question}
Answer: {answer[:4000]}

Return ONLY a JSON object with:
- "score": integer 0-100
- "technical_score": integer 0-100
- "communication_score": integer 0-100
- "confidence_indicator": integer 0-100
- "feedback": 2-3 sentences of clear, constructive feedback
- "missed_points": string or list summarizing key points that could be improved or added
- "suggested_answer": an exemplary, well-structured answer explaining the concept, reasoning, and practical example"""

    sys_inst = "You are an expert interview coach and senior technical interviewer. Return clean, valid JSON only."
    raw = call_gemini(prompt, system_instruction=sys_inst, json_mode=True)
    if not raw:
        return None

    try:
        clean_text = raw.strip()
        if clean_text.startswith("```"):
            clean_text = re.sub(r"^```(?:json)?\s*", "", clean_text)
            clean_text = re.sub(r"\s*```$", "", clean_text)
        data = json.loads(clean_text)
        
        # Format missed_points cleanly as string if array
        if isinstance(data.get("missed_points"), list):
            data["missed_points"] = "; ".join(str(p) for p in data["missed_points"])
        else:
            data["missed_points"] = str(data.get("missed_points", ""))

        for key in ["score", "technical_score", "communication_score", "confidence_indicator"]:
            data[key] = max(0, min(100, int(data.get(key, 50))))
        return data
    except Exception as exc:
        print("Error parsing Gemini evaluation response:", exc)
        return None

def gemini_generate_questions(interview_type, answer_mode, role, difficulty, resume_text, detected_skills, job_description, used_questions):
    """
    Generate questions using Gemini:
    - 2-3 Resume-based questions (tailored to skills/projects on resume)
    - 2-3 Role-based questions (tailored to target role)
    - Anti-repetition against previous questions
    """

    used_sample = list(used_questions)[:30]
    used_clause = ""
    if used_sample:
        used_clause = f"CRITICAL: The candidate has ALREADY been asked the following questions in past sessions. DO NOT repeat or closely rephrase any of these: {json.dumps(used_sample)}"

    has_resume = bool(detected_skills or (resume_text and resume_text.strip()))
    
    if has_resume:
        structure = (
            "You MUST create exactly 5 interview questions divided as follows:\n"
            "- Exactly 2 or 3 questions MUST BE STRICTLY RESUME-BASED (evaluating specific skills, tools, and projects mentioned in the candidate's resume). For each, set 'category': 'resume' and 'badge': 'Resume: <Skill/Project>'.\n"
            "- Exactly 2 or 3 questions MUST BE STRICTLY ROLE-BASED (evaluating core competencies and practical responsibilities of the target job role). For each, set 'category': 'role' and 'badge': 'Role: <Role>'.\n"
        )
    else:
        structure = (
            f"You MUST create exactly 5 practical questions STRICTLY ROLE-BASED for the target role '{role}'. "
            f"For all questions, set 'category': 'role' and 'badge': 'Role: {role}'.\n"
        )

    mode_rule = (
        "For MCQ: Return JSON array of 5 objects. Each object MUST have: "
        "'question' (string), 'options' (array of exactly 4 plausible strings), 'correct_index' (integer 0-3), 'topic' (string), 'explanation' (string explaining why correct), 'category' ('resume' or 'role'), 'badge' (string).\n"
        "For Written: Return JSON array of 5 objects. Each object MUST have: "
        "'question' (string), 'options': [], 'correct_index': null, 'topic' (string), 'explanation': '', 'category' ('resume' or 'role'), 'badge' (string)."
    )

    prompt = f"""Target Role: {role}
Interview Type: {interview_type}
Difficulty: {difficulty}
Answer Mode: {answer_mode}
Detected Resume Skills: {', '.join(detected_skills) if detected_skills else 'None'}
Resume Text: {resume_text[:4000]}
Job Description: {job_description[:2000]}

{structure}
{used_clause}
{mode_rule}

Return ONLY a valid JSON array of 5 question objects."""

    sys_inst = "You are a professional technical recruiter and engineering leader. Return valid JSON only."
    raw = call_gemini(prompt, system_instruction=sys_inst, json_mode=True)
    if not raw:
        return None

    try:
        clean_text = raw.strip()
        if clean_text.startswith("```"):
            clean_text = re.sub(r"^```(?:json)?\s*", "", clean_text)
            clean_text = re.sub(r"\s*```$", "", clean_text)
        result = json.loads(clean_text)
        if not isinstance(result, list):
            return None

        clean = []
        for item in result:
            if not isinstance(item, dict) or not item.get("question"):
                continue
            q_text = str(item["question"])[:1000]
            cat = str(item.get("category", "role"))
            badge = str(item.get("badge", f"{cat.capitalize()}: {role}"))

            if answer_mode == "MCQ":
                opts = item.get("options", [])
                c_idx = item.get("correct_index")
                if len(opts) != 4 or not isinstance(c_idx, int) or c_idx not in range(4):
                    continue
                clean.append({
                    "question": q_text,
                    "options": [str(o)[:300] for o in opts],
                    "correct_index": c_idx,
                    "topic": str(item.get("topic", interview_type))[:100],
                    "explanation": str(item.get("explanation", ""))[:600],
                    "category": cat,
                    "badge": badge
                })
            else:
                clean.append({
                    "question": q_text,
                    "options": [],
                    "correct_index": None,
                    "topic": str(item.get("topic", interview_type))[:100],
                    "explanation": "",
                    "category": cat,
                    "badge": badge
                })
        return clean if len(clean) >= 4 else None
    except Exception as exc:
        print("Error parsing Gemini question generation:", exc)
        return None
