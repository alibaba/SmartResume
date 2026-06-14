"""
Prompt management module
"""
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
    "phoneNumber": "", #电话/手机 如:13915732235 请保留原文中的形式 保留国家码 区号括号 例如:"+1（201）706 1136"
    "age":"", # 当前年龄
    "born": "", # 出生年  如 1996-11
    "gender": "", # 男/女 若不存在 则不填
    "desiredLocation": ["城市名", ...],
    # 意向期望目标工作地/城市 可以填写多个 如果仅存在一个 只需要填写一个
    # e.g: "[北京市,上海市]" **简历中需要明确说明是期望城市**
    # 一般出现在同一行(若多个则使用"," ";" 隔开) 若不存在填 []
    # 例如("求职目标：填写意向岗位) 应该填写为 "desiredLocation": []
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
        "startDate": "",# 入职时间 开始时间 若不存在 填写""(不要编造) 格式为 %Y.%m 或 %Y 如 2024 ,2024.1
        "endDate": "" #若至今 填写  "至今"  若不存在 填写""(不要编造) 格式为 %Y.%m 或 %Y 如 2024 ,2024.1
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
       # 若 "jobDescription_refer_index_range":[22,23] 则代表从段落index 从22到23的所有内容。(包含22和23本身) 即 22 + 23
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
      "educationDescription": "" # 教育描述  包括这段教育经历的课程成绩、研究方向、GPA、荣誉奖项等 不包含学位。直接使用简历中的描述 不存在则填写 "" 空
    }, ...
  ]
}
"""

THINK_TAG = " /no_think"


def get_prompts() -> Dict[str, str]:
    """Get all prompts"""
    return {
        "basic_info": SYSTEM_PROMPT + BASIC_INFO_PROMPT + THINK_TAG,
        "work_experience": SYSTEM_PROMPT + WORK_EXPERIENCE_PROMPT + THINK_TAG,
        "education": SYSTEM_PROMPT + EDUCATION_PROMPT + THINK_TAG,
    }
