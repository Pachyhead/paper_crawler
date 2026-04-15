import re
import os
import torch
import requests
import fitz  # PyMuPDF
from pathlib import Path
from typing import Optional
from bs4 import BeautifulSoup
from db_manager.database import engine
import pandas as pd
import requests

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    pipeline,
)
from langchain_huggingface import HuggingFacePipeline, ChatHuggingFace, HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.utilities import ArxivAPIWrapper
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


MODEL_ID    = "Qwen/Qwen3.5-9B"  # Qwen/Qwen3-30B-A3B-Instruct-2507  Qwen/Qwen3.5-9B  
EMBED_ID    = "BAAI/bge-m3"
USE_4BIT    = False
DEVICE      = "cuda" if torch.cuda.is_available() else "cpu"

def keep_after_think(text: str) -> str:
    return text.split("</think>", 1)[-1].strip()


def load_chat_model(
    model_id: str = MODEL_ID,
    use_4bit: bool = USE_4BIT,
    temperature: float = 0.3,
    max_new_tokens: int = 32768,
) -> ChatHuggingFace:
    """
    HuggingFace Instruct 모델을 로컬에서 로드.
    ChatHuggingFace가 apply_chat_template을 자동 적용함.
    """
    print(f"  🔧 모델 로딩: {model_id} (4bit={use_4bit}, device={DEVICE})")

    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    if use_4bit and DEVICE == "cuda":
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map="auto" if DEVICE == "cuda" else None,
            torch_dtype= "auto",
            trust_remote_code=True,
        )

    hf_pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        do_sample=temperature > 0,
        repetition_penalty=1.0,
        top_p=0.95, 
        top_k=20, 
        min_p=0.0,
        return_full_text=False,
        eos_token_id = [tokenizer.eos_token_id, 248044, 248046],
    )

    llm = HuggingFacePipeline(pipeline=hf_pipe)
    # ChatHuggingFace: tokenizer.apply_chat_template 자동 호출
    return ChatHuggingFace(llm=llm, verbose=False)


# ──────────────────────────────────────────────
# arXiv HTML 파서
# ──────────────────────────────────────────────

def _extract_arxiv_id(arxiv_input: str) -> str:
    match = re.search(r"(\d{4}\.\d{4,5}(?:v\d+)?)", arxiv_input)
    if match:
        return match.group(1)
    raise ValueError(f"arXiv ID 파싱 실패: {arxiv_input}")

def _get_tag_text(soup, selectors: list) -> str:
    for sel in selectors:
        tag = soup.select_one(sel)
        if tag:
            return tag.get_text(strip=True)
    return ""

def parse_arxiv_html(arxiv_input: str) -> list[Document]:
    """
    arXiv HTML 버전 파싱 (섹션 구조 + 수식 보존).
    HTML 없으면 PDF fallback.
    """
    arxiv_id = _extract_arxiv_id(arxiv_input)
    html_url = f"https://arxiv.org/html/{arxiv_id}"
    print(f"  🌐 arXiv HTML 요청: {html_url}")

    resp = requests.get(html_url, timeout=30)
    if resp.status_code != 200:
        print(f"  ⚠️  HTML 없음 → PDF fallback")
        return _arxiv_pdf_fallback(arxiv_id)

    soup = BeautifulSoup(resp.text, "html.parser")
    title   = _get_tag_text(soup, ["h1.ltx_title", ".ltx_title_document", "h1"])
    authors = _get_tag_text(soup, [".ltx_authors", ".ltx_creator"])
    meta    = {"source": html_url, "arxiv_id": arxiv_id,
               "title": title, "authors": authors, "parser": "arxiv_html"}

    documents = []

    # Abstract
    abstract_tag = soup.find("div", class_=re.compile("ltx_abstract"))
    if abstract_tag:
        documents.append(Document(
            page_content=f"[ABSTRACT]\n{abstract_tag.get_text(separator=' ', strip=True)}",
            metadata={**meta, "section": "abstract"}
        ))

    # 섹션별 추출
    sections = soup.find_all("section", class_=re.compile("ltx_section|ltx_appendix"))
    SKIP_SECTIONS = {"reference", "bibliography", "acknowledgment", "acknowledgement"}

    if sections:
        for sec in sections:
            h_tag = sec.find(re.compile("^h[1-6]$"))
            sec_title = h_tag.get_text(strip=True) if h_tag else "Unknown"

            if any(kw in sec_title.lower() for kw in SKIP_SECTIONS):
                continue

            # 수식 → LaTeX alt text 보존
            for math in sec.find_all("math"):
                alt = math.get("alttext", "")
                math.replace_with(f" $[{alt}]$ " if alt else " [FORMULA] ")

            text = sec.get_text(separator="\n", strip=True)
            if len(text) < 100:
                continue

            documents.append(Document(
                page_content=f"[SECTION: {sec_title}]\n{text}",
                metadata={**meta, "section": sec_title}
            ))
    else:
        body = soup.find("div", class_=re.compile("ltx_page_content|ltx_document"))
        if body:
            documents.append(Document(
                page_content=body.get_text(separator="\n", strip=True),
                metadata={**meta, "section": "full_body"}
            ))

    print(f"  ✅ arXiv HTML 파싱 완료: {len(documents)}개 섹션")
    return documents

