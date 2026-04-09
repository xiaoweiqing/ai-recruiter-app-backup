# FILE: database.py
# PURPOSE: Manages all interactions with the SQLite database and the
# Qdrant vector database. Includes setup, storage, and deduplication.

import sqlite3
import traceback
import uuid
import re
import json
from datetime import datetime, timezone, timedelta

# Import global variables from our config module
from config import (
    LOCAL_DATABASE_FILE,
    QDRANT_COLLECTION_NAME,
    QDRANT_COMPARISON_COLLECTION_NAME,
    Colors,
)
import config  # Import config itself for Colors inside functions

# These are third-party libraries for vector database
try:
    from qdrant_client import QdrantClient, models

    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    print(">> [Warning] Qdrant client not found. Vectorization will be disabled.")
    print("   -> Please run: pip install qdrant-client")

# Global placeholders
QDRANT_CLIENT: QdrantClient = None
EMBEDDING_MODEL = None

# ===================================================================================
# --- SQLite Database Functions ---
# ===================================================================================


# In database.py, replace the whole function with this one


def setup_local_database():
    """
    【V5.4 Robust Version】
    Creates the database with a complete, modern schema from the start.
    This avoids all "ALTER TABLE" issues with UNIQUE constraints.
    """
    print(">> [DB] Initializing robust database setup...")
    try:
        with sqlite3.connect(LOCAL_DATABASE_FILE) as conn:
            cursor = conn.cursor()

            # --- Create the 'reports' table with the FULL, FINAL schema ---
            # By defining all columns at creation time, we avoid the ALTER TABLE error.
            print("   -> [DB] Ensuring 'reports' table has the latest structure...")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY,
                    total_id INTEGER UNIQUE,
                    candidate_name TEXT,
                    vector_score TEXT,
                    final_match_score TEXT,
                    ai_analysis TEXT,
                    raw_resume TEXT,
                    creation_time TEXT,
                    phone TEXT,
                    email TEXT,
                    status TEXT,
                    core_strengths TEXT,
                    core_gaps TEXT,
                    ai_thinking_process TEXT,
                    is_reviewed INTEGER DEFAULT 0,
                    task_type TEXT DEFAULT 'resume_analysis',
                    human_reviewed_analysis TEXT,
                    source_filename TEXT,
                    resume_hash TEXT UNIQUE,
                    full_resume_json TEXT
                )
                """
            )

            # --- Create the 'comparisons' table (no changes needed here) ---
            print("   -> [DB] Ensuring 'comparisons' table exists...")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS comparisons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, task_name TEXT, jd_name TEXT,
                    benchmark_candidate_name TEXT, new_candidate_name TEXT,
                    benchmark_candidate_score INTEGER, new_candidate_score INTEGER, verdict TEXT,
                    full_pk_report TEXT, full_jd_match_report TEXT, creation_time TEXT
                )
                """
            )
            # --- [这是您需要添加的部分] ---
            # --- 在这里添加新表的创建代码 ---
            print("   -> [DB] Ensuring 'pk_reports' table exists for PK analysis...")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS pk_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    baseline_name TEXT, 
                    candidate_name TEXT, 
                    report_text TEXT, 
                    report_json TEXT,
                    creation_time TEXT
                )"""
            )
        print(f"✅ [DB] Database '{LOCAL_DATABASE_FILE.name}' is correctly configured.")
        return True
    except Exception as e:
        print(f"❌ [DB] FATAL ERROR during database setup: {e}")
        traceback.print_exc()
        return False


def deduplicate_database_resumes():
    # This function is correct and does not need changes.
    print(">> [DB Dedupe] Starting database deduplication check...")
    try:
        with sqlite3.connect(LOCAL_DATABASE_FILE) as conn:
            cursor = conn.cursor()
            query = """
            SELECT raw_resume, COUNT(*), MAX(id)
            FROM reports WHERE raw_resume IS NOT NULL AND raw_resume != ''
            GROUP BY raw_resume HAVING COUNT(*) > 1
            """
            duplicates = cursor.execute(query).fetchall()
            if not duplicates:
                print("   -> ✅ No duplicate resumes found. Database is clean.")
                return
            # ... rest of the function is correct
            print(
                f"   -> Found {len(duplicates)} sets of duplicate resumes. Cleaning up..."
            )
            total_deleted = 0
            for resume_text, count, max_id in duplicates:
                delete_cursor = conn.cursor()
                delete_cursor.execute(
                    "DELETE FROM reports WHERE raw_resume = ? AND id < ?",
                    (resume_text, max_id),
                )
                total_deleted += delete_cursor.rowcount
            print(
                f"   -> ✅ Successfully deleted {total_deleted} old duplicate entries."
            )

    except Exception as e:
        print(f"❌ [DB Dedupe] An error occurred during deduplication: {e}")


def get_current_max_total_id():
    # This function is correct and does not need changes.
    try:
        with sqlite3.connect(LOCAL_DATABASE_FILE) as conn:
            res = (
                conn.cursor().execute("SELECT MAX(total_id) FROM reports").fetchone()[0]
            )
            return res or 0
    except Exception:
        return 0


async def background_storage_task(
    new_id,
    filename,
    resume_hash,
    raw_resume,
    full_resume_json,
    analysis_json,
    name,
    phone,
    email,
    status,
    vector_score,
    final_score,
    strengths,
    gaps,
    thinking_process,
):
    """
    【V5.3 Corrected Merge Version】
    Saves ALL data, including both original columns and new JSON columns, into the database.
    """
    try:
        with sqlite3.connect(LOCAL_DATABASE_FILE) as conn:
            # ✨✨✨ [CORRECT] The parameter list and SQL statement now include ALL fields ✨✨✨
            params = (
                new_id,
                name,
                vector_score,
                final_score,
                analysis_json,  # This goes into the 'ai_analysis' column
                raw_resume,
                datetime.now(timezone(timedelta(hours=8))).isoformat(),
                phone,
                email,
                status,
                strengths,
                gaps,
                thinking_process,
                filename,
                resume_hash,
                full_resume_json,
            )
            # This INSERT statement maps every parameter to its correct column
            conn.execute(
                """
                INSERT INTO reports (
                    total_id, candidate_name, vector_score, final_match_score, ai_analysis,
                    raw_resume, creation_time, phone, email, status,
                    core_strengths, core_gaps, ai_thinking_process,
                    source_filename, resume_hash, full_resume_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                params,
            )
            print(
                f" > [Sync] Report ID {new_id} ({name}) with all data saved to SQLite."
            )
    except Exception as e:
        print(f"!! [Sync Error] SQLite write failed for ID {new_id}: {e}")
        traceback.print_exc()


