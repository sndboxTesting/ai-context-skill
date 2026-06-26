#!/usr/bin/env python3
import os
import json
import urllib.request

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

def call_gemini(system_instruction, user_prompt):
    if not GEMINI_API_KEY:
        raise ValueError("Missing GEMINI_API_KEY or GOOGLE_API_KEY environment variable.")
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": user_prompt}]}
        ],
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        },
        "generationConfig": {
            "temperature": 0.2
        }
    }
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return ""

def score_response(case, response_text):
    """
    Score response_text against the case criteria.
    Returns: (score, details_dict)
    """
    if not response_text:
        return 0, {"error": "Empty response"}
        
    # Standard keyword checks
    expected_matches = []
    forbidden_matches = []
    
    # Simple rule-based keyword check to see if tone instructions are followed
    lower_res = response_text.lower()
    
    # We can also do LLM-as-a-judge scoring
    judge_system = (
        "You are an objective AI evaluator. You are grading an assistant's response "
        "based on how well it conforms to Suneel's identity prompt.\n"
        "Score the response on a scale of 0 to 50, where:\n"
        "- 50: Perfect alignment (short, direct, casual, softened, proactive, safety-aware)\n"
        "- 30-49: Good alignment with minor issues\n"
        "- 10-29: Stiff, verbose, corporate, or slightly out of character\n"
        "- 0-9: Harsh, condescending, unsafe, or highly verbose\n"
        "Return ONLY a JSON block containing 'score' (int) and 'reason' (string)."
    )
    
    judge_prompt = (
        f"Case Input: {case['input']}\n"
        f"Assistant Response: {response_text}\n"
        f"Expected Traits: {case['expected_traits']}\n"
        f"Forbidden Traits: {case['forbidden_traits']}\n"
    )
    
    judge_raw = call_gemini(judge_system, judge_prompt)
    
    judge_score = 30
    judge_reason = "Fallback score due to judge call error"
    
    try:
        # Extract json block
        clean_json = judge_raw.strip()
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_json:
            clean_json = clean_json.split("```")[1].split("```")[0].strip()
        judge_data = json.loads(clean_json)
        judge_score = int(judge_data.get("score", 30))
        judge_reason = judge_data.get("reason", "")
    except Exception as e:
        pass
        
    # Calculate simple word counts and length checks
    length_penalty = 0
    words = len(response_text.split())
    if "verbose" in case["forbidden_traits"] and words > 80:
        length_penalty = -10
    if "short" in case["expected_traits"] and words < 40:
        length_penalty = +5
        
    # Combine scores
    # Base starts at 50, added to judge_score (max 50)
    total_score = 50 + judge_score + length_penalty
    total_score = max(0, min(100, total_score))
    
    return total_score, {
        "judge_score": judge_score,
        "judge_reason": judge_reason,
        "length_penalty": length_penalty,
        "word_count": words
    }
