# FILE: utils.py
# PURPOSE: Contains general-purpose helper functions for file handling,
# text cleaning, JSON parsing, and notifications.

import json
import re
import sys
import unicodedata
import subprocess
from pathlib import Path
import traceback
import config

# These are third-party libraries.
try:
    import fitz  # PyMuPDF
    import docx  # python-docx
    from json_repair import repair_json
except ImportError as e:
    print(
        f"❌ Core dependency missing: {e}. Please run: pip install PyMuPDF python-docx json-repair"
    )
    sys.exit(1)


# --- [THIS IS THE NEW FUNCTION THAT WAS MISSING] ---
def safe_float(s: str) -> float:
    """
    Safely extracts a floating-point number from a string that might contain non-numeric characters like '%'.
    Returns -1.0 if conversion fails, which helps in sorting invalid entries to the bottom.
    """
    try:
        # Removes any character that is not a digit or a period.
        s_cleaned = re.sub(r"[^0-9.]", "", str(s))
        if not s_cleaned:
            return -1.0
        return float(s_cleaned)
    except (ValueError, TypeError):
        return -1.0


# --- [END OF NEW FUNCTION] ---


def clean_json_string_for_parsing(s: str) -> str:
    """
    Removes illegal control characters from a string that might cause JSON parsing to fail.
    Only allows legitimate whitespace like newline, carriage return, and tab.
    """
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", s)