# ... (The rest of the database.py file, including setup_qdrant and vectorization functions, remains unchanged) ...
# 在 database.py 文件中，用这个最终版本替换现有的 setup_qdrant 函数


def setup_qdrant(embedding_model_instance, os_environ):
    # This function is correct and does not need changes.
    global QDRANT_CLIENT, EMBEDDING_MODEL
    EMBEDDING_MODEL = embedding_model_instance
    if not QDRANT_AVAILABLE:
        return
    print(
        f"{Colors.MAGENTA}{Colors.BOLD}>>> Executing Qdrant Connection Diagnostic v2...{Colors.RESET}"
    )
    original_proxies = {
        k: os_environ.pop(k, None)
        for k in list(os_environ.keys())
        if k.lower().endswith("_proxy")
    }
    if original_proxies:
        print(
            f"    -> [Diagnostic] Temporarily removed proxy env vars: {', '.join(original_proxies.keys())}"
        )
    else:
        print("    -> [Diagnostic] No proxy environment variables found to remove.")
    try:
        print(">> [Qdrant] Connecting to local Qdrant service (localhost:6333)...")
        QDRANT_CLIENT = QdrantClient(host="localhost", port=6333)
        collections = QDRANT_CLIENT.get_collections().collections
        collection_names = [c.name for c in collections]
        test_vector = EMBEDDING_MODEL.embed_query("test")
        vector_size = len(test_vector)

        # --- 原有的创建 resumes collection 的代码 ---
        if QDRANT_COLLECTION_NAME not in collection_names:
            print(
                f">> [Qdrant] Collection '{QDRANT_COLLECTION_NAME}' not found, creating..."
            )
            QDRANT_CLIENT.create_collection(
                collection_name=QDRANT_COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=vector_size, distance=models.Distance.COSINE
                ),
            )

        # --- 原有的创建 comparisons collection 的代码 ---
        if QDRANT_COMPARISON_COLLECTION_NAME not in collection_names:
            print(
                f">> [Qdrant] Collection '{QDRANT_COMPARISON_COLLECTION_NAME}' not found, creating..."
            )
            QDRANT_CLIENT.create_collection(
                collection_name=QDRANT_COMPARISON_COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=vector_size, distance=models.Distance.COSINE
                ),
            )

        # --- [这是新增的、用于创建 PK reports collection 的代码] ---
        if config.PK_QDRANT_COLLECTION not in collection_names:
            print(
                f">> [Qdrant] Collection '{config.PK_QDRANT_COLLECTION}' not found, creating..."
            )
            QDRANT_CLIENT.create_collection(
                collection_name=config.PK_QDRANT_COLLECTION,
                vectors_config=models.VectorParams(
                    size=vector_size, distance=models.Distance.COSINE
                ),
            )
        # --- [新增代码结束] ---

        resume_count = QDRANT_CLIENT.count(
            collection_name=QDRANT_COLLECTION_NAME, exact=True
        ).count
        comparison_count = QDRANT_CLIENT.count(
            collection_name=QDRANT_COMPARISON_COLLECTION_NAME, exact=True
        ).count
        # 我们也打印一下新collection的数量
        pk_report_count = QDRANT_CLIENT.count(
            collection_name=config.PK_QDRANT_COLLECTION, exact=True
        ).count

        print("✅ [Qdrant] Connection successful.")
        print(
            f"   -> Resumes Collection: '{QDRANT_COLLECTION_NAME}' ({resume_count} vectors)"
        )
        print(
            f"   -> Comparisons Collection: '{QDRANT_COMPARISON_COLLECTION_NAME}' ({comparison_count} vectors)"
        )
        # 打印新collection的信息
        print(
            f"   -> PK Reports Collection: '{config.PK_QDRANT_COLLECTION}' ({pk_report_count} vectors)"
        )

    except Exception as e:
        print(f"❌ [Qdrant] FATAL ERROR: Could not connect to Qdrant. {e}")
        QDRANT_CLIENT = None
    finally:
        for key, value in original_proxies.items():
            if value:
                os_environ[key] = value
        if original_proxies:
            print("    -> [Diagnostic] Restored proxy environment variables.")


