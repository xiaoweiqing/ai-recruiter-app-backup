# FILE: config.py
# PURPOSE: Holds all configurations, paths, prompts, and global constants.

import os
from pathlib import Path
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()


# --- 全局配置与类 ---
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"


# --- Directory and File Paths ---
# Get the directory where this config file is located
PROJECT_ROOT_DIR = Path(__file__).resolve().parent

# Application-specific folders
IPC_DIR = PROJECT_ROOT_DIR / "AI_Recruiter_IPC"
INBOX_DIR = IPC_DIR / "inbox"
ARCHIVE_DIR = IPC_DIR / "archive"
JDS_FOLDER_PATH = PROJECT_ROOT_DIR / "JDs_library"
HIGH_PERFORMERS_DIR = PROJECT_ROOT_DIR / "绩优候选人简历"
COMPARISON_PARTICIPANTS_DIR = PROJECT_ROOT_DIR / "参与对比的候选人简历"
POTENTIAL_CANDIDATES_DIR = PROJECT_ROOT_DIR / "潜力候选人简历"
RANKED_RESUMES_DIR = PROJECT_ROOT_DIR / "已分析简历存档"
SUMMARY_REPORT_DIR = PROJECT_ROOT_DIR / "所有汇总报告"

# In config.py

# --- Directory and File Paths ---
PROJECT_ROOT_DIR = Path(__file__).resolve().parent
# ... other paths ...

# [CHANGE THIS LINE]
# The new database file, located directly in the project's main folder
LOCAL_DATABASE_FILE = PROJECT_ROOT_DIR / "talent_data.db"

# --- Qdrant Configuration ---
QDRANT_COLLECTION_NAME = "ai_recruiter_v33_resumes"
QDRANT_COMPARISON_COLLECTION_NAME = "ai_recruiter_v33_comparisons"

# --- AI Prompt Templates ---
# FILE: config.py

# ... (keep all other prompts and configurations as they are) ...

# FILE: config.py

# ... (keep all other prompts and configurations as they are) ...

# ❗️ THIS IS THE CORRECTED VARIABLE NAME ❗️
# FILE: config.py
# ... (keep all other configurations and prompts as they are) ...

# [REPLACE THE OLD PROMPT WITH THIS NEW, MORE DYNAMIC VERSION]
# FILE: config.py

# ... (other prompts remain the same) ...

PROMPT_ANALYSIS_REPORTER = """
# 角色
你是一位极其苛刻、一针见血的顶级人才战略分析师。你的核心任务是，将候选人简历与职位要求(JD)进行逐点审查，并对候选人的行业层级做出最终判断。

# 核心分析流程 (必须严格遵守)
1.  **识别核心要求**: 从JD中识别出3-5个最关键的硬性要求，作为分析回合的主题。
2.  **逐点对决**: 针对每一个核心要求，生成一个独立的分析回合(round)。
3.  **层级评估**: 基于所有分析，对候选人进行层级评估，必须从提供的选项中选择一个。
4.  **强制JSON数组输出**: 你的最终输出必须是且仅是一个JSON数组。

# 职位要求 (JOB DESCRIPTIONS):
<job_descriptions>
{jd_input}
</job_descriptions>

# 候选人简历 (CANDIDATE RESUMES):
<resumes>
{resumes_input}
</resumes>

# 你的输出格式 (严格遵循此JSON结构，移除所有面试建议):
```json
[
  {{
    "candidate_id": "必须与输入XML标签中的ID完全一致",
    "analysis_report": {{
      "title": "人才价值深度分析报告: [请从简历中提取并填写候选人姓名]",
      "analysis_timestamp": "YYYY-MM-DDTHH:MM:SSZ",
      "final_verdict": {{
        "final_match_score_percent": "综合所有回合后，计算得出的最终匹配度分数(0-100的数字)",
        "verdict_summary": "一句话总结这位候选人是否值得推荐，以及核心理由。"
      }},
      "rounds": [
        {{
          "round_name": "【JD核心要求1】: [此处填写你识别出的第一个JD核心要求]",
          "score": 0, "max_score": 10,
          "analysis": {{
            "strengths": "【基于简历，分析候选人在这项核心要求上的匹配点和证据】",
            "gaps": "【基于简历，分析候选人在这项核心要求上的缺失点或风险】"
          }}
        }}
      ],
      "talent_tier_assessment": {{
        "tier": "【必须从以下选项中选择一个: '行业顶尖人才 (Top 1%)', '资深专家 (Senior Expert)', '骨干人才 (Core Talent)', '潜力人才 (Potential Talent)', '不匹配 (Mismatched)'】",
        "justification": "【用一句话解释你做出该层级判断的核心依据】"
      }}
    }}
  }}
]
"""

