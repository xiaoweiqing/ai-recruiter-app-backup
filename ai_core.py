# FILE: ai_core.py
# PURPOSE: Handles all core AI-related logic, including setting up the LLM,
# loading JDs, calling the AI for analysis, and generating final reports.

import os
import json
import traceback
import asyncio
from datetime import datetime
import shutil
import re

# --- Third-party AI and ML libraries ---
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from numpy import dot
from numpy.linalg import norm

# --- Import from our own modules ---
import config
import utils
import database

# --- Global placeholders for core components ---
llm: ChatGoogleGenerativeAI = None
EMBEDDING_MODEL: HuggingFaceEmbeddings = None
ACTIVE_JD_DATA = {}
all_session_results = []
all_comparison_results = []
session_results_lock = asyncio.Lock()
ACTIVE_COMPARISON_TASK = None
# FILE: ai_core.py (near the top, with other globals)

# --- Add these two lines ---
all_comparison_results = []
ACTIVE_COMPARISON_TASK = None

# --- [恢复到V1稳定版] PK 功能全局变量 ---
baseline_resume_text: str = ""
baseline_resume_name: str = "基准候选人"
all_pk_session_results = []
pk_session_results_lock = asyncio.Lock()
# ===================================================================================
# --- Initialization and Setup Functions ---
# ===================================================================================


# 文件: ai_core.py

# ... (其他 import 语句保持不变) ...

# ===================================================================================
# --- Initialization and Setup Functions ---
# ===================================================================================

# 文件: ai_core.py

# ... (其他的 import 保持不变) ...
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from langchain_huggingface import HuggingFaceEmbeddings
import config
import os
import traceback


# ===================================================================================
# --- Initialization and Setup Functions ---
# ===================================================================================

def setup_api_and_embedder():
    """
    【自由切换版 V3.0 - 代理修复】
    - 根据 .env 的 LLM_MODE 智能选择模型。
    - 当且仅当使用 'local' 模式时，自动清理系统代理，防止连接本地服务出错。
    """
    global llm, EMBEDDING_MODEL

    llm_mode = os.getenv('LLM_MODE', 'google').lower()
    print(f"\n>> [AI] Mode selected from .env: '{llm_mode}'")

    # 【【【 核心修复：条件性代理清理器 】】】
    # 只有当我们要连接本地模型时，才执行代理清理操作。
    if llm_mode == 'local':
        print(">> [Proxy Cleaner] Local mode detected. Temporarily removing system proxy environment variables...")
        proxies_to_clean = [
            "http_proxy", "https_proxy", "all_proxy",
            "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"
        ]
        for var in proxies_to_clean:
            if var in os.environ:
                del os.environ[var]
                print(f"   -> Removed '{var}'")

    try:
        if llm_mode == 'local':
            # --- 本地模型 API 逻辑 ---
            api_url = "http://127.0.0.1:8087/v1"
            print(f">> [AI] Connecting to LOCAL model API at [{api_url}]...")
            
            # 由于代理已被清理，这里的连接不会再受到干扰
            llm = ChatOpenAI(
                openai_api_base=api_url,
                openai_api_key="not-needed-for-local",
                model_name="local-model",
                temperature=0.1,
                max_tokens=-1,
                request_timeout=600,
            )
            
            print(">> [AI] Testing connection to local model...")
            llm.invoke("Hi")
            print(f"✅ [AI] Connection to local model successful!")

        else: # 默认或 'google' 模式
            # --- Google Gemini API 逻辑 ---
            # 在这种模式下，代理清理器没有运行，所以代理设置依然有效！
            gemini_api_key = os.getenv("API_KEY")
            if not gemini_api_key:
                raise ValueError("'API_KEY' not found in .env file for 'google' mode.")

            print(">> [AI] Connecting to Google Gemini API (via system proxy if set)...")
            genai.configure(api_key=gemini_api_key)
            safety_settings = {
                # ... (safety settings apon here as before) ...
            }
            llm = ChatGoogleGenerativeAI(
                model="models/gemini-3-flash-preview",
                temperature=0.9,
                safety_settings=safety_settings,
                google_api_key=gemini_api_key,
                request_options={"timeout": 600},
            )
            print(f"✅ [AI] Gemini API connection successful! Model: gemini-1.5-flash-latest")

    except Exception as e:
        print(f"❌ {config.Colors.RED}[AI] Fatal Error during LLM setup: {e}{config.Colors.RESET}")
        if llm_mode == 'local':
            print(f"   -> [调试提示]: 请确认你的本地模型服务正在 8087 端口运行。")
        else:
            print(f"   -> [调试提示]: 请确认你的 API_KEY 和网络代理设置正确。")
        traceback.print_exc()
        return False

    # --- Embedding 模型部分保持不变 ---
    try:
        os.environ["HF_HUB_OFFLINE"] = "1"
        model_path = "/home/weiyubin/projects/ai-recruiter-app/local_models/embeddinggemma-300m"
        print(f">> [Embedder] Loading vectorization model from local folder: '{model_path}'...")
        EMBEDDING_MODEL = HuggingFaceEmbeddings(model_name=model_path, model_kwargs={"device": "cpu"})
        print(f"✅ [Embedder] Vectorization model loaded successfully from local folder.")
    except Exception as e:
        print(f"❌ {config.Colors.RED}[Embedder] Fatal Error: {e}{config.Colors.RESET}")
        traceback.print_exc()
        return False
        
    return True