def _arxiv_pdf_fallback(arxiv_id: str) -> list[Document]:
    import tempfile
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"
    resp = requests.get(pdf_url, timeout=60)
    resp.raise_for_status()
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(resp.content)
        tmp = f.name
    try:
        return load_pdf_smart(tmp)
    finally:
        os.unlink(tmp)



def load_pdf_smart(pdf_path: str) -> list[Document]:
    """2컬럼/1컬럼 자동 감지 후 올바른 읽기 순서로 텍스트 추출."""
    doc = fitz.open(pdf_path)
    documents = []

    for page_num, page in enumerate(doc):
        # blocks 원소 형식: (x0, y0, x1, y1, text, block_no, block_type, ...)
        blocks = page.get_text("blocks")
        # 텍스트 타입(block_type == 0)이고 내용이 비어 있지 않은 블록만 필터링
        text_blocks = [b for b in blocks if b[6] == 0 and b[4].strip()]
        
        if not text_blocks:
            continue
            
        blocks = page.get_text("blocks")
        
        # 페이지 중앙 x좌표 (좌/우 컬럼을 나누기 위한 기준)
        mid = page.rect.width / 2
        # 각 블록의 x 중심 좌표
        x_centers   = [(b[0] + b[2]) / 2 for b in text_blocks]
        # 중심이 mid보다 왼쪽이면 왼쪽 컬럼, 아니면 오른쪽 컬럼으로 분류
        left_blocks  = [b for b, xc in zip(text_blocks, x_centers) if xc <  mid]
        right_blocks = [b for b, xc in zip(text_blocks, x_centers) if xc >= mid]

        # 2컬럼 여부를 간단한 휴리스틱으로 판정:
        # 좌우에 최소 2개 이상의 블록이 있고
        # 오른쪽 블록 수가 왼쪽의 40% 이상이면 2컬럼으로 간주
        is_two_col = (
            len(left_blocks) >= 2 and len(right_blocks) >= 2 and
            len(right_blocks) / max(len(left_blocks), 1) > 0.4
        )

        # 2컬럼이면: 왼쪽 컬럼을 위→아래로 정렬한 뒤,
        #            오른쪽 컬럼을 위→아래로 정렬해서 이어 붙인다.
        # 1컬럼이면: 모든 블록을 y좌표 기준으로 위→아래 정렬.
        ordered = (
            sorted(left_blocks,  key=lambda b: b[1]) +
            sorted(right_blocks, key=lambda b: b[1])
            if is_two_col
            else sorted(text_blocks, key=lambda b: b[1])
        )

        # LangChain Document로 래핑하여 documents 리스트에 추가
        documents.append(Document(
            page_content="\n".join(b[4].strip() for b in ordered),
            metadata={
                "source": pdf_path, "page": page_num + 1,
                "layout": "two_column" if is_two_col else "one_column",
                "parser": "pymupdf",
            }
        ))

    doc.close()
    print(f"  ✅ PDF 파싱 완료: {len(documents)}페이지")
    return documents


def load_paper(source: str) -> list[Document]:
    """
    입력 자동 감지:
      - arXiv ID ("2401.12345") or URL  → arXiv HTML 파서
      - 로컬 PDF 경로                   → PyMuPDF 파서
    """
    is_arxiv = bool(re.search(r"\d{4}\.\d{4,5}", source)) or "arxiv.org" in source
    if is_arxiv:
        print("  🔍 arXiv 논문 감지 → HTML 파서")
        return parse_arxiv_html(source)
    else:
        print("  📄 로컬 PDF 감지 → PyMuPDF 파서")
        return load_pdf_smart(source)