# ... (the rest of your config.py) ...

# ... (the rest of your config.py file) ...
# ... (keep all other prompts and configurations as they are) ...
# ... (keep all other prompts and configurations as they are) ...
# [新增] 专门用于将简历文本转换为结构化JSON的Prompt
# (这是要粘贴到 config.py 的新Prompt)

PROMPT_RESUME_EXTRACTOR = """
# Role
You are a meticulous and highly capable AI data architect. Your mission is to deconstruct a resume with 100% fidelity, mapping every piece of information into the exhaustive JSON structure below.

# Core Mandates
1.  **Exhaustive Extraction**: You must find a place for EVERY piece of information. Even if it's a single, unusual character that appears to be a name, you must treat it as such and place it in the `full_name` field.
2.  **Forced JSON Output**: Your entire output must be a single, valid JSON object enclosed in ```json ... ```. Do not include any text outside this block.
3.  **Mandatory `null`**: If a specific field or section does not exist in the resume, you MUST use the JSON `null` value for that key. Do not omit the key.
4.  **Absolute Verbatim Copying**: For all descriptive text, you MUST copy the original text word-for-word, preserving all original line breaks by escaping them as `\\n`.
5.  **Critical Rule - Do Not Give Up**: The resume content may be unconventional. If you are unsure about any piece of information, make your best logical guess to place it in a field or use the `miscellaneous` section. It is mandatory that you process the entire document and return a complete JSON, even if some fields are uncertain.

# Ultimate Resume Schema (Strictly follow this structure)
```json
{{
  "personal_info": {{
    "full_name": "Full Name (Even if it's a single character)", "gender": "男/女/null", "age": 0, "birth_date": "YYYY-MM-DD/null",
    "marital_status": "已婚/未婚/null", "political_status": "党员/群众/等/null", "nationality": "国籍/null",
    "hukou_location": "户籍地/null"
  }},
  "contact_info": {{
    "phone_number": "手机号/null", "email_address": "邮箱/null", "wechat_id": "微信号/null",
    "linkedin_profile_url": "领英URL/null", "github_profile_url": "GitHub URL/null",
    "personal_website_url": "个人网站URL/null", "current_address": "当前地址/null"
  }},
  "job_intentions": {{
    "desired_positions": ["期望职位1"], "desired_industries": ["期望行业1"], "desired_locations": ["期望城市1"],
    "employment_type": "全职/兼职/实习/null", "expected_salary_range": "期望薪资/null", "availability_for_work": "到岗时间/null"
  }},
  "education_history": [
    {{
      "institution_name": "学校名称", "degree": "学位 (例如: 博士, 硕士, 本科, 大专)", "major": "专业名称",
      "start_date": "YYYY-MM", "end_date": "YYYY-MM", "gpa_or_honors": "【原文复制】GPA、在校荣誉或任何备注"
    }}
  ],
  "work_experience": [
    {{
      "company_name": "公司名称", "position_title": "职位名称", "start_date": "YYYY-MM",
      "end_date": "YYYY-MM 或 至今", "is_internship": false,
      "job_description": "【原文复制】对工作职责的完整描述",
      "achievements": ["【原文复制】第一个关键业绩"],
      "technologies_used": ["技术栈1"],
      "reporting_to": "汇报对象/null", "team_size": 0
    }}
  ],
  "project_experience": [
    {{
      "project_name": "项目名称", "role_in_project": "在项目中的角色", "start_date": "YYYY-MM", "end_date": "YYYY-MM",
      "project_description": "【原文复制】项目背景和目标的描述",
      "responsibilities": ["【原文复制】负责的第一项具体职责"],
      "technologies_used": ["技术栈1"],
      "project_link_or_demo": "项目链接/null"
    }}
  ],
  "skills_summary": {{
    "technical_skills": [{{ "category": "例如: 后端开发", "skills": ["技能1"]}}],
    "soft_skills": ["例如: 团队协作"],
    "languages": [{{ "language": "例如: 英语", "proficiency": "【原文复制】例如: CET-6"}}],
    "certifications": ["证书1"]
  }},
  "awards_and_honors": [{{ "award_name": "奖项名称", "issuing_organization": "颁发组织", "date": "YYYY-MM"}}],
  "publications": [{{ "title": "出版物标题", "publication_outlet": "发表刊物名称", "date": "YYYY-MM", "link": "链接/null"}}],
  "self_assessment_summary": "【原文复制】对简历中“自我评价”等所有总结性文字的完整合并。",
  "miscellaneous": {{
    "professional_memberships": ["协会会员1"], "hobbies_and_interests": "兴趣爱好描述",
    "other_info": "【原文复制】任何无法归入上述类别的其他信息"
  }}
}}
"""
AI_PROMPT_TEMPLATE_BATCH = """### INSTRUCTION:
You are a top-tier AI Technical Recruiter. Your mission is to analyze a batch of one or more candidates against the provided Job Descriptions. For EACH candidate, you MUST provide a complete analysis inside a JSON object.

### 【【【 核心修改点 1/2：明确告知AI批次大小是可变的 】】】 ###
### Evaluation Criteria & Weighting (Apply to EACH candidate):
- **70% Technical Prowess:** Focus on hands-on experience with LLM deployment/fine-tuning, system architecture, Python, OCR, and Vector DBs. This is the most critical factor.
- **30% Management & Business Acumen:** Includes team leadership, project management, and client communication.

### JOB DESCRIPTIONS:
<job_descriptions>
{jd_input}
</job_descriptions>

### CANDIDATE RESUMES:
<resumes>
{resumes_input}
</resumes>

### YOUR FULL RESPONSE:
Your response MUST be a valid JSON array. For EACH candidate provided in the input, you MUST generate a corresponding analysis object.
**Even if there is only one candidate, your response must still be an array containing a single object, like `[ {{...}} ]`.**

Your analysis for each candidate MUST be thorough and detailed. A superficial or overly brief `stream_of_consciousness` is unacceptable. Explain your reasoning clearly for every single candidate, referencing specific parts of their resume and the JD.

The `candidate_id` in the JSON MUST match the ID provided in the input XML tag. Your entire response must start with `[` and end with `]`.

```json
[
  {{
    "candidate_id": "ID_of_the_first_candidate",
    "analysis": {{
      "structured_data": {{
        "candidate_name": "The candidate's full name, or 'Unknown'",
        "phone": "The candidate's phone number, or 'N/A'",
        "email": "The candidate's email address, or 'N/A'",
        "status": "The candidate's current job status ('on-the-job' or 'searching'), or 'N/A'",
        "final_match_score_percent": "Your final, ADJUSTED score as a number only, after applying the 70/30 weighting rule."
      }},
      "stream_of_consciousness": "Your step-by-step thinking process for this candidate, explaining how you arrived at the final score based on the 70/30 rule.",
      "final_verdict": {{
        "core_strengths": "A bilingual summary of the strongest 1-2 matching points.",
        "core_gaps": "A bilingual summary of the main 1-2 risks or questions.",
        "final_match_score": "The same final score, formatted as XX%"
      }}
    }}
  }},
  {{
    "candidate_id": "ID_of_the_second_candidate",
    "analysis": {{
      // ... same complete structure for the second candidate
    }}
  }}
]"""