# 在 ai_core.py 文件中，替换掉旧的 load_baseline_resume 函数


# 在 ai_core.py 文件中，替换掉现有的 load_baseline_resume 函数


def load_baseline_resume():
    """
    [V1 Stable Version]
    Loads the baseline resume from a JSON file but generates a concise TEXT summary
    for the PK prompt. This is the key to comparing JSON with TXT/MD files.
    """
    global baseline_resume_text, baseline_resume_name
    print(">> [PK Init] Loading baseline resume for PK analysis...")
    try:
        config.BASELINE_DIR.mkdir(exist_ok=True)
        baseline_files = list(config.BASELINE_DIR.glob("*.json"))
        if not baseline_files:
            print(
                f"   -> {config.Colors.YELLOW}Warning: No baseline resume (.json) found. PK feature will be skipped.{config.Colors.RESET}"
            )
            return False

        baseline_file = baseline_files[0]
        with open(baseline_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # --- 智能地从JSON中拼接成一段文本摘要 ---
        text_parts = []
        if data.get("education_history") and data["education_history"]:
            edu = data["education_history"][0]
            text_parts.append(
                f"学历: {edu.get('degree', '')} 毕业于 {edu.get('institution_name', '')}"
            )
        if data.get("work_experience") and data["work_experience"]:
            exp = data["work_experience"][0]
            text_parts.append(
                f"核心经历: 在 {exp.get('company_name', '')} 担任 {exp.get('position_title', '')}"
            )
        if data.get("skills_summary") and data["skills_summary"].get(
            "technical_skills"
        ):
            skills_list = []
            for item in data["skills_summary"]["technical_skills"]:
                if isinstance(item, dict) and item.get("skills"):
                    skills_list.extend(item["skills"])
                elif isinstance(item, str):
                    skills_list.append(item)
            if skills_list:
                text_parts.append(
                    f"核心技能: {', '.join(list(dict.fromkeys(skills_list)))}"
                )

        baseline_resume_text = "\n".join(text_parts)  # <--- 我们现在生成的是文本
        baseline_resume_name = data.get("personal_info", {}).get(
            "full_name", baseline_file.stem
        )

        if not baseline_resume_text.strip():
            raise ValueError("从基准JSON生成的文本摘要为空。")

        print(
            f"   -> ✅ Baseline candidate '{baseline_resume_name}' (Text Summary) loaded successfully."
        )
        return True
    except Exception as e:
        print(
            f"   -> ❌ {config.Colors.RED}Error loading baseline resume: {e}{config.Colors.RESET}"
        )
        traceback.print_exc()
        return False


# 在 ai_core.py 文件中，替换掉旧的 execute_pk_analysis_async 函数


# 在 ai_core.py 文件中，用这个新版本替换掉旧的 execute_pk_analysis_async 函数


# 在 ai_core.py 文件中，替换掉现有的 execute_pk_analysis_async 函数


async def execute_pk_analysis_async(
    candidate_resume_text: str, candidate_name: str, loop
):
    """
    [V1 Stable Version]
    Performs a PK analysis for a single candidate using their raw resume text.
    """
    print(f"\n{'=' * 25} Stage 0: Talent PK Analysis vs. Baseline {'=' * 25}")

    if not baseline_resume_text:
        print(
            f"{config.Colors.YELLOW}>> [PK] Skipping analysis because no baseline resume was loaded.{config.Colors.RESET}"
        )
        return

    try:
        # 1. 格式化PK提示词，传入 TEXT
        pk_prompt = config.PK_PROMPT_TEMPLATE.format(
            baseline_resume_text=baseline_resume_text,
            candidate_resume_text=candidate_resume_text,
            baseline_name=baseline_resume_name,
            candidate_name=candidate_name,
        )

        # 2. 调用AI模型
        pk_response_text = await call_llm_for_analysis_async(pk_prompt, "PK-Analyst")

        # 3. 智能处理AI返回结果（可能是对象也可能是列表）
        parsed_data = utils.clean_and_parse_json(pk_response_text)

        if isinstance(parsed_data, list) and parsed_data:
            pk_data = parsed_data[0]
        else:
            pk_data = parsed_data

        if not isinstance(pk_data, dict):
            raise ValueError("Final PK data is not a valid JSON object.")

        rendered_report = utils.render_pk_report_from_json(pk_data)
        print(rendered_report)

        async with pk_session_results_lock:
            all_pk_session_results.append(pk_data)

        asyncio.create_task(database.background_pk_storage_task(pk_data, loop))

    except Exception as e:
        print(
            f"{config.Colors.RED}!! [PK Error] Failed to process PK analysis result: {e}{config.Colors.RESET}"
        )
        traceback.print_exc()


def load_and_vectorize_jds():
    """Loads and vectorizes all active Job Descriptions from the JDs_library folder."""
    global ACTIVE_JD_DATA
    print(f">> [JD] Syncing & vectorizing JDs from {config.JDS_FOLDER_PATH}")
    config.JDS_FOLDER_PATH.mkdir(exist_ok=True)
    print(
        f"{config.Colors.CYAN}>> [JD Filter] Tip: To temporarily disable a JD, add a hyphen '-' to the beginning of its filename (e.g., '-python.txt'){config.Colors.RESET}"
    )
    all_jd_files = list(config.JDS_FOLDER_PATH.glob("*.txt"))
    active_jd_files = [fp for fp in all_jd_files if not fp.name.startswith("-")]
    inactive_jd_files = [fp.name for fp in all_jd_files if fp.name.startswith("-")]
    jds = {}
    for fp in active_jd_files:
        try:
            content = fp.read_text("utf-8")
            if content.strip():
                jds[fp.stem.lstrip("-")] = {
                    "content": content,
                    "vector": EMBEDDING_MODEL.embed_query(content),
                }
            else:
                print(f" 🟡 [JD] Warning: '{fp.name}' is empty and will be skipped.")
        except Exception as e:
            print(f" ❌ [JD] Failed to process '{fp.name}': {e}")
    if not jds:
        print(
            f"{config.Colors.YELLOW}!! [JD] Warning: No active JDs found to load.{config.Colors.RESET}"
        )
    ACTIVE_JD_DATA = jds
    print(
        f"✅ [JD] Loaded and vectorized {config.Colors.BOLD}{len(jds)}{config.Colors.RESET} active JDs."
    )
    if inactive_jd_files:
        print(
            f"   -> Ignored {len(inactive_jd_files)} inactive JDs: {', '.join(inactive_jd_files)}"
        )
    return True


# FILE: ai_core.py (add this function after load_and_vectorize_jds)


# FILE: ai_core.py
# (Replace the entire load_active_comparison_task function with this one)


def load_active_comparison_task():
    """
    [CORRECTED VERSION]
    Checks for and loads the active Ultimate PK Showdown task at startup.
    Correctly identifies files starting with 'jd' and 'rs' per user specification.
    """
    global ACTIVE_COMPARISON_TASK

    import utils  # Ensure we can use the helper functions

    print(">> [Ultimate PK] Checking for active comparison task...")
    config.COMPARISON_DIR.mkdir(exist_ok=True)

    active_task_path = next(
        (
            d
            for d in config.COMPARISON_DIR.iterdir()
            if d.is_dir() and d.name != "completed_tasks"
        ),
        None,
    )

    if not active_task_path:
        print(
            f"   -> {config.Colors.CYAN}No active task found. Standard analysis mode only.{config.Colors.RESET}"
        )
        return

    print(
        f"   -> {config.Colors.MAGENTA}Active task detected: '{active_task_path.name}'{config.Colors.RESET}"
    )

    # --- THIS IS THE CORRECTED LOGIC ---
    # Look for a file starting with 'jd'
    jd_file = next((f for f in active_task_path.glob("jd*.txt")), None)
    # Look for a file starting with 'rs' OR 'benchmark'
    bench_file = next((f for f in active_task_path.glob("rs*.txt")), None) or next(
        (f for f in active_task_path.glob("benchmark*.txt")), None
    )
    # --- END OF CORRECTED LOGIC ---

    if jd_file and bench_file:
        jd_text, jd_error = utils.read_file_content(jd_file)
        benchmark_text, bench_error = utils.read_file_content(bench_file)

        if jd_text and benchmark_text:
            # Use our new helper to get the name!
            benchmark_name = utils.parse_candidate_name(bench_file.name)

            ACTIVE_COMPARISON_TASK = {
                "task_name": active_task_path.name,
                "jd_name": jd_file.name,
                "jd_text": jd_text,
                "benchmark_resume_text": benchmark_text,
                "benchmark_name": benchmark_name,  # Now uses the correctly parsed name
            }
            print(
                f"   -> ✅ {config.Colors.GREEN}Task loaded! Candidates with scores >70 will be compared against '{benchmark_name}'.{config.Colors.RESET}"
            )
        else:
            print(
                f"   -> ❌ {config.Colors.RED}Error: Could not read content from task files. PK will be disabled.{config.Colors.RESET}"
            )
    else:
        print(
            f"   -> ⚠️ {config.Colors.YELLOW}Warning: Task folder '{active_task_path.name}' is missing a required 'jd...' file or 'rs...' file.{config.Colors.RESET}"
        )


# ===================================================================================
# --- Core Analysis Functions ---
# ===================================================================================


def vector_similarity_analysis(resume_text: str):
    """Performs a quick vector similarity scan of a resume against all active JDs."""
    print("\n" + "=" * 25 + " Stage 1: Vector Similarity Quick Scan " + "=" * 25)
    if not ACTIVE_JD_DATA:
        print("No JDs loaded to compare against.")
        return {}
    resume_vector = EMBEDDING_MODEL.embed_query(resume_text)
    scores = {}
    for title, data in ACTIVE_JD_DATA.items():
        similarity = dot(resume_vector, data["vector"]) / (
            norm(resume_vector) * norm(data["vector"])
        )
        scores[title] = max(0, min(100, similarity * 100))
    sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    for title, score in sorted_scores:
        blocks = int(score / 4)
        color = (
            config.Colors.GREEN
            if score > 75
            else config.Colors.YELLOW if score > 50 else config.Colors.CYAN
        )
        print(
            f"{title:<40} | {color}{'█' * blocks}{config.Colors.RESET}{' ' * (25 - blocks)} | {score:.1f}%"
        )
    print("=" * 80)
    return {t: f"{s:.1f}%" for t, s in sorted_scores}


async def call_llm_for_analysis_async(prompt_text: str, worker_name: str) -> str:
    """
    A generic asynchronous function to call the LLM and collect the output without streaming to console.
    """
    color_map = {
        "PK-Analyst": config.Colors.CYAN,
        "JD-Matcher": config.Colors.MAGENTA,
        "Batch-Reporter": config.Colors.YELLOW,
        "Extractor": config.Colors.GREEN,
        "PK-Showdown": config.Colors.MAGENTA,
    }
    color = color_map.get(worker_name.split("-")[0], config.Colors.CYAN)
    print(
        f"\n{color}>> [{worker_name}] Requesting deep analysis from AI... Please wait.{config.Colors.RESET}"
    )
    full_response = ""
    try:
        # The 'astream' method is still good for performance, we just don't print each chunk
        async for chunk in llm.astream(prompt_text):
            content_chunk = chunk.content
            full_response += content_chunk
        print(f"{color}✅ [{worker_name}] AI analysis complete.{config.Colors.RESET}")
        return full_response
    except Exception as e:
        print(
            f"\n{config.Colors.RED}!! [Model Error during {worker_name}] {e}{config.Colors.RESET}"
        )
        return f"AI Analysis Failed: {e}"


# ===================================================================================
# --- Report Generation Function ---
# ===================================================================================


async def generate_combined_summary_report():
    """Generates the final summary reports for the session."""
    if not all_session_results:
        print(
            ">> [Report] No candidates were processed in this session. Skipping final report."
        )
        return
    run_timestamp = datetime.now()
    timestamp_str = run_timestamp.strftime("%Y-%m-%d %H:%M:%S")
    folder_timestamp_str = run_timestamp.strftime("%Y-%m-%d_%H%M%S")

    def safe_float(s):
        try:
            return float(re.sub(r"[^0-9.]", "", str(s)))
        except (ValueError, TypeError):
            return -1.0

    all_candidates_sorted = sorted(
        all_session_results, key=lambda x: safe_float(x.get("score")), reverse=True
    )
    print(
        f"\n✅ {config.Colors.BOLD}{config.Colors.GREEN}Ranking summary report generated!{config.Colors.RESET}"
    )
    print(
        f"✅ {config.Colors.BOLD}{config.Colors.GREEN}All resumes have been consolidated into one file!{config.Colors.RESET}"
    )


# 在 ai_core.py 文件的最末尾添加


# 在 ai_core.py 文件中，作为唯一的 trigger_smart_analysis_batch_async 函数


# 在 ai_core.py 文件中，用这个版本替换现有的 trigger_smart_analysis_batch_async


# 在 ai_core.py 中，用这个最终简化版替换现有的 trigger_smart_analysis_batch_async


# FILE: ai_core.py
# (Replace your entire existing trigger_smart_analysis_batch_async function with this)


# FILE: ai_core.py
# (Replace your entire existing trigger_smart_analysis_batch_async function with this)


async def trigger_smart_analysis_batch_async(batch_tasks: list, loop):
    """
    【V8.1 Type-Error-Fixed Version】
    - After the standard JD analysis, it checks the candidate's score.
    - It now safely converts the score from a string (text) to a number before comparison.
    - If score > 70 and a comparison task is active, it triggers the Ultimate PK Showdown.
    - Archives resumes to 'High_Performers' (>70) or 'Potential_Candidates' (>60) folders.
    - Saves PK results to the dedicated 'comparisons' table.
    """
    if not batch_tasks:
        return

    print(
        f"\n{'=' * 20} 🚀 Starting [Direct JD Match Analysis] for {len(batch_tasks)} resumes {'=' * 20}"
    )

    jd_input_text = "\n\n".join(
        [
            f"<jd title=\"{t}\">\n{d['content']}\n</jd>"
            for t, d in ACTIVE_JD_DATA.items()
        ]
    )
    resumes_input_parts = [
        f"<candidate id='{task['id']}'>\n{task['resume_text']}\n</candidate>"
        for task in batch_tasks
    ]
    resumes_input_text = "\n\n---\n\n".join(resumes_input_parts)
    analysis_prompt = config.PROMPT_ANALYSIS_REPORTER.format(
        jd_input=jd_input_text, resumes_input=resumes_input_text
    )

    analysis_response_text = await call_llm_for_analysis_async(
        analysis_prompt, "Batch-Reporter"
    )

    try:
        all_analyses = utils.clean_and_parse_json(analysis_response_text)
    except Exception as e:
        print(
            f"{config.Colors.RED}!! [Analysis Parsing Failed] {e}{config.Colors.RESET}"
        )
        return

    task_map = {str(task["id"]): task for task in batch_tasks}

    for analysis_json in all_analyses:
        try:
            candidate_id_str = str(analysis_json.get("candidate_id", "UNKNOWN_ID"))
            original_task = task_map.get(candidate_id_str)
            if not original_task:
                continue

            new_id = original_task["id"]
            original_filename = original_task["content"].name
            resume_text = original_task["resume_text"]
            report_body = analysis_json.get("analysis_report", {})
            verdict = report_body.get("final_verdict", {})

            # ==========================================================
            # THIS IS THE FIX. We safely convert the text score to a number.
            score_text = verdict.get("final_match_score_percent", "0")
            try:
                final_score_num = float(score_text)
            except (ValueError, TypeError):
                final_score_num = 0
            # ==========================================================

            ai_extracted_title = (
                report_body.get("title", "Unknown")
                .replace("人才价值深度分析报告: ", "")
                .strip()
            )
            candidate_name = utils.get_name_with_fallback(
                ai_name=ai_extracted_title,
                resume_text=resume_text,
                filename=original_filename,
            )

            rendered_markdown = utils.render_analysis_report_to_markdown(analysis_json)
            print(rendered_markdown)

            # ... (database storage code remains the same) ...

            safe_candidate_name = utils.sanitize_filename(candidate_name)
            final_score_str = f"{final_score_num}%"
            comparison_happened = False

            if (
                config.ENABLE_ULTIMATE_PK_SHOWDOWN
                and ACTIVE_COMPARISON_TASK
                and final_score_num >= 70
            ):
                comparison_happened = True
                print(
                    f"\n{config.Colors.MAGENTA}>> [Ultimate PK Triggered] Score ({final_score_num}%) is high. Commencing showdown...{config.Colors.RESET}"
                )
                task_info = ACTIVE_COMPARISON_TASK

                pk_prompt = config.PROMPT_CANDIDATE_COMPARISON.format(
                    job_title=task_info["task_name"],
                    jd_text=task_info["jd_text"],
                    benchmark_name=task_info["benchmark_name"],
                    benchmark_resume_text=task_info["benchmark_resume_text"],
                    new_candidate_name=candidate_name,
                    new_resume_text=resume_text,
                )

                pk_report_full = await call_llm_for_analysis_async(
                    pk_prompt, "PK-Showdown"
                )

                pk_json_data = {}
                try:
                    pk_json_data = utils.clean_and_parse_json(pk_report_full)
                except Exception as e:
                    print(f"!! [PK-Parsing Error] for '{candidate_name}': {e}")

                # --- [MODIFIED BLOCK START] ---
                # Since the live stream is disabled, we now print the Markdown part of the report manually.
                # The AI prompt for this task asks for JSON first, then a Markdown report.
                json_end_marker = "```"
                json_block_end_pos = pk_report_full.rfind(json_end_marker)
                json_block_start_pos = pk_report_full.find(json_end_marker)

                # Ensure we found a JSON block to avoid errors.
                if (
                    json_block_start_pos != -1
                    and json_block_end_pos != -1
                    and json_block_start_pos != json_block_end_pos
                ):
                    # The markdown report is everything *after* the JSON block.
                    markdown_report = pk_report_full[
                        json_block_end_pos + len(json_end_marker) :
                    ].strip()
                    # We only print if there's actual markdown content.
                    if markdown_report:
                        print(
                            f"\n{config.Colors.MAGENTA}{'=' * 20} 👑 Ultimate PK Showdown Report 👑 {'=' * 20}{config.Colors.RESET}"
                        )
                        print(markdown_report)
                        print(
                            f"{config.Colors.MAGENTA}{'=' * 78}{config.Colors.RESET}\n"
                        )
                # --- [MODIFIED BLOCK END] ---

                comparison_result_data = {
                    "task_name": f"{task_info['task_name']}_vs_{candidate_name}",
                    "jd_name": task_info["jd_name"],
                    "benchmark_name": task_info["benchmark_name"],
                    "new_candidate_name": candidate_name,
                    "benchmark_score": pk_json_data.get("benchmark_candidate_score"),
                    "new_candidate_score": pk_json_data.get("new_candidate_score"),
                    "verdict": pk_json_data.get("verdict", "N/A"),
                    "pk_report": pk_report_full,
                }

                async with session_results_lock:
                    all_comparison_results.append(comparison_result_data)
                asyncio.create_task(
                    database.background_comparison_storage_task(
                        comparison_result_data, loop
                    )
                )
                asyncio.create_task(
                    database.vectorize_and_store_comparison_async(
                        comparison_result_data, loop
                    )
                )

                print(
                    f"{config.Colors.GREEN}>> [Archive] Candidate '{candidate_name}' competed in a PK. Saving to 'PK Participants'...{config.Colors.RESET}"
                )
                dest_path = (
                    config.COMPARISON_PARTICIPANTS_DIR
                    / f"[PK]_{safe_candidate_name}_{new_id}_{final_score_str}.txt"
                )
                dest_path.write_text(resume_text, encoding="utf-8")
                print(
                    f"   -> ✅ Resume saved to: {dest_path.parent.name}/{dest_path.name}"
                )

            if not comparison_happened:
                if final_score_num >= 70:
                    print(
                        f"\n{config.Colors.GREEN}>> [Archive] Score ({final_score_num}%) >= 70. Saving as 'High Performer'...{config.Colors.RESET}"
                    )
                    dest_path = (
                        config.HIGH_PERFORMERS_DIR
                        / f"{safe_candidate_name}_{new_id}_{final_score_str}.txt"
                    )
                    dest_path.write_text(resume_text, encoding="utf-8")
                    print(
                        f"   -> ✅ Resume saved to: {dest_path.parent.name}/{dest_path.name}"
                    )

                elif final_score_num >= 60:
                    print(
                        f"\n{config.Colors.YELLOW}>> [Archive] Score ({final_score_num}%) >= 60. Saving as 'Potential Candidate'...{config.Colors.RESET}"
                    )
                    dest_path = (
                        config.POTENTIAL_CANDIDATES_DIR
                        / f"{safe_candidate_name}_{new_id}_{final_score_str}.txt"
                    )
                    dest_path.write_text(resume_text, encoding="utf-8")
                    print(
                        f"   -> ✅ Resume saved to: {dest_path.parent.name}/{dest_path.name}"
                    )

            content_path = original_task["content"]
            if content_path.exists():
                shutil.move(str(content_path), config.ARCHIVE_DIR / content_path.name)

        except Exception as e:
            print(
                f"\n{config.Colors.RED}!! [Processing Error] An unexpected error occurred while processing result for ID {candidate_id_str}: {e}{config.Colors.RESET}"
            )
            traceback.print_exc()