####################################
#   PROMPT                         #
####################################

SUM_SYSTEM = """You are an expert research assistant specialized in analyzing and summarizing academic papers.

Your task is to read a given research paper and produce a structured, concise, and accurate summary. Focus on extracting the most important information without adding speculation or unsupported interpretations.

Always organize your response into the following sections:

1. Background, Problem, Research Objective
- Describe the context and motivation for the research.
- Identify the specific gap, limitation, or challenge in existing work that this paper addresses.
- Briefly explain why solving this problem is important.
- Clearly explain the main goal or problem the paper aims to address.

2. Key Contributions
- List the main contributions of the paper.
- Use bullet points.
- Be specific and avoid vague statements.

3. Methodology
- Describe the core approach, models, or techniques used.
- Include important details such as architectures, algorithms, or frameworks if applicable.
- Keep it concise but informative.

4. Experimental Results
- Summarize the main findings from experiments.
- Mention datasets, baselines, and key performance metrics if available.
- Highlight improvements over prior work.

5. Conclusion
- Summarize the overall takeaway of the paper.
- Include implications or potential impact if mentioned.

Guidelines:
- Be precise and avoid unnecessary verbosity.
- Do not copy sentences verbatim from the paper; paraphrase instead.
- If any section is unclear or missing in the paper, state "Not clearly specified".
- Maintain a professional and academic tone.
"""

# Agent 1: 요약 (temperature=0.2)
SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
    ("system",SUM_SYSTEM),
    ("human", """You will be given content from a research paper.

Please analyze the paper and provide a structured summary with the following sections:
- Research Objective
- Key Contributions
- Methodology
- Experimental Results
- Conclusion

IMPORTANT:
- Write the entire response in Korean.
- Use clear and professional academic Korean.

Paper content:
{paper_text}\n
"""),])

ANALYSIS_SYSTEM = """You are an expert research analyst and critical reviewer of academic papers.

Your role is NOT just to summarize, but to critically evaluate the paper’s methodology, experimental design, validity of results, limitations, positioning within prior work, and overall impact.

Produce a structured, rigorous, and objective analysis. Avoid unsupported claims and clearly distinguish between what the paper states and your critical assessment.

Organize your response into the following sections:

1. Methodological Analysis
- Evaluate the soundness of the proposed approach.
- Identify assumptions, design choices, and potential weaknesses.
- Comment on clarity, reproducibility, and technical rigor.

2. Experimental Design & Validity
- Assess whether experiments properly test the hypotheses.
- Evaluate datasets, baselines, metrics, and evaluation protocols.
- Identify potential biases, confounding variables, or missing controls.

3. Results & Evidence Strength
- Analyze whether the results convincingly support the claims.
- Distinguish between statistical significance and practical significance.
- Point out inconsistencies, overclaims, or insufficient evidence.

4. Limitations
- Identify explicit and implicit limitations of the work.
- Consider scalability, generalization, robustness, and real-world applicability.

5. Positioning within Related Work
- Analyze how the paper compares to prior work.
- Evaluate novelty and differentiation.
- Identify whether important related work is missing or overlooked.

6. Impact Assessment
- Evaluate potential academic, technical, and practical impact.
- Consider short-term vs long-term significance.
- Assess whether the contribution is incremental or substantial.

7. Overall Verdict
- Provide a balanced final assessment.
- Include strengths vs weaknesses.
- Optionally assign a score (e.g., Weak / Moderate / Strong).

Guidelines:
- Be critical but fair and evidence-based.
- Do not hallucinate missing details; if information is unclear, state "Not clearly specified".
- Use concise but precise language.
- Prefer bullet points for clarity where appropriate.
- Avoid repeating the paper’s text verbatim; paraphrase and analyze.
"""

