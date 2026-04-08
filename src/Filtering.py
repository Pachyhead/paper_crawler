import torch
import pandas as pd
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from tqdm import tqdm
import re
import time
import json
import json
import re
from typing import List, Dict
from db_manager.database import engine, Engine, text
from config import PROJECT_ROOT

def read_table(table_name: str):
    df = pd.read_sql(table_name, con=engine)

    return df

def extract_json_array(text: str) -> List[Dict]:
    """
    Extract the first valid JSON array (list of objects) from model output.
    """
    # 가장 바깥 JSON array만 잡기 (object 포함)
    match = re.search(
        r"\[\s*(?:\{.*?\}\s*,?\s*)*\]",
        text,
        re.DOTALL
    )

    if not match:
        raise ValueError("No JSON array found in model output")

    try:
        return json.loads(match.group())
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON extracted: {e}")

def normalize_results(items: List[Dict]) -> List[Dict]:
    """
    Validate and normalize parsed results.
    """
    titles = []
    matched = []
    reasons = []

    for item in items:
        if not isinstance(item, dict):
            continue

        title = item.get("title")
        keywords = item.get("matched_keywords", [])
        reason = item.get("reason", "")

        if not isinstance(title, str):
            continue

        if not isinstance(keywords, list):
            keywords = []

        keywords = [kw for kw in keywords if isinstance(kw, str)]

        if not isinstance(reason, str):
            reason = ""

        titles.append(title.strip())
        matched.append(keywords)
        reasons.append(reason.strip())

    return titles, matched, reasons


def filter_titles():

    start = time.perf_counter()


    model_id = "Qwen/Qwen3-4B-Instruct-2507"   #  openai/gpt-oss-20b,  "Qwen/Qwen2.5-7B-Instruct"  Qwen/Qwen2.5-32B-Instruct, 
    
    pipe = pipeline(
        "text-generation",
        model=model_id,
        torch_dtype="auto",
        device_map="auto",
        trust_remote_code=True,
    )

    SYSTEM_PROMPT = """
    You are a strict and careful research assistant.
    Your job is to filter research paper titles.
    You must follow the user's instructions exactly.
    Output MUST be a valid JSON array of strings.
    Do not include explanations, comments, or any extra text.
    If no title matches, output an empty JSON array: [].
    """

    USER_PROMPT = """
    You are given a list of research paper titles from a recent conference and a set of target keyword(s).

    Select ONLY the paper titles that satisfy BOTH of the following conditions:

    1) Keyword relevance:
    - The title is relevant to the given keyword(s).
    - Relevance includes synonyms and conceptually related research topics.

    2) NLP relevance:
    - The paper is clearly within the field of Natural Language Processing (NLP).
    - This includes language modeling and LLMs.
    - Multimodal or general ML papers are allowed ONLY if language is the primary focus.

    Exclusion rules:
    - Exclude titles unrelated to the keyword(s).
    - Exclude vision-only, speech-only, robotics, or recommendation papers.
    - Exclude multimodal papers where language is not the central contribution.

    Keyword(s):
    {KEYWORDS}

    Paper Titles:
    {TITLES}

    Output:
    Return ONLY a JSON array.
    Each item MUST include:
    - "title": the paper title
    - "matched_keywords": keywords that caused the match
    - "reason": a SHORT explanation (one sentence or phrase) of why the title matches the keywords

    Do NOT include any extra text.

    Example:
    [
    {{
        "title": "Example Paper Title",
        "matched_keywords": ["LoRA", "Efficient Tuning"],
        "reason": "Proposes a parameter-efficient fine-tuning method for large language models"
    }},
    {{
        "title": "Another Example Paper",
        "matched_keywords": ["Alignment"],
        "reason": "Studies alignment objectives for controlling LLM behavior"
    }}
    ]
    """

    KEYWORDS = "Personality, Alignment, reasoning"

    full_titles_df = read_table(table_name="EMNLP_2025")  # 추후 수정 필요
    print(full_titles_df.head())

    title_list = full_titles_df.title.to_list()

    finds_title= []
    finds_key = []
    finds_reason = []

    for i in tqdm(range(0, len(title_list), 1000)):
        print("Now i == : ", i)
        chunk_titles = title_list[i:i+1000]
        titles_str = "\n".join(chunk_titles)

        user_input = USER_PROMPT.format(KEYWORDS= KEYWORDS, TITLES=titles_str)

        messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
        ]
        
        outputs = pipe(
            messages,
            max_new_tokens= 8192,  # 8192
            temperature = 0.7,
        )
        
        raw_text = outputs[0]["generated_text"][-1]['content']
        parsed = extract_json_array(raw_text)
        mid_title, mid_key, mid_reason = normalize_results(parsed)

        finds_title.extend(mid_title)
        finds_key.extend(mid_key)
        finds_reason.extend(mid_reason)

    time.sleep(1) # 1초 대기

    end = time.perf_counter()
    print(f"소요 시간: {end - start:.5f}초")

    print("Matched Paper: ", len(list(set(finds_title))))


    result_csv = pd.DataFrame({'title': finds_title, 
                            'key': finds_key,
                            'reason': finds_reason
                            })

    result_csv.to_csv("./emnlp_first_filtering_test.csv")

    return finds_title

    # Qwen/Qwen3-30B-A3B-Instruct-2507, 228; 15분
    # "Qwen/Qwen2.5-7B-Instruct" , 76; 3분
    # "Qwen/Qwen2.5-32B-Instruct", 12; 1분