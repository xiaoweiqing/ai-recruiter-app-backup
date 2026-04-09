# FILE: main.py
# PURPOSE: Main entry point for the AI Recruiter application.
# This script initializes all components and starts the services.

import os
import threading
import time
from pathlib import Path

# --- Import from our own modules ---
import ai_core
import api_server
import config
import database
import utils
import json  # <--- 这是需要添加的关键一行
import shutil  # <--- 最好也检查并添加这一行


# FILE: main.py
# (Replace your existing create_required_directories function with this)


def create_required_directories():
    """Ensures that all necessary folders for the application exist."""
    print(">> [Init] Verifying application directory structure...")
    dirs_to_create = [
        config.IPC_DIR,
        config.INBOX_DIR,
        config.ARCHIVE_DIR,
        config.JDS_FOLDER_PATH,
        config.HIGH_PERFORMERS_DIR,
        config.POTENTIAL_CANDIDATES_DIR,
        config.RANKED_RESUMES_DIR,
        config.SUMMARY_REPORT_DIR,
        # --- [THIS IS THE NEW LINE YOU NEED TO ADD] ---
        config.COMPARISON_PARTICIPANTS_DIR,  # The folder for Ultimate PK participants
        config.PK_REPORTS_DIR,  # The folder for personal PK reports
        config.BASELINE_DIR,  # The folder for your personal baseline
        config.COMPARISON_DIR,  # The folder for PK tasks
    ]
    for dir_path in dirs_to_create:
        dir_path.mkdir(exist_ok=True)
    print("   -> ✅ All required directories are in place.")


# 在 main.py 文件中，用下面这个版本完整替换旧的 main_async_logic 函数


# 在 main.py 文件中，这是最终版本的 main_async_logic 函数


# 在 main.py 文件中，这是最终、完美的 main_async_logic 函数


# (这是完整的、最终的函数，请用它替换掉您文件里旧的整个函数)


# (这是 main.py 的最终版本，请用它完整替换旧函数)


# 在 main.py 文件中，用这个稳定版函数完整替换掉现有的 main_async_logic


# 在 main.py 文件中，用这个稳定版函数完整替换掉现有的 main_async_logic


async def main_async_logic():
    """
    [V1 Stable Workflow - Final Fix]
    The core loop runs a stable "PK first, then JD analysis" process.
    """
    print(
        f"\n{config.Colors.BOLD}>> [Core] AI Recruiter is now running (Stable Workflow).{config.Colors.RESET}"
    )
    print(
        f"{config.Colors.YELLOW}   -> Watching for new resumes in: {config.INBOX_DIR}{config.Colors.RESET}"
    )

    current_id = database.get_current_max_total_id() + 1

    try:
        while True:
            inbox_files = [
                p
                for p in config.INBOX_DIR.iterdir()
                if p.is_file()
                and not p.name.startswith(("-", "."))
                and p.suffix.lower() in [".txt", ".md", ".pdf", ".docx"]
            ]

            if inbox_files:
                print(
                    f"\n{config.Colors.GREEN}>> [Inbox] Detected {len(inbox_files)} new resume(s). Starting processing...{config.Colors.RESET}"
                )

                loop = asyncio.get_running_loop()

                batch_tasks_for_jd_analysis = []

                for file_path in inbox_files:
                    print(
                        f"\n{config.Colors.CYAN}{'─' * 30} Processing: {file_path.name} {'─' * 30}{config.Colors.RESET}"
                    )

                    resume_text, error_msg = utils.read_file_content(file_path)

                    if error_msg or not resume_text:
                        print(
                            f"{config.Colors.RED}   -> Skipping {file_path.name}: {error_msg}{config.Colors.RESET}"
                        )
                        try:
                            shutil.move(
                                str(file_path), config.ARCHIVE_DIR / file_path.name
                            )
                        except Exception:
                            pass
                        continue

                    # 第一步：执行PK分析
                    candidate_name_temp = file_path.stem
                    await ai_core.execute_pk_analysis_async(
                        resume_text, candidate_name_temp, loop
                    )

                    # --- [这是修复后的代码块] ---
                    # 第二步：准备JD匹配任务，把文本也传进去
                    task_data = {
                        "id": current_id,
                        "content": file_path,
                        "resume_text": resume_text,  # <--- 关键的修复
                    }
                    batch_tasks_for_jd_analysis.append(task_data)
                    current_id += 1

                if batch_tasks_for_jd_analysis:
                    # 确保调用的是未优化的稳定版函数
                    await ai_core.trigger_smart_analysis_batch_async(
                        batch_tasks_for_jd_analysis, loop
                    )
                    await ai_core.generate_combined_summary_report()

                print(
                    f"\n{config.Colors.BOLD}>> [Core] Batch processing complete. Resuming watch...{config.Colors.RESET}"
                )
                print(
                    f"{config.Colors.YELLOW}   -> Watching for new resumes in: {config.INBOX_DIR}{config.Colors.RESET}"
                )

            await asyncio.sleep(5)

    except KeyboardInterrupt:
        print("\n>> [Core] Shutdown signal received. Exiting gracefully.")
    except Exception as e:
        print(
            f"\n{config.Colors.RED}!! [Core] A fatal error occurred in the main loop: {e}{config.Colors.RESET}"
        )
        import traceback

        traceback.print_exc()


# FILE: main.py

if __name__ == "__main__":
    # This block is the actual entry point of the application.
    # If you run `python main.py`, the code inside this block will execute.

    print("\n" + "=" * 50)
    print("      AI Recruiter v33.1 - Application Starting")
    print("=" * 50)

    # --- Step 1: Synchronous Setup ---
    create_required_directories()

    if not database.setup_local_database():
        print(
            f"{config.Colors.RED}Halting: Database setup failed.{config.Colors.RESET}"
        )
        exit(1)

    if not ai_core.setup_api_and_embedder():
        print(
            f"{config.Colors.RED}Halting: AI model setup failed.{config.Colors.RESET}"
        )
        exit(1)

    database.setup_qdrant(ai_core.EMBEDDING_MODEL, os.environ)
    # This is for your personal Stage 1 PK
    ai_core.load_baseline_resume()
    # This loads the Job Descriptions for Stage 2
    ai_core.load_and_vectorize_jds()

    # --- [THIS IS THE NEW LINE YOU NEED TO ADD] ---
    # This loads the Ultimate PK task for Stage 3
    ai_core.load_active_comparison_task()
    # --- [END OF NEW LINE] ---

    database.deduplicate_database_resumes()

    # --- Step 2: Start the FastAPI server in a separate thread ---
    api_thread = threading.Thread(target=api_server.run_api_server, daemon=True)
    api_thread.start()

    # Give the server a moment to start up before the main loop begins
    time.sleep(2)

    # --- Step 3: Start the main asynchronous event loop ---
    import asyncio

    try:
        asyncio.run(main_async_logic())
    except KeyboardInterrupt:
        print("\n>> [Main] Application shutting down.")
