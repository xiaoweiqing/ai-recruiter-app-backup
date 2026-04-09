#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===================================================================================
# AI Recruiter - On-Demand Comprehensive Report Generator v3.0
# ===================================================================================
# 功能:
# - 作为一个独立的脚本运行，用于生成最终的汇报材料。
# - 自动从 JDs_library 文件夹识别当前正在招聘的职位名称。
# - 连接到项目唯一的 talent_data.db 数据库，读取所有分析记录。
# - 对所有记录进行智能去重，只保留每个候选人得分最高的分析结果。
# - 生成一份包含【完整简历】和【AI深度分析】的精美HTML报告。
# - 生成一份包含【分数】和【人才层级评估】的Markdown排名速览。
# - 将两个报告保存在以职位名称命名的专属文件夹内。
# ===================================================================================

import sqlite3
import re
import json
from datetime import datetime
from pathlib import Path

# --- 从主程序导入共享配置和工具 ---
import config
import utils


def get_current_job_title() -> str:
    """
    智能扫描JDs_library文件夹，自动识别当前处于激活状态的职位名称。
    """
    try:
        active_jds = [
            p.stem
            for p in config.JDS_FOLDER_PATH.glob("*.txt")
            if not p.name.startswith("-")
        ]
        if not active_jds:
            return "综合职位报告"
        return " & ".join(active_jds)
    except Exception:
        return "综合职位报告"


def read_and_process_database() -> (list, int, int):
    """
    连接到数据库，读取所有记录，并执行智能去重。
    """
    db_path = config.LOCAL_DATABASE_FILE
    if not db_path.exists():
        print(
            f"❌ {config.Colors.RED}[错误] 数据库文件未找到: {db_path}{config.Colors.RESET}"
        )
        return [], 0, 0

    print(f">> 正在连接并读取数据库: {db_path.name}")
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # 读取所有需要的字段，特别是 ai_analysis
            cursor.execute(
                "SELECT candidate_name, final_match_score, raw_resume, ai_analysis FROM reports"
            )
            all_records = [dict(row) for row in cursor.fetchall()]
            print(
                f"   -> {config.Colors.GREEN}成功读取 {len(all_records)} 条总记录。{config.Colors.RESET}"
            )
    except Exception as e:
        print(
            f"❌ {config.Colors.RED}[数据库错误] 无法读取数据: {e}{config.Colors.RESET}"
        )
        return [], 0, 0

    # 智能去重逻辑
    unique_candidates = {}
    for record in all_records:
        resume_text = record.get("raw_resume", "").strip()
        if not resume_text:
            continue

        current_score = utils.safe_float(record.get("final_match_score", "0"))

        # 如果简历不存在，或者新记录的分数更高，则更新
        if resume_text not in unique_candidates or current_score > utils.safe_float(
            unique_candidates[resume_text].get("final_match_score", "0")
        ):
            unique_candidates[resume_text] = record

    final_list = list(unique_candidates.values())
    duplicates_removed = len(all_records) - len(final_list)

    # 按分数从高到低排序
    sorted_list = sorted(
        final_list,
        key=lambda x: utils.safe_float(x.get("final_match_score")),
        reverse=True,
    )

    return sorted_list, len(all_records), duplicates_removed


