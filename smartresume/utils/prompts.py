from typing import Dict

SYSTEM_PROMPT = """
您是一个专业的简历分析助手。您的任务是将给定的简历文本转换为下面给定的 JSON 输出。(如果有中英文简历同时出现时，只关注中文简历)
"""

BASIC_INFO_PROMPT = """
提取如下信息到json ，若某些字段不存在则输出 "" 空
{
  "basicInfo": {
    "name": "", # 姓名 如: 张三
    "personalEmail": "", # 邮箱 如:610730297@qq.com
    "phoneNumber": "", #电话/手机 如:13915732235 请保留原文中的形式\
 保留国家码 区号括号 例如:"+1（201）706 1136"
    "age":"", # 当前年龄
    "born": "", # 出生年  如 1996-11
    "gender": "", # 男/女 若不存在 则不填
    "desiredLocation": ["城市名", ...],
    # 意向期望目标工作地/城市 可以填写多个 如果仅存在一个 只需要填写一个
    # e.g: "[北京市,上海市]" **简历中需要明确说明是期望城市**
    # 一般出现在同一行(若多个则使用"," ";" 隔开) 若不存在填 []
    # 例如("求职目标：填写意向岗位) 应该填写为 "desiredLocation": []
    "jobIntention": "", # 原文明示的求职意向岗位，不从历史职位推测；不存在填 ""
    "currentLocation": "城市名"
    # 现居地/当前城市 xxx省xx市 **不要出现籍贯中的地址**
    # **不要从工作经历中推测现居地 要写明现居地**
    "placeOfOrigin": "" # 籍贯 不要和 现居地/当前城市 混淆
  },
}
"""

WORK_EXPERIENCE_PROMPT = """{
  "workExperience": [  #工作经历 工作经验 实习经验
    {
      "companyName": "", # 公司名称  如阿里巴巴
      "employmentPeriod": {  #  经历开始时间和结束时间
        "startDate": "",# 入职时间 开始时间 若不存在 填写""(不要编造)\
 格式为 %Y.%m 或 %Y 如 2024 ,2024.1
        "endDate": "" #若至今 填写  "至今"  若不存在 填写""(不要编造)\
 格式为 %Y.%m 或 %Y 如 2024 ,2024.1
      },
      "position": "", #职位  如  算法工程师 TeamLeader 业务组专家 遵循原文不要编造或者不要推测职位
      "internship": 0, #该段经历是否是实习 如果是实习则为1  不是实习为0
      "jobDescription_refer_index_range": [start_index,end_index]   # List
       # 如果不存在 就写 []。请勿和项目描述混淆
       # jobDescription_refer_index_range字段的定义:
       # 指工作经历描述的原文引用的段落index范围
       # 一般情况下包括了工作成果 业绩 主要工作 项目背景
       # 使用的技术栈 工作描述等 尽可能写全 直到下一段工作经历为止。
       # jobDescription_refer_index_range不包括
       # companyName字段 employmentPeriod字段 position字段。
       # 请勿将companyName字段 employmentPeriod字段
       # position字段写入描述范围。
       # jobDescription_refer_index_range不包括
       # companyName字段 employmentPeriod字段 position字段。
       # 请勿将companyName字段 employmentPeriod字段
       # position字段写入描述范围。
       # 如下示例1
       # [22]: 阿里巴巴 2021.11-2022.11
       # [22]: 工作描述: 从事地推工作完成xx业绩
       # [23]: 在地推任务中考核为A
       # [24]: 公司：阿里云
       # 若 "jobDescription_refer_index_range":[22,23] 则代表从段落index 从22到23的所有内容。\
(包含22和23本身) 即 22 + 23
       # 如下示例2
       # [22]: 工作描述: 从事地推工作完成xx业绩
       # [23]: 在地推任务中考核为A
       # [...]:  ...
       # [40]: 为公司地推活动的圆满结束贡献了xxx销售业绩。
       # 若 "jobDescription_refer_index_range": [22,40]
       # 则代表从段落index 从22到40的所有内容。
       # (包含22和40本身) 即 22 + 23 + 24 .... + 39 + 40
    }, ...
  ]
  }
"""

PROJECT_EXPERIENCE_PROMPT = """
提取简历中的项目经历，遵循原文，不要编造。若不存在则输出 {"projectExperience": []}。
以下注释仅用于解释字段，实际只输出 JSON，不输出注释或说明。
{
  "projectExperience": [  # 项目经历 项目经验 科研项目 课程项目
    {
      "projectName": "", # 项目名称，保留原文完整名称，不要将公司名称或章节标题当作项目名称
      "projectPeriod": {  # 项目开始时间和结束时间，不要使用工作经历时间代替
        "startDate": "", # 开始时间，格式为 %Y.%m 或 %Y，如 2024.1、2024；不存在填 ""
        "endDate": "" # 结束时间，格式同上；若至今填 "至今"；不存在填 ""
      },
      "position": "", # 项目角色，如项目负责人、后端开发；只填写原文明确的角色，不存在填 ""
      "projectDescription_refer_index_range": []
      # 项目描述的原文段落 index 范围，存在时填写 [start_index, end_index]，不存在填 []
      # 包括项目背景、目标、个人职责、实现过程、使用的技术及项目成果
      # 不包含只有项目名称、时间、角色的段落，也不能包含下一项目或其他章节
      # 如果同一段同时包含项目名称和描述正文，则保留整段
      # 索引使用输入中的真实编号，起止均包含在内，单段写 [n, n]，不要编造编号
      # 如 [12]: 负责接口设计与开发；[13]: 完成性能优化
      # 则填写 "projectDescription_refer_index_range": [12, 13]
    }
  ]
}
多个项目分别生成对象。只抽取明确项目章节中的经历，不要把普通工作职责改写为项目。
"""

