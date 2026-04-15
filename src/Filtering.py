import torch
import pandas as pd
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from tqdm import tqdm
import re
import time
import json
import re
from typing import List, Dict
from db_manager.database import engine, Engine, text
from config import PROJECT_ROOT

def read_table(table_name: str):
    df = pd.read_sql(table_name, con=engine)

    return df

def keep_after_think(text: str) -> str:
    return text.split("</think>", 1)[-1].strip()

def extract_json_array(text: str) -> List[Dict]:
    """
    Extract the first valid JSON array from model output using JSONDecoder.
    """
    decoder = json.JSONDecoder()
    start_idx = 0

    text = keep_after_think(text)

    while True:
        # 여는 대괄호 '[' 의 위치를 찾음
        start_idx = text.find('[', start_idx)
        if start_idx == -1:
            raise ValueError("No JSON array found in model output")

        try:
            # raw_decode는 파싱된 객체와, 파싱이 끝난 문자열의 인덱스를 반환
            obj, _ = decoder.raw_decode(text[start_idx:])
            
            # 파싱된 결과가 리스트(배열)인지 확인
            if isinstance(obj, list):
                return obj
            else:
                # 리스트가 아니라면 다음 '[' 부터 다시 탐색
                start_idx += 1
                continue
                
        except json.JSONDecodeError:
            # 유효한 JSON이 아니라면 다음 '[' 위치부터 다시 탐색
            start_idx += 1
            continue

    raise ValueError("Valid JSON array could not be extracted.")

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


def filter_titles(is_first = True):

    start = time.perf_counter()


    model_id = "Qwen/Qwen3.5-4B"   #  openai/gpt-oss-20b,  "Qwen/Qwen2.5-7B-Instruct"  Qwen/Qwen2.5-32B-Instruct, 

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    
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

    if is_first:
        full_titles_df = read_table(table_name="EMNLP_2025")  # 추후 수정 필요

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
            {"role": "user", "content": user_input + " /no_think"},
            ]

        
            outputs = pipe(
                messages,
                max_new_tokens= 131072,  # 8192
                temperature=0.7, 
                top_p=0.8, 
                min_p=0.0, 
                repetition_penalty=1.0,
                top_k = 20,
                tokenizer_encode_kwargs   = {"enable_thinking": False},
                eos_token_id = [tokenizer.eos_token_id, 248044, 248046],
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
    
    else:
        full_titles_df = read_table(table_name="EMNLP_2025")  # 추후 수정 필요

        mask = full_titles_df['selected'] == 1
        selected_df = full_titles_df[mask] # 수집이 완료된 행만 추려냅니다.
        selected_df['T+A'] = selected_df['title'] + ' ' + selected_df['abstract']

        finds_title= []
        finds_key = []
        finds_reason = []

        for i in tqdm(range(0, len(selected_df), 50)):
            print("Now i == : ", i)
            chunk_df = selected_df[i:i+10]
            chunk_list = chunk_df['T+A'].to_list()

            titles_str = "\n".join(chunk_list)

            user_input = USER_PROMPT.format(KEYWORDS= KEYWORDS, TITLES=titles_str)

            messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
            ]
            
            outputs = pipe(
                messages,
                max_new_tokens= 131072,  # 8192
                temperature=1.0, 
                top_p=0.95, 
                min_p=0.0, 
                repetition_penalty=1.0,
                top_k = 20,
                tokenizer_encode_kwargs   = {"enable_thinking": True},
                eos_token_id = [tokenizer.eos_token_id, 248044, 248046],
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

        result_csv.to_csv("./emnlp_second_filtering_test.csv")

        torch.cuda.empty_cache()
        del(pipe)

        return finds_title