PROMPT_CANDIDATE_COMPARISON = """
# 角色
你是一位拥有15年经验的资深技术招聘专家，任务是针对一个具体的【{job_title}】职位，对两位候选人进行精准的横向对比，并以结构化的JSON和详细的分析文本两种形式输出。

# 输入材料
1.  **【职位要求 (JD)】**
    ```    {jd_text}
    ```
2.  **【基准候选人简历 (Benchmark Candidate)】**
    - 姓名: {benchmark_name}
    ```
    {benchmark_resume_text}
    ```
3.  **【新候选人简历 (New Candidate)】**
    - 姓名: {new_candidate_name}
    ```
    {new_resume_text}
    ```

# 任务指令
必须严格按照以下两步输出：

**第一部分: 结构化数据提取 (JSON)**
首先，生成一个包含你核心判断的JSON对象。这个块必须以 ```json 开始，以 ``` 结束。所有分析都必须围绕提供的JD进行。

```json
{{
  "benchmark_candidate_score": "为基准候选人打一个0-100的综合分",
  "new_candidate_score": "为新候选人打一个0-100的综合分",
  "verdict": "明确指出谁更胜出 ('新候选人胜出', '基准候选人胜出', 或 '综合实力相当')",
  "new_candidate_win_points": [
    "新候选人最明显的第一个优势",
    "新候选人最明显的第二个优势"
  ],
  "new_candidate_risk_points": [
    "新候选人最明显的第一个劣势或风险点"
  ]
}}
**第二部分: 详细分析报告 (Markdown)**
在JSON块之后，生成一份详细的、具有深度洞察的分析报告。使用Markdown格式，内容包括：

- **【综合评分对比】**: 分别陈述两位候选人的得分和打分依据。
- **【新候选人 vs. 基准候选人：优势 (Win Points)】**: 详细阐述“新候选人”明显优于“基准候选人”的3-5个关键点，并结合JD说明原因。
- **【新候选人 vs. 基准候选人：劣势 (Risk Points)】**: 详细阐述“新候选人”可能不如“基准候选人”的2-3个潜在风险点或不确定性。
- **【最终结论与建议】**: 基于以上所有分析，用一段话总结你的最终推荐建议。明确回答：“新候选人是否比基准候选人更值得推荐？”，并给出核心理由。
"""