EDUCATION_PROMPT = """
{
  "education": [  #教育经历
    {
      "degreeLevel": "", #学位 本科/硕士/博士/专科/高中/初中 若不存在则填""
      "period": {  # 教育经历开始时间和结束时间 格式为 "yyyy.mm" 或 "yyyy" 如 "2021.2"
        "startDate": "", # 开始时间 格式为 %Y.%m 或 %Y 如 2024 ,2024.1
        "endDate":""  #若至今 填写  "至今"  若不存在 填写""
      },
      "school": "", #学校名称: 如厦门大学 MIT 中英文都可以
      "department": "", # 系: 如信息工程系
      "major": "", # 专业: 如机械工程
      "advisorList": [], # 导师姓名数组，可多个；只提取明确标为导师/指导老师/\
Advisor/Supervisor的人名，不含职称；不存在填 []
      "labName": "", # 该段教育经历所属的实验室、课题组或研究组名称，遵循原文，不存在填 ""
      "expectedGraduationDate": "", # 预计毕业时间，格式 YYYY 或 YYYY-MM；仅原文明示预计/\
Expected等时填写，不由入学或结束时间推算；不存在填 ""
      "gpa": "", # 绩点或均分，如 3.8/4.0、88/100，保留原文满分制，不自行换算；排名、名次、百分比不填此处；不存在填 ""
      "educationDescription": "" # 教育描述，包括该段教育经历的课程、排名、研究方向、荣誉等原文补充信息；\
不重复已单独填写的学位、导师、实验室、GPA等；不存在填 ""
    }, ...
  ]
}
"""

SKILLS_STRENGTHS_PROMPT = """
提取简历中明确列出的专业技能和个人优势，使用原文段落 index 范围，不要自行总结或推测。
以下注释仅用于解释字段，实际只输出 JSON，不输出注释或说明。
{
  "professionalSkills": [], # 专业技能/技能清单/技术能力/Skills 章节正文的 \
[start_index, end_index]；不存在填 []
  "personalStrengths": [] # 个人优势/自我评价/个人简介/Strengths/Summary 章节正文的 \
[start_index, end_index]；不存在填 []
}
# 两个字段均为原文引用范围，不是技能名称列表
# 只引用对应章节，不要从工作经历或项目经历推测技能、沟通能力等优势
# 不包含单独的章节标题；若标题和正文在同一段，如“专业技能：Python、SQL”，则保留整段
# 索引使用输入中的真实编号，起止均包含在内；单段写 [n, n]，不存在或输入无编号时填 []
# 每个范围必须连续，不能跨入其他章节或无关段落
# 例如 [8]: 专业技能；[9]: Python、SQL；[10]: 自我评价；[11]: 善于团队协作
# 输出 {"professionalSkills": [9, 9], "personalStrengths": [11, 11]}
"""

PUBLICATION_PROMPT = """
提取简历中明确列出的论文，若不存在则输出 {"publicationList": []}。
以下注释仅用于解释字段，实际只输出 JSON，不输出注释或说明。
{
  "publicationList": [
    {
      "title": "", # 论文完整题目；只有论文数量而无具体题目时不生成记录
      "conferenceName": "", # 原文明示的会议名称或简称；不把期刊名当会议名，未写明填 ""
      "publicationYear": "", # 年份 YYYY，未写明填 ""
      "publicationLevel": "", # SCI/EI/CCF-A/CCF-B/CCF-C/其他等级，仅原文明示时填写，不能按会议名推断
      "status": "", # 原文明示已发表填“已发布”，投稿或审稿中填“投稿中”；其他或未说明填 ""
      "candidateAuthorRole": "", # 独立一作/共同一作/其他作者，必须能从原文明示身份或作者列表确定，否则填 ""
      "citationCount": "", # 原文明示的被引次数，使用字符串；未写明填 ""
      "url": "" # 原文明示的论文链接，不联网查找或补造；不存在填 ""
    }
  ]
}
多篇论文分别生成对象；不提取专利、项目名称或没有题目的论文数量总结。
保留题目原文，不编造会议、等级、作者身份或引用数。
"""