async def vectorize_and_store_resume_async(candidate_id, name, resume_text, loop):
    # This function is correct and does not need changes.
    if not QDRANT_CLIENT or not resume_text or not EMBEDDING_MODEL:
        return
    try:
        vector = await loop.run_in_executor(
            None, EMBEDDING_MODEL.embed_query, resume_text
        )
        point_id = str(uuid.uuid4())
        upsert_op = lambda: QDRANT_CLIENT.upsert(
            collection_name=QDRANT_COLLECTION_NAME,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "candidate_id": candidate_id,
                        "candidate_name": name,
                        "text_snippet": resume_text[:500],
                    },
                )
            ],
            wait=True,
        )
        await loop.run_in_executor(None, upsert_op)
        print(
            f" > [Qdrant Sync] ID {candidate_id} ({name}) resume vectorized and saved."
        )
    except Exception as e:
        print(f"!! [Qdrant Sync Error] Failed to vectorize for ID {candidate_id}: {e}")


async def background_pk_storage_task(pk_data_dict: dict, loop):
    """【后台任务】将PK报告同时存入文本文件、SQLite数据库和Qdrant向量库。"""
    try:
        # 动态导入 utils 避免循环依赖
        import utils

        report_md = utils.render_pk_report_from_json(pk_data_dict)
        report_json_str = json.dumps(pk_data_dict, ensure_ascii=False, indent=2)

        report_info = pk_data_dict.get("talent_pk_report", {})
        title = report_info.get("title", "")

        b_name_match = re.search(r":\s*(.*?)\s*vs\.", title)
        b_name = b_name_match.group(1).strip() if b_name_match else "基准"
        c_name_match = re.search(r"vs\.\s*(.*)", title)
        c_name = c_name_match.group(1).strip() if c_name_match else "候选人"

        # 1. 保存为 TXT 文件
        config.PK_REPORTS_DIR.mkdir(exist_ok=True)
        filename = f"PK报告_{utils.sanitize_filename(b_name)}_vs_{utils.sanitize_filename(c_name)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        (config.PK_REPORTS_DIR / filename).write_text(report_md, encoding="utf-8")

        # 2. 存入 SQLite
        def _sync_sqlite_write():
            with sqlite3.connect(LOCAL_DATABASE_FILE) as conn:
                conn.execute(
                    "INSERT INTO pk_reports (baseline_name, candidate_name, report_text, report_json, creation_time) VALUES (?, ?, ?, ?, ?)",
                    (
                        b_name,
                        c_name,
                        report_md,
                        report_json_str,
                        datetime.now().isoformat(),
                    ),
                )

        await loop.run_in_executor(None, _sync_sqlite_write)
        print(f" > [PK Sync] PK Report for '{c_name}' saved to SQLite.")

        # 3. 存入 Qdrant (如果已启用)
        if QDRANT_CLIENT and EMBEDDING_MODEL:
            vector = await loop.run_in_executor(
                None, EMBEDDING_MODEL.embed_query, report_md
            )
            point_id = str(uuid.uuid4())
            upsert_op = lambda: QDRANT_CLIENT.upsert(
                collection_name=config.PK_QDRANT_COLLECTION,
                points=[
                    models.PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={
                            "baseline_name": b_name,
                            "candidate_name": c_name,
                            "report_snippet": report_md[:500],
                            "timestamp": datetime.now().isoformat(),
                        },
                    )
                ],
                wait=True,
            )
            await loop.run_in_executor(None, upsert_op)
            print(f" > [PK Qdrant Sync] PK Report for '{c_name}' vectorized and saved.")

    except Exception as e:
        print(f"!! [PK Sync Error] Failed to save PK report: {e}")
        traceback.print_exc()