PROMPT_DEEP_DIVE_JD_MATCH = """
# 角色
你是一位专业的AI招聘分析师，任务是深度剖析一份候选人简历与职位要求的匹配度。

# 输入材料
1.  **【职位要求 (JD)】**
    ```    {jd_text}
    ```
2.  **【候选人简历】**
    ```
    {resume_text}
    ```

# 任务指令
请生成一份关于这位候选人与职位匹配度的详细分析报告，包含以下部分：

1.  **【总体匹配度评分】**:
    - 请给出一个0-100分之间的分数，并附上一句精炼的总体评价。

2.  **【核心匹配点 (Strengths)】**:
    - 详细列出候选人的经历、技能或项目中最符合JD要求的3-5个关键点。

3.  **【潜在风险与不匹配点 (Weaknesses/Gaps)】**:
    - 客观地指出简历中未能体现或可能不满足JD要求的2-3个方面。

4.  **【面试建议问题 (Interview Questions)】**:
    - 基于发现的潜在风险点，提出3个有针对性的面试问题，用于在面试中进一步考察候选人。
"""
# ===================================================================================
# --- V2 新增：人才 PK 对比功能专属配置 ---
# ===================================================================================

# --- PK 功能专属文件夹 ---
# 存放“你自己”的基准简历（必须是 .json 格式）
BASELINE_DIR = PROJECT_ROOT_DIR / "baseline_profile"
# 存放每次PK生成的详细报告
PK_REPORTS_DIR = PROJECT_ROOT_DIR / "pk_reports"
# 存放程序退出时生成的PK汇总报告
PK_SUMMARY_REPORT_DIR = PROJECT_ROOT_DIR / "所有汇总报告"

# --- PK 功能数据库配置 ---
# Qdrant 中用于存储PK报告向量的集合名称
PK_QDRANT_COLLECTION = "ai_recruiter_v33_pk_reports"

# --- PK 功能核心提示词 (Prompt) ---
# 在 config.py 文件中，用这个版本替换现有的 PK_PROMPT_TEMPLATE