COMPETITION_PROMPT = """
提取简历中明确写出的竞赛经历，若不存在则输出 {"competitionList": []}。
以下注释仅用于解释字段，实际只输出 JSON，不输出注释或说明。
{
  "competitionList": [  # 竞赛经历 比赛获奖 Competitions Contests
    {
      "experience": "", # 赛事完整名称及获奖等级，如“全国大学生数学建模竞赛二等奖”；仅参赛未写获奖时只填赛事名称
      "level": "", # 竞赛级别：国际级/国家级/省市级/院校级；只根据原文明示的范围填写，无法判断填 ""
      "competitionDate": "" # 该次参赛或获奖时间，格式 YYYY 或 YYYY-MM；不要用工作或项目时间代替；不存在填 ""
    }
  ]
}
多条竞赛分别生成对象。同一届、同一阶段的重复表述合并，不同年份或阶段的不同奖项分别保留。
只提取明确的竞赛经历或获奖条目，不把奖学金、学术荣誉、资格证书或普通工作成果当作竞赛。
缺失字符串填 ""，不编造赛事、奖项等级或时间，不生成全空记录。
"""

HONOR_PROMPT = """
提取简历中明确写出的学术荣誉、奖学金及在校荣誉，若不存在则输出 {"honorList": []}。
以下注释仅用于解释字段，实际只输出 JSON，不输出注释或说明。
{
  "honorList": [  # 学术荣誉 荣誉奖项 奖学金 Honors Awards Scholarships
    {
      "name": "", # 荣誉完整名称，如国家奖学金、优秀毕业生、优秀论文奖；不要只填“一等奖”等等级
      "issuer": "", # 颁发机构，只填写原文明示的机构，不根据奖项名称推测；不存在填 ""
      "level": "", # 级别：国际级/国家级/省市级/院校级；根据原文明示的范围填写，无法判断填 ""
      "awardDate": "", # 获奖时间，格式 YYYY 或 YYYY-MM；若原文仅有学年区间则取起始年份；不存在填 ""
      "description": "" # 与该项荣誉直接相关的原文补充说明，如获奖名次、比例或事由；不存在填 ""
    }
  ]
}
多项荣誉分别生成对象。同一项荣誉的重复表述合并，不同年份多次获得的荣誉分别保留。
竞赛奖项归入 competitionList，不在此重复提取；资格证书、公司绩效奖不收录。
只提取明确的荣誉记录，不把论文发表、项目成果或普通学业成绩改写成荣誉，不生成全空记录。
"""

RESEARCH_DIRECTION_PROMPT = """
提取简历中明确写出的研究方向或研究兴趣，若不存在则输出 {"researchDirectionList": []}。
以下注释仅用于解释字段，实际只输出 JSON，不输出注释或说明。
{
  "researchDirectionList": [  # 研究方向 研究兴趣 Research Interests Research Areas
    {
      "name": "", # 研究方向名称，保留原文措辞，如多模态学习、信息检索
      "description": "" # 与该方向直接关联的原文补充描述，不存在填 ""
    }
  ]
}
明确列出多个研究方向时分别生成对象，同一方向的重复表述只保留一条。
不要根据专业、论文题目、工作经历、项目或技能推断研究方向，不生成全空记录。
"""

SOCIAL_PROFILE_PROMPT = """
提取候选人本人明确提供的外部主页与社交账号，若不存在则输出 {"socialProfileList": []}。
以下注释仅用于解释字段，实际只输出 JSON，不输出注释或说明。
{
  "socialProfileList": [  # 个人主页 社交主页 联系账号
    {
      "type": "", # 平台类型：personal_homepage/github/linkedin/google_scholar/\
wechat/other；个人网站或博客归 personal_homepage
      "url": "", # 主页链接，保留原文形式，不补协议头或域名；只有账号时填 ""
      "account": "" # 原文明示的用户名或账号；只有链接时不从链接推导账号，填 ""
    }
  ]
}
多个主页或账号分别生成对象，同一链接或同平台同账号去重，不同链接保留。
url 与 account 至少一个非空。邮箱、手机号、公司官网、项目演示地址、论文 DOI 不收录。
只提取原文明确的信息，不搜索、不猜测或补全候选人的链接及账号。
"""

THINK_TAG = " /no_think"


def get_prompts() -> Dict[str, str]:

    return {
        "basic_info": SYSTEM_PROMPT + BASIC_INFO_PROMPT + THINK_TAG,
        "work_experience": SYSTEM_PROMPT + WORK_EXPERIENCE_PROMPT + THINK_TAG,
        "project_experience": SYSTEM_PROMPT
        + PROJECT_EXPERIENCE_PROMPT
        + THINK_TAG,
        "education": SYSTEM_PROMPT + EDUCATION_PROMPT + THINK_TAG,
        "skills_strengths": SYSTEM_PROMPT
        + SKILLS_STRENGTHS_PROMPT
        + THINK_TAG,
        "publication": SYSTEM_PROMPT + PUBLICATION_PROMPT + THINK_TAG,
        "competition": SYSTEM_PROMPT + COMPETITION_PROMPT + THINK_TAG,
        "honor": SYSTEM_PROMPT + HONOR_PROMPT + THINK_TAG,
        "research_direction": SYSTEM_PROMPT
        + RESEARCH_DIRECTION_PROMPT
        + THINK_TAG,
        "social_profile": SYSTEM_PROMPT + SOCIAL_PROFILE_PROMPT + THINK_TAG,
    }