def safe_extract_value(text_block: str, key: str) -> str:
    """
    [Core Fault-Tolerant Tool] Safely extracts a value for a given key from a text block using regex.
    Succeeds even if the JSON structure is broken, as long as the "key": "value" format exists locally.
    """
    pattern = re.compile(
        f"[\"']?{key}[\"']?"
        + r"\s*:\s*"
        + r"(\"(.*?)\"|'([^']*)'|(\d[\d\.\s]*)|(true|false|null))",
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(text_block)
    if match:
        value = match.group(2) or match.group(3) or match.group(4) or match.group(5)
        if value is not None:
            return value.strip().replace("\\n", "\n").replace('\\"', '"')
    return "N/A"


def clean_and_parse_json(ai_response_text: str):
    """
    [V5 Robust Edition]
    This version is simpler and more robust. It finds the first and last braces/brackets
    to isolate the JSON block, then uses the json_repair library.
    This avoids complex regex and handles cases where the AI forgets the markdown ``` markers.
    """
    # 查找JSON对象或数组的起始位置
    start_pos = -1
    first_brace = ai_response_text.find("{")
    first_bracket = ai_response_text.find("[")

    if first_brace == -1 and first_bracket == -1:
        raise json.JSONDecodeError(
            "No JSON object or array found in the AI response.", ai_response_text, 0
        )

    if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
        start_pos = first_brace
        end_char = "}"
    else:
        start_pos = first_bracket
        end_char = "]"

    # 查找最后一个对应的结束符号
    end_pos = ai_response_text.rfind(end_char)
    if end_pos == -1:
        raise json.JSONDecodeError(
            f"JSON structure is incomplete. Started with '{ai_response_text[start_pos]}' but found no closing '{end_char}'.",
            ai_response_text,
            start_pos,
        )

    # 提取JSON字符串
    json_str = ai_response_text[start_pos : end_pos + 1]

    try:
        # 使用强大的json_repair库来修复并解析
        return json.loads(repair_json(json_str))
    except Exception as e:
        print(
            f"   !! [JSON Repair Failed] Content is severely damaged, even json_repair could not fix it."
        )
        # 抛出更详细的错误，以便调试
        raise json.JSONDecodeError(
            f"Error after expert repair: {e}. Attempted to parse: '{json_str[:200]}...'",
            ai_response_text,
            0,
        )


def clean_text(text: str) -> str:
    """Normalizes and cleans a string by removing extra whitespace."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text or "")).strip()


def read_file_content(file_path):
    """
    【V4.3 Robust Read Edition】
    Reads file content with enhanced checks and clearer error messages.
    Differentiates between zero-byte files and whitespace-only files.
    """
    try:
        p = Path(file_path)
        if not p.exists():
            return None, f"File does not exist: {p.name}"

        if p.stat().st_size == 0:
            return None, f"File '{p.name}' is a zero-byte empty file"

        ext = p.suffix.lower()

        content = ""
        if ext in [".txt", ".md", ".markdown"]:
            encodings_to_try = ["utf-8-sig", "utf-8", "gbk", "gb18030"]
            for encoding in encodings_to_try:
                try:
                    raw_content = p.read_text(encoding)
                    if raw_content:
                        content = raw_content
                        break
                except (UnicodeDecodeError, TypeError):
                    continue
            if not content:
                return None, f"Failed to decode '{p.name}' with any tried encoding"

        elif ext == ".pdf":
            with fitz.open(p) as doc:
                content = "".join(page.get_text() for page in doc)

        elif ext == ".docx":
            doc = docx.Document(p)
            content = "\n".join([para.text for para in doc.paragraphs])

        else:
            return None, f"Unsupported file type: '{p.name}'"

        stripped_content = content.strip()
        if not stripped_content:
            return None, f"File '{p.name}' contains only whitespace characters"

        return stripped_content, None

    except Exception as e:
        return None, f"An unknown error occurred while reading '{file_path}': {e}"


def sanitize_filename(name: str) -> str:
    """Removes or replaces illegal characters from a string to make it a safe filename."""
    if not isinstance(name, str):
        name = str(name)
    name = name.replace("/", "_").replace("\\", "_")
    return re.sub(r'[*:?"<>|]', "", name).strip()


def render_analysis_report_to_markdown(report_json: dict) -> str:
    """
    [CORRECTED & ENHANCED VERSION]
    Renders the AI analysis JSON into beautiful command-line markdown.
    - Safely converts score to a number.
    - Adds the new "Hard Requirements Check" section.
    - Adds the final score at the bottom for convenience.
    """
    try:
        report = report_json.get("analysis_report", {})
        if not report:
            return "❌ 报告JSON结构不正确，未找到 'analysis_report' 顶级键。"

        title = report.get("title", "人才价值深度分析报告")
        verdict = report.get("final_verdict", {})

        # Safely convert the text score to a number.
        score_text = verdict.get("final_match_score_percent", "0")
        try:
            score = float(score_text)
        except (ValueError, TypeError):
            score = 0

        lines = [f"\n{config.Colors.CYAN}{'=' * 70}{config.Colors.RESET}"]
        lines.append(
            f"{config.Colors.BOLD}{config.Colors.CYAN}{title.center(80)}{config.Colors.RESET}"
        )
        lines.append(f"{config.Colors.CYAN}{'=' * 70}{config.Colors.RESET}")

        score_color = (
            config.Colors.GREEN
            if score >= 80
            else config.Colors.YELLOW if score >= 60 else config.Colors.RED
        )
        lines.append(
            f"\n{config.Colors.MAGENTA}{'--- 🏆 最终裁决 (Final Verdict) 🏆 ---':^80}{config.Colors.RESET}"
        )
        lines.append(
            f"  - **【最终匹配度】**: {score_color}{config.Colors.BOLD}{score}%{config.Colors.RESET}"
        )
        lines.append(f"  - **【一句话总结】**: {verdict.get('verdict_summary', 'N/A')}")

        # --- NEW: Render Hard Requirements Check ---
        hard_req_check = report.get("hard_requirements_check", {})
        met_reqs = hard_req_check.get("met_requirements", [])
        unmet_reqs = hard_req_check.get("unmet_requirements", [])

        if met_reqs or unmet_reqs:
            lines.append(
                f"\n{config.Colors.MAGENTA}{'--- 🚨 硬性要求审查 (Hard Requirements) 🚨 ---':^80}{config.Colors.RESET}"
            )
            for req in met_reqs:
                lines.append(
                    f"  - {config.Colors.GREEN}✅ 符合{config.Colors.RESET}: {req.get('requirement_text', 'N/A')}"
                )
                lines.append(
                    f"    {config.Colors.CYAN}  └ 简历证据: {req.get('evidence_from_resume', '无')}{config.Colors.RESET}"
                )
            for req in unmet_reqs:
                lines.append(
                    f"  - {config.Colors.RED}❌ 不符{config.Colors.RESET}: {req.get('requirement_text', 'N/A')}"
                )
                lines.append(
                    f"    {config.Colors.YELLOW}  └ 缺失分析: {req.get('reasoning_for_mismatch', '无')}{config.Colors.RESET}"
                )
        # --- END OF NEW SECTION ---

        for round_data in report.get("rounds", []):
            round_score = round_data.get("score", 0)
            round_max_score = round_data.get("max_score", 10)
            lines.append(
                f"\n--- [ {config.Colors.BOLD}{round_data.get('round_name', '')} ] ---"
            )
            lines.append(f"  - **【本轮评分】**: {round_score} / {round_max_score}")
            analysis = round_data.get("analysis", {})
            lines.append(
                f"  - {config.Colors.GREEN}【匹配点分析】{config.Colors.RESET}: {analysis.get('strengths', 'N/A')}"
            )
            lines.append(
                f"  - {config.Colors.YELLOW}【风险点分析】{config.Colors.RESET}: {analysis.get('gaps', 'N/A')}"
            )

        assessment = report.get("talent_tier_assessment", {})
        tier = assessment.get("tier", "评估失败")
        justification = assessment.get("justification", "N/A")

        lines.append(
            f"\n{config.Colors.MAGENTA}{'--- 🎯 人才层级评估 (Talent Tier Assessment) 🎯 ---':^80}{config.Colors.RESET}"
        )
        lines.append(
            f"  - **【人才层级】**: {config.Colors.BOLD}{config.Colors.YELLOW}{tier}{config.Colors.RESET}"
        )
        lines.append(f"  - **【判断依据】**: {justification}")
        # --- NEW: Add final score at the bottom for convenience ---
        lines.append(
            f"  - **【最终匹配分数】**: {score_color}{config.Colors.BOLD}{score}%{config.Colors.RESET}"
        )
        # --- END OF NEW LINE ---

        lines.append(f"\n{config.Colors.CYAN}{'=' * 70}{config.Colors.RESET}\n")
        return "\n".join(lines)

    except Exception as e:
        traceback.print_exc()
        return f"❌ 渲染分析报告时出错: {e}"


def get_name_with_fallback(ai_name: str, resume_text: str, filename: str = None) -> str:
    """
    Intelligently extracts the candidate's name with multiple fallbacks.
    1. Tries the name provided by the AI.
    2. If that fails, checks if the first character of the resume is a Chinese surname.
    3. If that fails, tries to extract a name from the filename.
    4. Final fallback is a generic message.
    """
    # 1. Try the AI-extracted name first.
    if ai_name and ai_name.lower() not in ["unknown", "n/a", "", "姓名未知"]:
        # Handles cases like "姜**" by removing the asterisks
        return ai_name.replace("*", "").strip()

    # 2. Fallback: Use the first character of the resume if it's a Chinese character.
    if resume_text and "\u4e00" <= resume_text <= "\u9fff":
        surname = resume_text
        return f"{surname}先生/女士"

    # 3. Fallback: Try to parse the filename.
    if filename:
        # Extracts the first block of Chinese characters from the filename
        match = re.match(r"^[\u4e00-\u9fa5]+", Path(filename).stem)
        if match:
            name_from_file = match.group(0)
            return f"{name_from_file.replace('*','')}先生/女士"

    # 4. If all else fails.
    return "姓名无法识别"


def render_pk_report_from_json(report_data: dict) -> str:
    """将AI生成的PK报告JSON，渲染成美观的、带颜色的命令行文本。"""
    try:
        report = report_data.get("talent_pk_report", {})
        if not report:
            return f"❌ {config.Colors.RED}PK报告JSON结构不正确 (缺少 'talent_pk_report' 键)。{config.Colors.RESET}"

        title = report.get("title", "人才价值PK擂台")
        final_verdict = report.get("final_verdict", {})
        winner = final_verdict.get("overall_winner", "")
        debrief = report.get("personal_strategic_debrief_for_you", {})

        # 从标题中稳健地提取名字
        your_name_match = re.search(r":\s*(.*?)\s*vs\.", title)
        your_name = your_name_match.group(1).strip() if your_name_match else "你"
        candidate_name_match = re.search(r"vs\.\s*(.*)", title)
        candidate_name = (
            candidate_name_match.group(1).strip() if candidate_name_match else "候选人"
        )

        lines = [f"\n{config.Colors.MAGENTA}{'=' * 70}{config.Colors.RESET}"]
        lines.append(
            f"{config.Colors.BOLD}{config.Colors.MAGENTA}{title.center(80)}{config.Colors.RESET}"
        )
        lines.append(f"{config.Colors.MAGENTA}{'=' * 70}{config.Colors.RESET}")

        # 渲染每个回合
        for round_data in report.get("rounds", []):
            round_winner = round_data.get("winner", "")
            your_score = round_data.get("your_score", 0)
            candidate_score = round_data.get("candidate_score", 0)
            lines.append(
                f"\n--- [ {config.Colors.BOLD}{round_data.get('round_name', '')} ] ---"
            )
            lines.append(
                f"  - 【评分】: {your_name}: {your_score}/10 | {candidate_name}: {candidate_score}/10"
            )

            winner_line = f"  - 【本回合胜者】: {round_winner}"
            if your_name in round_winner:
                winner_line = f"  - 【本回合胜者】: {config.Colors.GREEN}{round_winner}{config.Colors.RESET}"
            elif candidate_name in round_winner:
                winner_line = f"  - 【本回合胜者】: {config.Colors.YELLOW}{round_winner}{config.Colors.RESET}"
            lines.append(winner_line)

            analysis = round_data.get("analysis", {})
            lines.append(
                f"  - {config.Colors.GREEN}【胜者分析】{config.Colors.RESET}: {analysis.get('winner_strengths', 'N/A')}"
            )
            lines.append(
                f"  - {config.Colors.YELLOW}【败者分析】{config.Colors.RESET}: {analysis.get('loser_weaknesses', 'N/A')}"
            )

        # 渲染最终裁决
        lines.append(
            f"\n{config.Colors.CYAN}{'-' * 30} 🏆 最终裁决 🏆 {'-' * 30}{config.Colors.RESET}"
        )
        winner_display = winner
        if your_name in winner:
            winner_display = f"{config.Colors.BOLD}{config.Colors.GREEN}{winner} (胜利){config.Colors.RESET}"
        elif candidate_name in winner:
            winner_display = f"{config.Colors.BOLD}{config.Colors.RED}{winner} (惜败){config.Colors.RESET}"
        lines.append(f"【综合胜出者】: {winner_display}")
        lines.append(f"【裁决概要】: {final_verdict.get('verdict_summary', 'N/A')}")

        # 渲染个人战略简报
        lines.append(
            f"\n{config.Colors.CYAN}{'=' * 25} 📈 机密个人战略简报 📈 {'=' * 25}{config.Colors.RESET}"
        )
        if candidate_name in winner and "IF_YOU_LOST" in debrief:
            lost_data = debrief["IF_YOU_LOST"]
            action_plan = lost_data.get("high_roi_action_plan", {})
            enhancements = action_plan.get("key_capability_enhancements", [])
            lines.append(
                f"\n{config.Colors.BOLD}{config.Colors.RED}🎯【直面现实的残酷真相】{config.Colors.RESET}\n   {lost_data.get('brutal_truth', 'N/A')}"
            )
            lines.append(
                f"\n{config.Colors.BOLD}{config.Colors.YELLOW}🚀【高ROI价值提升行动计划】{config.Colors.RESET}"
            )
            lines.append(
                f"   - **首要项目目标**: {action_plan.get('primary_project_objective', 'N/A')}"
            )
            for item in enhancements:
                lines.append(f"   - **关键能力强化**: {item}")
            lines.append(
                f"   - **市场定位重塑**: {action_plan.get('strategic_repositioning', 'N/A')}"
            )
        elif your_name in winner and "IF_YOU_WON" in debrief:
            won_data = debrief["IF_YOU_WON"]
            lines.append(
                f"\n{config.Colors.BOLD}{config.Colors.GREEN}👑【你的核心竞争壁垒 (Alpha)】{config.Colors.RESET}\n   {won_data.get('analysis_of_your_alpha', 'N/A')}"
            )
            lines.append(
                f"\n{config.Colors.BOLD}{config.Colors.CYAN}⚡【扩大优势的下一步战略】{config.Colors.RESET}\n   {won_data.get('how_to_achieve_dominant_lead', 'N/A')}"
            )
        else:
            lines.append(
                "   (未生成个人战略简报，请检查AI返回的JSON结构或胜者姓名是否匹配)"
            )

        lines.append(f"\n{config.Colors.MAGENTA}{'=' * 70}{config.Colors.RESET}\n")
        return "\n".join(lines)

    except Exception as e:
        traceback.print_exc()
        return f"❌ 渲染PK报告JSON时发生严重错误: {e}\n\n{config.Colors.YELLOW}原始数据:{config.Colors.RESET}\n {json.dumps(report_data, ensure_ascii=False, indent=2)}"


def parse_candidate_name(filename: str) -> str:
    """
    Extracts a candidate's name from a benchmark resume filename.
    Handles prefixes like 'rs' and suffixes like '基准模型简历'.
    Example: 'rs周翔基准模型简历.txt' -> '周翔'
    """
    # Get the filename without the extension (e.g., 'rs周翔基准模型简历')
    base = Path(filename).stem

    # Remove the known prefixes and suffixes
    name = (
        base.replace("rs", "")
        .replace("benchmark", "")
        .replace("基准模型简历", "")
        .strip()
    )

    # Clean up any remaining separators and return the name
    return name.replace("_", " ").strip()