PK_PROMPT_TEMPLATE = """
# 角色
你是一位极其苛刻、挑剔、一针见血的顶级人才战略分析师。你的双重任务是：
1.  主持一场关于 {baseline_name} vs. {candidate_name} 的、绝对客观的“人才价值PK擂台”。
2.  基于PK结果，为 {baseline_name} 提供一份机密的、高度可执行的个人战略发展简报。

# 核心原则
1.  **绝对客观**: PK阶段的分析必须公正，严格基于双方简历提供的证据。
2.  **深度细节**: 每一回合的分析都必须深入细节，引用原文，拒绝空泛评论。
3.  **结论一致**: `overall_winner` 字段必须与 `verdict_summary` 的结论严格保持一致。这是强制性规则。
4.  **结果驱动的简报**: 最终的战略建议（`personal_strategic_debrief_for_you`）必须根据PK的胜负结果进行动态调整。

# 输入材料
## 【你的简历】: {baseline_name}
{baseline_resume_text}
---
## 【对比候选人】: {candidate_name}
{candidate_resume_text}
---

# 输出规则
1.  **强制JSON输出**: 你的最终输出必须是且仅是一个完整的JSON对象，包裹在 ```json ... ``` 代码块中。
2.  **强制全中文**: JSON中所有的键(key)和值(value)都必须使用简体中文。
3.  **强制完整与深度**: 必须包含所有PK回合的分析，每个分析都不能少于50字。
4.  **强制打分与胜负**: 每个回合都必须为双方打分 (1-10分制)，并明确指出胜者。

# PK报告与个人战略简报输出格式 (严格遵循此结构)
```json
{{
  "talent_pk_report": {{
    "title": "人才价值PK擂台: {baseline_name} vs. {candidate_name}",
    "pk_timestamp": "YYYY-MM-DDTHH:MM:SSZ",
    "rounds": [
      {{
        "round_name": "第一回合: 学历背景价值 (Educational Background Value)",
        "your_score": 0, "candidate_score": 0, "winner": "胜者姓名",
        "analysis": {{
          "winner_strengths": "【分析胜者学历的品牌价值、专业匹配度或名校光环带来的市场溢价，至少50字】",
          "loser_weaknesses": "【分析败者学历在此次对比中的相对劣势，至少50字】"
        }}
      }},
      {{
        "round_name": "第二回合: 职业履历含金量 (Professional History Pedigree)",
        "your_score": 0, "candidate_score": 0, "winner": "胜者姓名",
        "analysis": {{
          "winner_strengths": "【分析胜者职业履历的亮点，如公司知名度、晋升速度、职位核心度等，至少50字】",
          "loser_weaknesses": "【分析败者履历的不足之处，如稳定性、公司平台或职业轨迹的清晰度，至少50字】"
        }}
      }},
      {{
        "round_name": "第三回合: 技术栈与项目影响力 (Tech Stack & Project Impact)",
        "your_score": 0, "candidate_score": 0, "winner": "胜者姓名",
        "analysis": {{
          "winner_strengths": "【分析胜者技术栈的深度、广度或前瞻性，并结合其项目成果的商业影响力进行论证，至少50字】",
          "loser_weaknesses": "【分析败者在技术栈或项目经验上的明显短板，至少50字】"
        }}
      }},
      {{
        "round_name": "第四回合: 市场价值与稀缺性 (Market Value & Scarcity)",
        "your_score": 0, "candidate_score": 0, "winner": "胜者姓名",
        "analysis": {{
          "winner_strengths": "【分析胜者的技能组合为何在当前人才市场上更受欢迎、更稀缺，议价能力更强，至少50字】",
          "loser_weaknesses": "【分析败者的技能组合为何市场竞争力相对较弱，可替代性较高，至少50字】"
        }}
      }},
      {{
        "round_name": "第五回合: 未来发展潜力 (Future Potential)",
        "your_score": 0, "candidate_score": 0, "winner": "胜者姓名",
        "analysis": {{
          "winner_strengths": "【分析胜者展现出的学习能力、适应性和战略思维，判断其未来的成长天花板为何更高，至少50字】",
          "loser_weaknesses": "【分析败者在成长性上的潜在局限，至少50字】"
        }}
      }},
      {{
        "round_name": "第六回合: 风险与疑点评估 (Risk Assessment)",
        "your_score": 0, "candidate_score": 0, "winner": "胜者姓名",
        "analysis": {{
          "winner_strengths": "【分析胜者为何让雇主更“放心”，如职业稳定性、背景的真实可靠性等，至少50字】",
          "loser_weaknesses": "【分析败者简历中可能存在的风险点，如频繁跳槽、空窗期、过度包装等，至少50字】"
        }}
      }}
    ],
    "final_verdict": {{
      "overall_winner": "【严格根据总分和分析，填写最终胜者姓名】",
      "verdict_summary": "【总结这场PK的最终结果，结论必须与 overall_winner 严格一致】"
    }},
    "personal_strategic_debrief_for_you": {{
      "commentary": "此部分内容根据PK胜负结果动态生成。",
      "IF_YOU_LOST": {{
        "brutal_truth": "【直面现实的残酷真相】总结这次PK暴露出的你最核心的1-2个价值短板，必须一针见血。",
        "high_roi_action_plan": {{
          "primary_project_objective": "【最高价值的实践目标】给出一个具体的、能直接对标并超越对手核心优势的项目目标。",
          "key_capability_enhancements": ["一项需要强化的、能直接提升你市场价值的技术能力。", "另一项高价值能力或软技能。"],
          "strategic_repositioning": "【重塑你的市场定位】建议你如何在下阶段的简历和面试中，调整你的个人叙事。"
        }}
      }},
      "IF_YOU_WON": {{
        "analysis_of_your_alpha": "【你的核心竞争壁垒】总结你这次胜出的1-2个决定性优势。",
        "how_to_achieve_dominant_lead": {{
            "strategic_goal": "【确立“遥遥领先”的战略目标】基于你的现有优势，设定一个更高的、能让你与此类竞争者拉开代差的战略目标。例如：‘目标：从“AI应用开发者”进化为“AI原生业务系统架构师”，不再局限于工具，而是设计和交付能独立创造营收的AI业务闭环。’",
            "next_flagship_project": "【启动下一个旗舰项目】设计一个新的、更具雄心的个人项目，以达成上述战略目标。例如：‘项目：构建一个“AI驱动的自动化猎头SaaS平台”原型，该平台不仅能分析简历，还能主动进行人才寻源、建立沟通渠道并进行初步筛选，展示端到端的商业解决方案能力。’",
            "amplification_tactic": "【影响力放大战术】给出一个具体的建议，将你的技术优势转化为行业影响力。例如：‘战术：将你的“旗舰项目”的核心技术和架构思考，撰写成深度系列文章或制作成视频，在顶级技术社区（如InfoQ, GitHub）发表，将个人品牌提升为行业标杆。’"
        }}
      }}
    }}
  }}
}}
"""
# FILE: config.py (add to the end of the file)