# Agent 2: 분석 (temperature=0.3) — 전체 텍스트 직접 입력 (RAG 없음)
ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", ANALYSIS_SYSTEM),
    ("human", """You will be given content from a research paper.

Please provide a deep critical analysis covering:
- Methodological soundness
- Experimental design and validity
- Strength of evidence
- Limitations
- Positioning with respect to prior work
- Impact assessment

Focus on identifying weaknesses, assumptions, and potential issues, not just strengths.

IMPORTANT:
- Write the entire response in Korean.
- Use clear and professional academic Korean.

Paper content:
{paper_text}\n
"""),
])

IDEA_SYSTEM = """You are an expert research scientist specializing in generating high-quality future research directions and critical insights based on academic papers.

Your task is to go beyond summarization and produce thoughtful, original, and feasible research ideas grounded in the given paper.

Base your analysis strictly on the paper’s content, but extend it with logical reasoning and domain knowledge.

Organize your response into the following sections:

1. Core Insight Extraction
- Briefly identify the key ideas, assumptions, and limitations of the paper that are most relevant for future work.
- Focus only on elements that motivate further research.

2. Limitations & Gaps
- Clearly identify both explicit and implicit limitations.
- Consider methodological, experimental, theoretical, and practical gaps.

3. Future Research Directions
- Propose multiple concrete future research directions.
- Each direction should:
  - Be specific and actionable
  - Clearly explain the motivation
  - Describe what could be improved or explored
- Use bullet points.

4. Extension Opportunities
- Suggest ways to extend the work:
  - New domains, datasets, or applications
  - Scaling strategies
  - Integration with other methods or paradigms
- Be creative but realistic.

5. Ideas for Overcoming Limitations
- For each major limitation, propose possible solutions or alternative approaches.
- Include technical ideas when possible.

6. Novel Research Ideas
- Propose at least 2–3 original research ideas inspired by the paper.
- Each idea should include:
  - Problem statement
  - Proposed approach (high-level)
  - Expected contribution or impact

7. Impact & Feasibility Consideration
- Evaluate which ideas are high-risk/high-reward vs low-risk/practical.
- Briefly comment on feasibility.

Guidelines:
- Do not repeat the paper’s content unnecessarily.
- Focus on insight generation, not summarization.
- Avoid vague or generic suggestions (e.g., “improve performance”).
- Clearly distinguish between what the paper did and your proposed ideas.
- If information is missing, infer cautiously and state assumptions.
- Maintain a professional and research-oriented tone.
"""

# Agent 3: 아이디어 (temperature=0.7)
IDEA_PROMPT = ChatPromptTemplate.from_messages([
    ("system", IDEA_SYSTEM),
    ("human", """You will be given content from a research paper.

Please generate deep and well-reasoned research insights, including:
- Limitations and gaps
- Future research directions
- Extension opportunities
- Novel research ideas
- Ways to overcome limitations

Focus on producing specific, actionable, and non-trivial ideas.

IMPORTANT:
- Write the entire response in Korean.
- Use clear and professional academic Korean.

Paper content:
[Summary]\n{summary}\n\n[Analysis]\n{analysis}\n\n
"""),
])