def format_resume_for_html(resume_text: str) -> str:
    """将纯文本简历格式化为更美观的HTML。"""
    if not isinstance(resume_text, str) or not resume_text.strip():
        return "<p><i>简历文本为空或无效。</i></p>"

    # 将换行符转换成 <br>，并包裹在 <pre> 标签中以保留格式
    escaped_text = (
        resume_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    return f'<div class="resume-text-box"><pre>{escaped_text}</pre></div>'


def format_analysis_for_html(ai_analysis_json: str) -> str:
    """将AI分析的JSON字符串转换为精美的HTML块。"""
    try:
        data = json.loads(ai_analysis_json)
        report = data.get("analysis_report", {})

        html = """
        <details class="ai-analysis-container">
            <summary>展开/折叠 AI 深度分析报告</summary>
            <div class="analysis-content">
        """

        # 逐轮分析
        html += '<div class="analysis-section rounds"><h4>📝 逐轮分析 (Round-by-Round Analysis)</h4>'
        for round_data in report.get("rounds", []):
            round_name = round_data.get("round_name", "未知回合")
            analysis = round_data.get("analysis", {})
            strengths = analysis.get("strengths", "N/A")
            gaps = analysis.get("gaps", "N/A")
            html += f"""
            <div class="round-card">
                <h5>{round_name}</h5>
                <p class="strength"><strong>匹配点:</strong> {strengths}</p>
                <p class="gap"><strong>风险点:</strong> {gaps}</p>
            </div>
            """
        html += "</div>"

        # 人才层级评估
        assessment = report.get("talent_tier_assessment", {})
        tier = assessment.get("tier", "N/A")
        justification = assessment.get("justification", "N/A")
        html += f"""
        <div class="analysis-section assessment">
            <h4>🎯 人才层级评估 (Talent Tier Assessment)</h4>
            <p><strong>人才层级:</strong> <span class="tier">{tier}</span></p>
            <p><strong>判断依据:</strong> {justification}</p>
        </div>
        """

        html += "</div></details>"
        return html
    except (json.JSONDecodeError, AttributeError):
        return "<p><i>无法渲染AI分析报告（数据格式错误）。</i></p>"


def generate_html_report(
    candidates, job_title, timestamp_str, file_path, total_count, dupe_count
):
    """生成最终的HTML报告。"""

    # 增强版声明
    disclaimer_html = f"""
    <div class="disclaimer">
        <p><strong>【【【 重要声明：保密与合规说明 】】】</strong></p>
        <p>本次分析的所有候选人简历均来源于公开招聘网站 (如 Boss直聘、猎聘等)，为公开求职 <strong>{job_title}</strong> 等相关职位的求职者。</p>
        <p>所有简历内容、分析报告及相关数据，仅供公司内部招聘和人事部门、及岗位直属领导审阅。任何非招聘相关人员，严禁以任何形式转发、复制、滥用或外泄简历信息。所有操作必须严格遵守《网络安全法》、《个人信息保护法》等相关法律法规。</p>
        <p><strong>【AI分析局限性声明】</strong></p>
        <p>AI大模型根据职位要求和候选人简历进行的严谨分析匹配，其结果只作为参考和招聘支持，不作为对候选人的定性分析。候选人简历可能存在未及时更新的客观情况，AI的判断计算也存在一定概率的偏差和幻觉，不完全正确，不作为任何录用依据，仅供内部人员参考。最终录用决策仍然依据综合面试结果。</p>
    </div>
    """

    # 增强版CSS
    html_template = f"""
    <!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>AI候选人分析报告: {job_title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #f8f9fa; color: #333; margin: 0; padding: 20px; }}
        .container {{ max-width: 960px; margin: auto; background-color: #fff; border-radius: 12px; box-shadow: 0 6px 20px rgba(0,0,0,0.07); }}
        .report-header {{ background: linear-gradient(135deg, #4A90E2, #50E3C2); color: white; padding: 30px; border-top-left-radius: 12px; border-top-right-radius: 12px; text-align: center; }}
        .report-header h1 {{ margin: 0; font-size: 28px; }}
        .report-summary {{ background-color: #f1f3f5; padding: 15px 30px; font-size: 14px; color: #555; }}
        .disclaimer {{ background-color: #fffbe6; border-left: 5px solid #ffe58f; margin: 25px; padding: 20px; font-size: 14px; line-height: 1.7; }}
        .candidate-card {{ border-top: 1px solid #e9ecef; padding: 30px; }}
        .candidate-header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 25px; }}
        .candidate-header h2 {{ margin: 0; font-size: 22px; color: #2c3e50; }}
        .score {{ background-color: #28a745; color: white; padding: 8px 16px; border-radius: 20px; font-weight: bold; }}
        .rank {{ font-size: 24px; margin-right: 15px; color: #4A90E2; }}
        .resume-text-box {{ background-color: #fdfdfd; border: 1px solid #eee; padding: 15px; border-radius: 6px; margin-bottom: 20px; }}
        .resume-text-box pre {{ white-space: pre-wrap; word-wrap: break-word; font-family: inherit; font-size: 14px; margin: 0; }}
        .ai-analysis-container summary {{ cursor: pointer; font-weight: bold; color: #4A90E2; margin-bottom: 15px; font-size: 16px; }}
        .analysis-content {{ border-left: 3px solid #50E3C2; padding-left: 20px; margin-top: 10px; }}
        .round-card {{ background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 5px; padding: 15px; margin-bottom: 10px; }}
        .strength {{ color: #218838; }} .gap {{ color: #c82333; }}
        .tier {{ font-weight: bold; background-color: #ffc107; color: #333; padding: 3px 8px; border-radius: 4px; }}
    </style></head><body><div class="container">
    <div class="report-header"><h1>所有候选人简历汇总 (按AI评分排名)</h1></div>
    <div class="report-summary">
        <p><strong>报告针对职位:</strong> {job_title}</p>
        <p><strong>报告生成时间:</strong> {timestamp_str}</p>
        <p><strong>数据统计:</strong> 本次共处理了 <strong>{total_count}</strong> 条原始记录，经智能去重后，最终有效候选人为 <strong>{len(candidates)}</strong> 名 (其中 <strong>{dupe_count}</strong> 条重复记录被移除)。</p>
    </div>
    {disclaimer_html}
    """

    for rank, candidate_data in enumerate(candidates, 1):
        name = candidate_data.get("candidate_name", "未知姓名")
        score_str = candidate_data.get("final_match_score", "N/A")
        rank_icon = {1: "👑", 2: "🥈", 3: "🥉"}.get(rank, f"#{rank}")

        # 用户要求：先简历，再分析
        resume_html = format_resume_for_html(candidate_data.get("raw_resume", ""))
        analysis_html = format_analysis_for_html(
            candidate_data.get("ai_analysis", "{}")
        )

        html_template += f"""
        <div class="candidate-card">
            <div class="candidate-header">
                <h2><span class="rank">{rank_icon}</span>{name}</h2>
                <span class="score">分数: {score_str}</span>
            </div>
            {resume_html}
            {analysis_html}
        </div>
        """

    html_template += "</div></body></html>"
    file_path.write_text(html_template, encoding="utf-8")


def generate_markdown_report(
    candidates, job_title, timestamp_str, file_path, total_count, dupe_count
):
    """生成增强版的Markdown排名报告。"""

    # 增强版声明
    disclaimer_md = f"""
> **【【【 重要声明：保密与合规说明 】】】**
> 本次分析的所有候选人简历均来源于公开招聘网站 (如 Boss直聘、猎聘等)，为公开求职 **{job_title}** 等相关职位的求职者。所有简历内容、分析报告及相关数据，仅供公司内部招聘和人事部门、及岗位直属领导审阅。任何非招聘相关人员，严禁以任何形式转发、复制、滥用或外泄简历信息。所有操作必须严格遵守《网络安全法》、《个人信息保护法》等相关法律法规。
>
> **【AI分析局限性声明】**
> AI大模型根据职位要求和候选人简历进行的严谨分析匹配，其结果只作为参考和招聘支持，不作为对候选人的定性分析。候选人简历可能存在未及时更新的客观情况，AI的判断计算也存在一定概率的偏差和幻觉，不完全正确，不作为任何录用依据，仅供内部人员参考。最终录用决策仍然依据综合面试结果。
"""

    lines = [f"# AI候选人排名速览: {job_title}\n"]
    lines.append(f"> **报告生成时间:** {timestamp_str}")
    lines.append(
        f"> **数据统计:** 从 {total_count} 条记录中去重后，有效候选人 {len(candidates)} 名。\n"
    )
    lines.append(disclaimer_md)
    lines.append("\n---\n")

    for rank, candidate in enumerate(candidates, 1):
        rank_icon = {1: "👑", 2: "🥈", 3: "🥉"}.get(rank, f"**#{rank}**")
        name = candidate.get("candidate_name", "N/A")
        score = candidate.get("final_match_score", "N/A")

        # 提取人才层级
        tier = "N/A"
        try:
            analysis_json = json.loads(candidate.get("ai_analysis", "{}"))
            tier = (
                analysis_json.get("analysis_report", {})
                .get("talent_tier_assessment", {})
                .get("tier", "N/A")
            )
        except:
            pass

        lines.append(
            f"{rank}. {rank_icon} **[分数: {score}]** **[层级: {tier}]** - {name}"
        )

    file_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("      AI Recruiter - On-Demand Report Generator")
    print("=" * 50)

    job_title = get_current_job_title()
    print(
        f"\n>> 识别到当前分析的职位为: {config.Colors.BOLD}{job_title}{config.Colors.RESET}"
    )

    candidates, total_records, duplicates_removed = read_and_process_database()

    if not candidates:
        print(
            f"{config.Colors.YELLOW}!! [警告] 数据库中没有找到有效的候选人记录。程序退出。{config.Colors.RESET}"
        )
    else:
        print(
            f"\n>> {config.Colors.BOLD}数据处理完成。去重前总记录: {total_records}，去重后有效候选人: {len(candidates)}。{config.Colors.RESET}"
        )
        print(">> 正在生成报告文件...")

        run_timestamp = datetime.now()
        timestamp_str = run_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        folder_timestamp_str = run_timestamp.strftime("%Y-%m-%d_%H%M%S")

        # 创建职位专属的报告文件夹
        safe_job_title = utils.sanitize_filename(job_title)
        report_output_dir = config.SUMMARY_REPORT_DIR / f"{safe_job_title}_分析报告"
        report_output_dir.mkdir(parents=True, exist_ok=True)
        print(f">> 报告将保存在文件夹: {report_output_dir}")

        # 生成HTML报告
        html_path = (
            report_output_dir
            / f"【完整报告】{safe_job_title}_{folder_timestamp_str}.html"
        )
        generate_html_report(
            candidates,
            job_title,
            timestamp_str,
            html_path,
            total_records,
            duplicates_removed,
        )

        # 生成Markdown报告
        md_path = (
            report_output_dir
            / f"【排名速览】{safe_job_title}_{folder_timestamp_str}.md"
        )
        generate_markdown_report(
            candidates,
            job_title,
            timestamp_str,
            md_path,
            total_records,
            duplicates_removed,
        )

        print(
            f"\n{config.Colors.GREEN}{config.Colors.BOLD}🎉 所有报告已成功生成！{config.Colors.RESET}"
        )