# ===================================================================================
# --- Stage 3: Ultimate PK Showdown Specific Config ---
# ===================================================================================

# --- Folder for defining the active PK task ---
COMPARISON_DIR = PROJECT_ROOT_DIR / "comparison_tasks"
# --- Folder for archiving candidates who participate in the Ultimate PK ---
COMPARISON_PARTICIPANTS_DIR = PROJECT_ROOT_DIR / "参与对比的候选人简历"

# --- Qdrant collection name for storing PK reports ---
QDRANT_COMPARISON_COLLECTION_NAME = "ai_recruiter_v33_comparisons"

# --- AI Prompt for the Ultimate PK Showdown ---
PROMPT_CANDIDATE_COMPARISON = """
# 角色
你是一位拥有15年经验的资深技术招聘专家，任务是针对一个具体的【{job_title}】职位，对两位候选人进行精准的横向对比，并以结构化的JSON和详细的分析文本两种形式输出。

# 输入材料
1.  **【职位要求 (JD)】**
    ```    {jd_text}
    ```
2.  **【基准候选人简历 (Benchmark Candidate)】**
    - 姓名: {benchmark_name}
    ```
    {benchmark_resume_text}
    ```
3.  **【新候选人简历 (New Candidate)】**
    - 姓名: {new_candidate_name}
    ```    {new_resume_text}
    ```

# 任务指令
必须严格按照以下两步输出：

**第一部分: 结构化数据提取 (JSON)**
首先，生成一个包含你核心判断的JSON对象。这个块必须以 ```json 开始，以 ``` 结束。所有分析都必须围绕提供的JD进行。

```json
{{
  "benchmark_candidate_score": "为基准候选人打一个0-100的综合分",
  "new_candidate_score": "为新候选人打一个0-100的综合分",
  "verdict": "明确指出谁更胜出 ('新候选人胜出', '基准候选人胜出', 或 '综合实力相当')",
  "new_candidate_win_points": [
    "新候选人最明显的第一个优势",
    "新候选人最明显的第二个优势"
  ],
  "new_candidate_risk_points": [
    "新候选人最明显的第一个劣势或风险点"
  ]
}}
"""