class ResearchPaperPipeline:
    def __init__(
        self,
        source: str,                          # arXiv ID/URL 또는 로컬 PDF 경로
        llm: ChatHuggingFace,  
    ):
        print("=" * 60)
        print("🚀 Research Paper Pipeline 초기화")
        print("=" * 60)

        # ── 논문 로드
        print("\n📄 [Step 1] 논문 로딩...")
        self.documents = load_paper(source)
        self.full_text = "\n\n".join(d.page_content for d in self.documents)
        # 128K 컨텍스트 모델 기준 최대 입력 (토큰 초과 방지용 soft limit)
     #   self.safe_text = self.full_text[:24000]


        # ── 모델 로드 (temperature별 3개 인스턴스)
        print("\n🤖 [Step 3] 모델 로딩...")
     #   print("  Summary Agent  (temp=0.2)")
     #   self.summary_llm  = load_chat_model(model_id, use_4bit, temperature=0.2)
        print("Agent (temp=0.6)")
        self.analysis_llm = llm
        # print("  Idea Agent     (temp=1.0)")
        # self.idea_llm     = load_chat_model(model_id, use_4bit, temperature=1.0)

        # ── 체인 구성
        self._build_chains()

    def _build_chains(self):
        parser = StrOutputParser()

        # Agent 1: 요약
        self.summary_chain = SUMMARY_PROMPT | self.analysis_llm | parser

        # Agent 2: 분석 (전체 텍스트 직접 입력, RAG 없음)
        self.analysis_chain = ANALYSIS_PROMPT | self.analysis_llm | parser

        # Agent 3: 아이디어
        self.idea_chain = IDEA_PROMPT | self.analysis_llm | parser


    def run(self) -> dict:
        """전체 3-에이전트 파이프라인 순차 실행."""

        # Agent 1
        print("🤖 [Agent 1] 연구 요약 생성 중...")
        summary = self.summary_chain.invoke({"paper_text": self.full_text})
        print("  ✅ 완료\n")

        # Agent 2
        print("🔍 [Agent 2] 다각도 분석 중...")
        analysis = self.analysis_chain.invoke({"paper_text": self.full_text})
        print("  ✅ 완료\n")

        # Agent 3
        print("💡 [Agent 3] 연구 아이디어 생성 중...")
        ideas = self.idea_chain.invoke({"summary": summary, "analysis": analysis})
        print("  ✅ 완료\n")

        return {"summary": keep_after_think(summary), "analysis": keep_after_think(analysis), "ideas": keep_after_think(ideas)}

    def save_report(self, results: dict, output_path: str = "report.md"):
        # 저장할 경로의 상위 폴더가 없다면 자동으로 생성합니다.
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# Research Paper Analysis Report\n\n")
            f.write("## 📋 연구 요약\n\n" + results["summary"] + "\n\n")
            f.write("## 🔍 다각도 분석\n\n" + results["analysis"] + "\n\n")
            f.write("## 💡 연구 아이디어\n\n" + results["ideas"] + "\n\n")
        print(f"📁 리포트 저장: {output_path}")

    def print_report(self, results: dict):
        div = "=" * 65
        print(f"\n{div}\n📑  RESEARCH PAPER ANALYSIS REPORT\n{div}")
        for title, key in [
            ("📋 AGENT 1: 연구 요약",    "summary"),
            ("🔍 AGENT 2: 다각도 분석",  "analysis"),
            ("💡 AGENT 3: 연구 아이디어", "ideas"),
        ]:
            print(f"\n{'─'*65}\n{title}\n{'─'*65}")
            print(results[key])
        print(f"\n{div}")


def download_file(url, save_path):
    try:
        # stream=True로 설정하면 큰 파일도 청크 단위로 나누어 메모리 부담 없이 다운로드합니다.
        response = requests.get(url, stream=True)
        response.raise_for_status() # HTTP 에러(404, 500 등) 발생 시 예외를 발생시킵니다.

        # 저장할 경로의 상위 폴더가 없다면 자동으로 생성합니다.
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # 'wb' (Write Binary) 모드로 파일을 엽니다.
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk: # chunk가 비어있지 않은 경우에만 쓰기
                    file.write(chunk)
                    
        print(f"다운로드 성공: {save_path}")
        
    except requests.exceptions.RequestException as e:
        print(f"다운로드 실패: {e}")



def main_pipe():
    db = pd.read_sql("EMNLP_2025", engine)
    df1 = db[db["selected"] == 1]
    df1["title_regexed"] = df1["title"].str.replace(r'[^a-zA-Z0-9가-힣]', '', regex=True).str.lower()

    df2 = pd.read_csv("./emnlp_second_filtering_test.csv")
    df2['title_regexed'] = df2["title"].str.replace(r'[^a-zA-Z0-9가-힣]', '', regex=True).str.lower()

    result = df1[(df1['title_regexed'].isin(df2["title_regexed"]))]

    print("Finally matched: ", len(result))


    for i, row in result.iterrows():
        download_file(row['pdf_link'], f'./pdfs/{i}.pdf')

    folder_path = "./pdfs"
    report_path = "./reports"

    llm = load_chat_model(MODEL_ID, USE_4BIT, temperature=0.6)

    for i, filename in enumerate(os.listdir('./pdfs')):
        if filename.endswith('.pdf'):
            SOURCE = os.path.join(folder_path, filename) # "/home/egg2018037024/Paper_cawler/pdfs/backtobasics.pdf"
            pipe = ResearchPaperPipeline(source=SOURCE, llm=llm)

            # 전체 분석 실행
            results = pipe.run()
            #pipe.print_report(results)

            pipe.save_report(results, f"{report_path}/{i}_{filename}_report.md")