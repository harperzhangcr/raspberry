# -*- coding: utf-8 -*-
"""
每月例行全自动版：基于【当前日期 - 15天】智能推算目标月份，明细指标精准对齐版
"""

from __future__ import annotations

import json
import html
import csv
import os
import re
from datetime import datetime, timedelta
from collections import OrderedDict

# ====================== 【核心调整：当前日期 - 15天 锁定月份】 ======================
now = datetime.now()
# 计算核心锚定日期：当前时间向前推 15 天
anchor_date = now - timedelta(days=15)

report_year = anchor_date.year
report_month = anchor_date.month

# 1. 自动组装飞书导出的历史月度文件名后缀（如: 202605）
MONTH_STR_SHORT = f"{report_year}{report_month:02d}" 

# 2. 自动组装对应的月末截止日期（如: 2026-05-31）
if report_month in [1, 3, 5, 7, 8, 10, 12]:
    last_day = 31
elif report_month in [4, 6, 9, 11]:
    last_day = 30
else:
    # 闰年判断
    last_day = 29 if (report_year % 4 == 0 and report_year % 100 != 0) or (report_year % 400 == 0) else 28
TARGET_MONTH_DATE = f"{report_year}-{report_month:02d}-{last_day}"

# 3. 自动组装指摘落实表所需的月份（如: 2026-05}
TARGET_MONTH_Y_M = f"{report_year}-{report_month:02d}"

# 4. 自动计算所属季度（如: 2026-Q2）
quarter = (report_month - 1) // 3 + 1
TARGET_QUARTER = f"{report_year}-Q{quarter}"

print(f"📅 系统当前时间: {now.strftime('%Y-%m-%d')}")
print(f"⚓️ [当前日期 - 15天] 的锚定时间为: {anchor_date.strftime('%Y-%m-%d')}")
print(f"📊 已自动为您锁定报表月度规则：")
print(f"   -> 目标月份: {TARGET_MONTH_Y_M}")
print(f"   -> 里程碑节点: {TARGET_MONTH_DATE}")
print(f"   -> 所属季度: {TARGET_QUARTER}")
print(f"   -> 期待的看板文件名: 进度跟踪看板-{MONTH_STR_SHORT}存档_data.json\n")


# 全自动获取当前脚本所在的绝对目录，彻底绕开 Mac 根目录只读限制
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS_DIR = os.path.join(BASE_DIR, 'artifacts')

def clean_name(name):
    if not name:
        return ""
    return str(name).replace('“', '"').replace('”', '"').strip()

def zhizhai_sort_key(row):
    type_order = {'指摘': 0, '建议': 1}
    zhi_leader_order = {'丁国祥': 0, '李化': 1}
    suggestion_leader_order = {'何修华': 0}
    item_type = str(row.get('事项类型', ''))
    leader = str(row.get('提出领导', ''))
    if item_type == '指摘':
        leader_rank = zhi_leader_order.get(leader, 99)
    elif item_type == '建议':
        leader_rank = suggestion_leader_order.get(leader, 99)
    else:
        leader_rank = 99
    return (type_order.get(item_type, 99), leader_rank, leader, str(row.get('跟踪事项', '')))

# ====================== 1. 里程碑完成率指标统计表 ======================
def generate_milestone_completion_table(progress_data, project_data):
    print("正在生成里程碑完成率指标统计表...")
    
    project_risk_from_list = {}
    for p_row in project_data:
        p_name = clean_name(p_row.get('创新课题名称', ''))
        if p_name:
            project_risk_from_list[p_name] = p_row.get('风险等级', '')

    month_filtered_rows = []
    for row in progress_data:
        plan_time = row.get('计划完成时间', '')
        if plan_time and TARGET_MONTH_DATE in plan_time:
            month_filtered_rows.append(row)

    q2_filtered_rows = [
        r for r in progress_data \
        if r.get('所属季度') == TARGET_QUARTER and r.get('是否为当前应完成里程碑') == '是'
    ]

    q2_total = len([r for r in q2_filtered_rows if r.get('状态') is not None])
    q2_completed = len([r for r in q2_filtered_rows if r.get('状态') == '已完成'])
    q2_overall_rate = q2_completed / q2_total if q2_total > 0 else 0

    q2_system_rows = [r for r in q2_filtered_rows if r.get('是否涉及系统建设') == '是']
    q2_system_total = len([r for r in q2_system_rows if r.get('状态') is not None])
    q2_system_completed = len([r for r in q2_system_rows if r.get('状态') == '已完成'])
    q2_system_rate = q2_system_completed / q2_system_total if q2_system_total > 0 else 0

    q2_early_rows = [
        r for r in progress_data \
        if r.get('所属季度') == TARGET_QUARTER and r.get('进度管理') == '🎉 提前完成'
    ]
    early_completion_count = len(q2_early_rows)

    # 本月基础核心指标计算
    month_total = len([r for r in month_filtered_rows if r.get('状态') is not None])
    month_completed = len([r for r in month_filtered_rows if r.get('状态') == '已完成'])
    month_overall_rate = month_completed / month_total if month_total > 0 else 0

    # ⭐ 【明细指标精准计算】
    month_total_count = month_total
    month_completed_count = month_completed
    month_delayed_count = len([r for r in month_filtered_rows if r.get('进度管理') == '🚨 已延期'])
    month_early_count = len([r for r in month_filtered_rows if r.get('进度管理') == '🎉 提前完成'])

    project_completion_rates = {}

    for row in month_filtered_rows:
        project = clean_name(row.get('所属项目', ''))
        if project:
            if project not in project_completion_rates:
                project_completion_rates[project] = {'total': 0, 'completed': 0}
            if row.get('状态') is not None:
                project_completion_rates[project]['total'] += 1
                if row.get('状态') == '已完成':
                    project_completion_rates[project]['completed'] += 1

    project_rates = []
    for project, counts in project_completion_rates.items():
        total = counts['total']
        completed = counts['completed']
        rate = completed / total if total > 0 else 0
        risk = project_risk_from_list.get(project, "")  
        project_rates.append([project, f"{rate:.2%}", risk])

    # 按照最新模版顺序组装 CSV 报表
    output_data = [
        ['指标名称', '数值', '说明'],
        [f'里程碑总体完成率-{TARGET_QUARTER.split("-")[1]}TD', f"{q2_overall_rate:.2%}", f"已完成{q2_completed}个/总计{q2_total}个"],
        [f'系统建设相关里程碑完成率-{TARGET_QUARTER.split("-")[1]}TD', f"{q2_system_rate:.2%}", f"已完成{q2_system_completed}个/总计{q2_system_total}个"],
        [f'提前完成里程碑数量-{TARGET_QUARTER.split("-")[1]}', str(early_completion_count), f"{TARGET_QUARTER}季度提前完成"],
        ['里程碑总体完成率-本月', f"{month_overall_rate:.2%}", f"已完成{month_completed}个/总计{month_total}个"],
        # ⭐ 精准插队 4 个过程指标
        ['本月总里程碑数量', str(month_total_count), ''],
        ['本月完成里程碑数量', str(month_completed_count), ''],
        ['本月延期里程碑数量', str(month_delayed_count), ''],
        ['本月提前完成里程碑数量', str(month_early_count), ''],
        ['各课题里程碑完成率-本月', '', '按所属项目分组']
    ]

    for item in project_rates:
        output_data.append(item)
        
    return output_data


# ====================== 2. 指摘落实 ======================
def process_zhizhai():
    try:
        json_path = os.path.join(BASE_DIR, '历次创新委课题&部门指示.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        rows = data['tables'][0]['rows']
        filtered = [r for r in rows if r.get('所属月份') == TARGET_MONTH_Y_M]
        grouped = {}
        for r in filtered:
            depts = r.get('相关课题/部门', ['未分类'])
            for d in depts:
                if d not in grouped:
                    grouped[d] = []
                grouped[d].append({
                    '相关课题/部门': d,
                    '跟踪事项': r.get('跟踪事项','').replace('\n',' '),
                    '事项类型': r.get('事项类型',''),
                    '提出领导': r.get('提出领导',''),
                    '落实情况': r.get('落实情况','')
                })
        final = []
        for d in sorted(grouped.keys()):
            final.extend(sorted(grouped[d], key=zhizhai_sort_key))
        path = os.path.join(ARTIFACTS_DIR, '指摘落实.csv')
        with open(path, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.DictWriter(f, fieldnames=['相关课题/部门','跟踪事项','事项类型','提出领导','落实情况'])
            w.writeheader()
            w.writerows(final)
        print('✅ 指摘落实.csv')
    except Exception as e:
        print('指摘落实文件读取失败', e)

# ====================== 3. 课题进度表 ======================
def load_progress_data():
    try:
        json_path = os.path.join(BASE_DIR, f'进度跟踪看板-{MONTH_STR_SHORT}存档_data.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)['tables'][0]['rows']
    except:
        print(f"❌ 未找到本月看板数据文件: 进度跟踪看板-{MONTH_STR_SHORT}存档_data.json")
        return []

# 固化课题分解结构
fixed_decompositions = {
    '01. 构建行业领先的 "新一代" 汽车金融系统': [
        '1.1 进行新一代核心业务模式设计，梳理和优化各业务条线展业流程、打造极致客户体验',
        '1.2 新一代核心应用架构，技术架构、数据架构设计',
        '1.3 打造标杆级速赢项目（统一授信 + 机构用信、无感购换车等）的模式与方案设计',
        '1.4 搭建基于 AI 能力和自主可控要求下的新一代技术架构及平台，及非业务需求投产配合',
        '1.5 全面优化电子签，进一步优化客户签署环节体验',
        '1.6 建设【无感金融】全旅程业务功能体验设计'
    ],
    '02. 贷后资产管理体系和统一贷后业务系统的建设': [
        '2.1 梳理现有资产管理业务需求，整理贷后资产管理体系整体架构',
        '2.2 梳理统一贷后业务及应用架构，明确各业务领域建设目标',
        '2.3 推进统一贷后各业务领域平台建设，实现业务能力落地',
        '2.4 贷后资产管理系统 - 非业务需求设计并投产'
    ],
    '03. 统一客服平台及直营数字化': [
        '3.1 以客户最优体验为核心，梳理客户金融旅程交互场景，构建全流程智能闭环客服体系蓝图',
        '3.2 针对直营痛点，减少流程断点，提升服务质效',
        '3.3 建设智能客服系统，优化AI在客服方面应用；实现多渠道一致服务，为客户提供优质的连续服务',
        '3.4 作为数字化营销的一个环节，以汽金保有客户为核心，与数字化营销、猛士、岚图品牌的联动，推出定制化增换购政策活动及“一对一顾问式推介” 的营销直营方式，实现猛士、岚图增换购建联转换率的突破'
    ],
    '04. 完善落地 "四位一体" 机制，打造金融服务护城河，提升产融协同及金融促销的延续性和黏性': [
        '4.1 设定“四位一体”会议沟通计划表，并得到品牌/集团/创格&畅行认可形成固定的机制',
        '4.2 落实乘用车相关会议制度，分月、季度、半年度、年度分时间进行开展会议事项，并对会议结果跟踪落地',
        '4.3 落实商用车相关会议制度，分月、季度、半年度、年度分时间进行开展会议事项，并对会议结果跟踪落地',
        '4.4 金融服务融入奕境品牌的成立、渠道发展、车型研发上市全流程， 并在系统支持、渠道拓展、联合金融 product 研发、批发业务、零售支持等全方位金融服务'
    ],
    '05. 二手车业务模式破局与规模化启动': [
        '5.1 打通官方认证二手车零售业务:构建从“授信→用信→贷后”的全流程SOP，支持岚图二手车快速流通与价格稳定，为后续生态建设打下基础',
        '5.2 打通岚图认证二手车批发库融业务:构建从“授信→用信→贷后”的全流程SOP，支持岚图二手车快速流通与价格稳定，为后续生态建设打下基础。',
        '5.3 实现零售二手车业务规模化突破:以核心车商平台为切入点，打通“批零联动”模式，实现零售业务规模化展业。',
        '5.4 构建二手车金融生态试点方案:与集团化平台车商合作，就“无感焕新”业务场景展开探索性合作，实现流程的全贯通'
    ],
    '06. 进一步探索海外金融业务': [
        '6.1 ①与进出口公司完成2026海外业务规划建议报告②启动同业对标，了解同业海外金融业务的盈利模式，完成同业对标报告③确定业务规划及合作机制，输出业务模式报告',
        '6.2 ① 梳理海外各大区属地潜在银行清单② 根据进出口公司的海外子公司规划，制定海外金融机构沟通路线图③根据沟通路线图，完成重点区域金融机构的拜访',
        '6.3 ①明确业务需求，确认业务方案②根据进出口公司的海外子公司规划，完成已有子公司地区属地金融展业方法论报告指引'
    ],
    '07. 构建数智化风控体系': [
        '7.1 建立大客户授信模型，统筹风险监测和预警模型-构建经销商库融授信模型',
        '7.2 建立大客户授信模型，统筹风险监测和预警模型-构建机构客户授信模型',
        '7.3 通过AI风险模型，提升客户精细分层审批-搭建机器学习模型，提升自动审批通过率',
        '7.4 增加重构信用数据平台和决策引擎平台'
    ],
    '08. 构建数字化运营能力体系': [
        '8.1 梳理战略解码成果，形成指标库',
        '8.2 根据部门绩效设置、月度运营分析会需求，筛选识别核心指标，明确指标计算公式、数据口径、取数逻辑',
        '8.3 梳理数据驾驶舱需求、数据开会需求，搭建数据驾驶舱、数据开会平台',
        '8.4 开发数字化审计模型，提升审计效率，选取征信或反洗钱等具有一定数据基础的领域搭建审计模型'
    ],
    '09. 打造数字化营销矩阵': [
        '9.1 搭建数字化营销体系',
        '9.2 提升车消费产品，持续赋能后市场生态',
        '9.3 微信公众号引流，实现百万粉丝触达',
        '9.4 品牌直播间深度联合，金融直播露出常态化',
        '9.5 进驻抖音/小红书/知乎等新媒体平台，建立汽金官方账号，并形成运营发布计划',
        '9.6 建立数字区域经理体系'
    ],
    '10. AI 数字化员工': [
        '10.1 1. 收集业务痛点，明确需求，完成技术方案设计。2. 梳理AI原子能力，明确技术路线，制定数字员工专项规划。3. 营造“人人愿用AI、人人会用AI、人人都用AI”的工作氛围。',
        '10.2 建设企业知识库',
        '10.3 投产分业务领域数字员工（数字合规官、财务数字人、采购数字人）'
    ]
}

def extract_project_number(name):
    m = re.match(r'(\d{2})\.', str(name))
    return m.group(1) if m else ''

def extract_decomp_number(d):
    return d.split(' ')[0]

def find_milestones(progress_data, pn, dn):
    res = []
    for r in progress_data:
        if r.get('计划完成时间') and TARGET_MONTH_DATE in r.get('计划完成时间'):
            pass
        else:
            continue
            
        if extract_project_number(clean_name(r.get('所属项目',''))) != pn:
            continue
        ms = r.get('课题-课题分解（关键举措）-里程碑','')
        if ms and ms.split(' ')[0].startswith(dn+'.'):
            res.append(r)
    return res

def fmt(ms_list, field):
    vals = []
    for ms in ms_list:
        v_raw = ms.get(field, '')
        if not v_raw:
            continue
        if isinstance(v_raw, dict):
            v = v_raw.get('link', v_raw.get('text', ''))
        elif isinstance(v_raw, list):
            sub_vals = []
            for item in v_raw:
                if isinstance(item, dict):
                    sub_vals.append(item.get('link', item.get('text', '')))
                else:
                    sub_vals.append(str(item))
            v = '、'.join([x for x in sub_vals if x])
        else:
            v = str(v_raw)
            
        v = v.strip().replace('\n', ' ')
        if v:
            vals.append(v)
            
    uniq = list(dict.fromkeys(vals))
    return '\n'.join(uniq) if uniq else ''

def build_progress_rows(progress_data, full_name, project_data, risk_data):
    decomps = fixed_decompositions.get(full_name, [])
    pn = extract_project_number(full_name)
    cleaned_full_name = clean_name(full_name)
    
    base_rows = []
    for d in decomps:
        dn = extract_decomp_number(d)
        ms = find_milestones(progress_data, pn, dn)
        if ms:
            mt = fmt(ms, '课题-课题分解（关键举措）-里程碑')
            kr = fmt(ms, '进展')
            st = fmt(ms, '进度管理')
            dl = fmt(ms, '交付物清单')
            url = fmt(ms, '交付物存档地址')
        else:
            mt = kr = st = dl = url = ''
        base_rows.append({
            '课题分解': d,
            '本月目标': mt,
            '本月关键成果': kr,
            '当前状态': st,
            '里程碑交付物': dl,
            '交付物存档地址': url
        })

    added_col1 = []
    for row in project_data:
        if clean_name(row.get('创新课题名称', '')) == cleaned_full_name:
            pm = row.get('项目经理', [])
            if isinstance(pm, list):
                pm_names = [x.get('name','') for x in pm if x.get('name')]
                pm_str = '、'.join(pm_names)
            else:
                pm_str = str(pm)
            added_col1.append({
                '课题名称': row.get('创新课题名称',''),
                '课题牵头人': row.get('课题牵头人',''),
                '课题owner': row.get('课题Owner',''),
                '项目经理': pm_str,
                '风险等级': row.get('风险等级',''),
                'PMO评价': row.get('PMO评价',''),
                '下月工作计划': row.get('下月工作计划',''),
                '展示材料': url_value(row.get('展示材料',''))
            })

    added_col2 = []
    for r in risk_data:
        if r.get('所属月度') == TARGET_MONTH_Y_M and clean_name(r.get('所属课题', '')) == cleaned_full_name:
            added_col2.append({
                '课题风险': r.get('课题风险',''),
                '应对计划': r.get('应对计划',''),
                '当前进展': r.get('当前进展','')
            })

    max_len = max(len(base_rows), len(added_col1), len(added_col2))
    final_rows = []
    
    for i in range(max_len):
        combined = {}
        if i < len(base_rows):
            combined.update(base_rows[i])
        else:
            combined.update({'课题分解':'', '本月目标':'', '本月关键成果':'', '当前状态':'', '里程碑交付物':'', '交付物存档地址':''})
            
        if i < len(added_col1):
            combined.update(added_col1[i])
        else:
            combined.update({'课题名称':'', '课题牵头人':'', '课题owner':'', '项目经理':'', '风险等级':'', 'PMO评价':'', '下月工作计划':'', '展示材料':''})
            
        if i < len(added_col2):
            combined.update(added_col2[i])
        else:
            combined.update({'课题风险':'', '应对计划':'', '当前进展':''})
            
        final_rows.append(combined)

    return final_rows

def save_progress_csv(rows, full_name):
    path = os.path.join(ARTIFACTS_DIR, f'{full_name}本月进度表.csv')
    headers = [
        '课题分解','本月目标','本月关键成果','当前状态','里程碑交付物','交付物存档地址',
        '课题名称', '课题牵头人', '课题owner', '项目经理', '风险等级', 'PMO评价', '下月工作计划', '展示材料',
        '课题风险', '应对计划', '当前进展'
    ]
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        w.writerows(rows)
    print(f'✅ {full_name}本月进度表.csv')

def process_all_progress(project_data, risk_data):
    progress_data = load_progress_data()
    if not progress_data:
        return
    for full_name in sorted(fixed_decompositions.keys()):
        rows = build_progress_rows(progress_data, full_name, project_data, risk_data)
        save_progress_csv(rows, full_name)

def save_csv(data, name):
    path = os.path.join(ARTIFACTS_DIR, name)
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerows(data)
    print(f'✅ {name}')



# ====================== 4. HTML 看板静态渲染 ======================
DASHBOARD_TEMPLATE_NAME = "第7次创新管理委员会.html"
DASHBOARD_TEMPLATE_PATH = os.environ.get(
    "DASHBOARD_TEMPLATE_PATH",
    os.path.join(BASE_DIR, DASHBOARD_TEMPLATE_NAME)
)
DASHBOARD_OUTPUT_PATH = os.environ.get(
    "DASHBOARD_OUTPUT_PATH",
    os.path.join(ARTIFACTS_DIR, os.path.basename(DASHBOARD_TEMPLATE_PATH))
)
CELL_LEFT_STYLE = "border: 1px solid #000; padding: 14px 12px; text-align: left; vertical-align: middle; line-height: 1.5;"
CELL_CENTER_STYLE = "border: 1px solid #000; padding: 14px 12px; text-align: center; vertical-align: middle; line-height: 1.5;"
CELL_DONE_STYLE = "border: 1px solid #000; padding: 14px 12px; text-align: left; vertical-align: middle; line-height: 1.5; background-color: #dcfce7;"

def read_json_rows(name: str) -> list[dict]:
    with open(os.path.join(BASE_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)["tables"][0]["rows"]


def report_meta() -> dict:
    anchor_date = datetime.now() - timedelta(days=15)
    year = anchor_date.year
    month = anchor_date.month
    last_day = (datetime(year + (month == 12), month % 12 + 1, 1) - timedelta(days=1)).day
    quarter = f"Q{(month - 1) // 3 + 1}"
    return {
        "year": year,
        "month": month,
        "target_month": f"{year}-{month:02d}",
        "cutoff": f"{year}年{month}月{last_day}日",
        "quarter": quarter,
        "meeting_no": month + 2,
    }


def esc(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        value = "、".join(str(item) for item in value if item is not None)
    elif isinstance(value, dict):
        value = value.get("text") or value.get("link") or ""
    return html.escape(str(value).replace("\r\n", "\n").replace("\r", "\n").strip()).replace("\n", "<br>")


def text_value(value) -> str:
    return str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()


def inline_meta_value(value) -> str:
    return re.sub(r"\s*、\s*", "、", text_value(value).replace("\n", " "))


def url_value(value) -> str:
    if not value:
        return ""
    if isinstance(value, dict):
        return text_value(value.get("link") or value.get("url") or value.get("text"))
    if isinstance(value, list):
        for item in value:
            url = url_value(item)
            if url:
                return url
        return ""
    return text_value(value)


def normalize_name(name: str) -> str:
    return (
        str(name or "")
        .replace("“", '"')
        .replace("”", '"')
        .replace(" ", "")
        .replace("AI数字化员工", "AI 数字化员工")
        .strip()
    )


def pct_number(value: str) -> float:
    try:
        return float(str(value).replace("%", ""))
    except ValueError:
        return 0.0


def pct_text(value: str | float, digits: int = 1) -> str:
    n = value if isinstance(value, float) else pct_number(value)
    if abs(n - 100) < 0.005:
        return "100%"
    return f"{n:.{digits}f}%"


def count_pair(desc: str) -> str:
    m = re.search(r"已完成(\d+)个/总计(\d+)个", desc or "")
    return f"{m.group(1)}/{m.group(2)}" if m else ""


def risk_view(raw: str) -> dict:
    text = str(raw or "").strip()
    if re.search(r"高|严重|重大|红", text):
        return {"class": "high", "color": "#E74C3C", "label": "🔴 高风险", "short": "高风险"}
    if re.search(r"中", text):
        return {"class": "medium", "color": "#FF7A00", "label": "🟠 中风险", "short": "中风险"}
    if re.search(r"轻微|低|黄", text):
        return {"class": "low", "color": "#FFB300", "label": "🟡 轻微风险", "short": "轻微风险"}
    return {"class": "normal", "color": "#2ECC71", "label": "🟢 正常", "short": "正常推进"}


def progress_class(rate: str | float) -> str:
    n = rate if isinstance(rate, float) else pct_number(rate)
    if n >= 80:
        return "green"
    if n >= 60:
        return "orange"
    return "red"


def status_view(status: str) -> dict:
    text = status or ""
    if "提前" in text:
        return {"class": "early", "icon": "🎉", "label": "🎉 提前完成"}
    if "延期" in text:
        return {
            "class": "delay",
            "icon": "⚠️",
            "label": "🚨 已延期",
            "icon_style": ' style="color: #dc2626;"',
            "status_style": ' style="background:#fee2e2; padding:4px 10px; border-radius:12px; font-size:12px; color:#b91c1c;"',
        }
    if "完成" in text:
        return {"class": "done", "icon": "✅", "label": "✅ 已完成"}
    return {"class": "progress", "icon": "📋", "label": esc(text)}


def load_milestone_metrics(progress_data: list[dict], project_data: list[dict]) -> tuple[dict, list[list[str]]]:
    table = generate_milestone_completion_table(progress_data, project_data)
    metrics = {row[0]: {"value": row[1], "desc": row[2]} for row in table[1:] if row}
    return metrics, table


def update_slide_1_2(html_text: str, meta: dict, metrics: dict, metric_table: list[list[str]]) -> str:
    q = meta["quarter"]
    month = meta["month"]
    overall = metrics.get(f"里程碑总体完成率-{q}TD", {})
    system = metrics.get(f"系统建设相关里程碑完成率-{q}TD", {})
    early = metrics.get(f"提前完成里程碑数量-{q}", {})
    month_rate = metrics.get("里程碑总体完成率-本月", {})
    month_total = metrics.get("本月总里程碑数量", {}).get("value", "")
    month_done = metrics.get("本月完成里程碑数量", {}).get("value", "")
    month_delay = metrics.get("本月延期里程碑数量", {}).get("value", "")
    month_early = metrics.get("本月提前完成里程碑数量", {}).get("value", "")
    stats_total_style = 'style="font-weight:700;"'
    stats_done_style = 'style="color:#0F3A8A; font-weight:700;"'
    stats_early_style = 'style="color:#0F3A8A; font-weight:700; text-shadow:0 0 8px rgba(37,99,235,0.45);"'
    stats_delay_style = 'style="color:#991B1B; font-weight:700;"'
    month_stats_html = (
        '<span class="progress-stats" data-dashboard-field="month-status-stats" style="font-size: 18px;">'
        f'共<strong {stats_total_style}>{month_total}</strong>项 · '
        f'已完成<strong {stats_done_style}>{month_done}</strong>项，'
        f'提前<strong {stats_early_style}>{month_early}</strong>项，'
        f'<strong {stats_delay_style}>{month_delay}</strong>项延期'
        '</span>'
    )

    replacements = {
        r'<div class="cover-badge">\s*<span[^>]*>.*?</span>\s*<span data-dashboard-field="meeting-title">.*?</span>\s*</div>': rf'<div class="cover-badge" style="font-size: 22px; gap: 12px; padding: 14px 26px;"><span style="font-size: 28px; line-height: 1;">📊</span><span data-dashboard-field="meeting-title">{meta["year"]}年第{meta["meeting_no"]}次创新管理委员会</span></div>',
        r'<p style="font-size: 16px; color: rgba\(255,255,255,0\.8\); margin-bottom: 6px;">东风汽车金融有限公司</p>': '<p style="font-size: 24px; color: rgba(255,255,255,0.86); margin-bottom: 10px;">东风汽车金融有限公司</p>',
        r'<p style="font-size: 13px; color: rgba\(255,255,255,0\.6\);" data-dashboard-field="report截止日">.*?</p>': rf'<p style="font-size: 20px; color: rgba(255,255,255,0.72);" data-dashboard-field="report截止日">截至 {meta["cutoff"]}</p>',
        r'(<p class="slide-subtitle" data-dashboard-field="quarter-subtitle">).*?(</p>)': rf"\g<1>{q}季度至今各课题里程碑完成情况\2",
        r'(<div class="kpi-value" data-dashboard-field="quarter-overall-count">).*?(</div>)': rf"\g<1>{count_pair(overall.get('desc', ''))}\2",
        r'(<div class="kpi-label" data-dashboard-field="quarter-overall-label">).*?(</div>)': rf"\g<1>{q}里程碑完成率\2",
        r'(<div class="kpi-right-pct" data-dashboard-field="quarter-overall-rate">).*?(</div>)': rf"\g<1>{pct_text(overall.get('value', ''))}\2",
        r'(<div class="kpi-value" data-dashboard-field="quarter-system-count">).*?(</div>)': rf"\g<1>{count_pair(system.get('desc', ''))}\2",
        r'(<div class="kpi-label" style="font-size:14px;" data-dashboard-field="quarter-system-label">).*?(</div>)': rf"\g<1>{q}系统建设里程碑完成率\2",
        r'(<div class="kpi-right-pct" data-dashboard-field="quarter-system-rate">).*?(</div>)': rf"\g<1>{pct_text(system.get('value', ''), 0)}\2",
        r'(<div class="kpi-value" data-dashboard-field="quarter-early-count">).*?(</div>)': rf"\g<1>{early.get('value', '')}\2",
        r'(<span class="progress-title" data-dashboard-field="month-status-title">).*?(</span>)': rf"\g<1>{month}月里程碑状态分布\2",
        r'<span class="progress-stats" data-dashboard-field="month-status-stats"(?: style="[^"]*")?>.*?</span>': month_stats_html,
        r'(<div class="progress-bar [^"]*" style="width: )[^"]*(" data-dashboard-field="month-status-bar"></div>)': rf"\g<1>{pct_number(month_rate.get('value', ''))}%\2",
    }
    for pattern, repl in replacements.items():
        html_text = re.sub(pattern, repl, html_text, count=1, flags=re.S)

    projects: dict[str, dict] = {}
    try:
        start = next(i for i, row in enumerate(metric_table) if row[0] == "各课题里程碑完成率-本月")
    except StopIteration:
        start = -1
    if start >= 0:
        for row in metric_table[start + 1 :]:
            projects[normalize_name(row[0])] = {"rate": row[1], "risk": row[2]}

    def replace_subject_segment(match: re.Match) -> str:
        segment = match.group(0)
        name_match = re.search(r'<span class="subject-name">([^<]+)</span>', segment)
        if not name_match:
            return segment
        project = projects.get(normalize_name(name_match.group(1)))
        if not project:
            return segment
        view = risk_view(project["risk"])
        rate = pct_text(project["rate"], 0)
        width = f"{pct_number(project['rate'])}%"
        fill = progress_class(project["rate"])
        segment = re.sub(
            r'<span class="risk-badge [^"]*" style="color:\s*[^;]+;([^"]*)">.*?</span>',
            rf'<span class="risk-badge {view["class"]}" style="color: {view["color"]};\1">{view["label"]}</span>',
            segment,
            count=1,
            flags=re.S,
        )
        segment = re.sub(
            r'<div class="subject-progress-fill [^"]+" style="width: [^"]*"></div>',
            rf'<div class="subject-progress-fill {fill}" style="width: {width}"></div>',
            segment,
            count=1,
        )
        segment = re.sub(r'<span class="subject-progress-value">.*?</span>', rf'<span class="subject-progress-value">{rate}</span>', segment, count=1, flags=re.S)
        return segment

    slide2_match = re.search(r'<section class="slide" data-slide="2">.*?</section>', html_text, re.S)
    if slide2_match:
        slide2 = slide2_match.group(0)
        slide2 = re.sub(r'<div class="subject-card">.*?(?=\n\s*<div class="subject-card">|\n\s*</div>\s*</div>\s*</div>\s*</section>)', replace_subject_segment, slide2, flags=re.S)
        html_text = html_text[: slide2_match.start()] + slide2 + html_text[slide2_match.end() :]

    html_text = re.sub(
        r'\n<script>\s*const DASHBOARD_MILESTONE_COMPLETION_CSV = [\s\S]*?loadMilestoneCompletionRows\(\)\.then\(updateMilestoneDashboard\);\s*</script>\n',
        "\n",
        html_text,
        count=1,
    )
    return html_text


def load_zhizhai_rows(target_month: str) -> list[dict[str, str]]:
    rows = read_json_rows("历次创新委课题&部门指示.json")
    grouped: OrderedDict[str, list[dict[str, str]]] = OrderedDict()
    for row in rows:
        if row.get("所属月份") != target_month:
            continue
        depts = row.get("相关课题/部门") or ["未分类"]
        if not isinstance(depts, list):
            depts = [depts]
        for dept in depts:
            grouped.setdefault(str(dept), []).append(
                {
                    "相关课题/部门": str(dept),
                    "跟踪事项": str(row.get("跟踪事项", "")).replace("\n", " "),
                    "事项类型": str(row.get("事项类型", "")),
                    "提出领导": str(row.get("提出领导", "")),
                    "落实情况": str(row.get("落实情况", "")),
                }
            )

    final_rows: list[dict[str, str]] = []
    for dept in sorted(grouped.keys()):
        final_rows.extend(sorted(grouped[dept], key=zhizhai_sort_key))
    return final_rows


def build_zhizhai_tbody(rows: list[dict[str, str]]) -> str:
    groups: OrderedDict[str, list[dict[str, str]]] = OrderedDict()
    for row in rows:
        groups.setdefault(row["相关课题/部门"], []).append(row)

    lines = ["          <tbody>"]
    for dept, dept_rows in groups.items():
        rowspan = len(dept_rows)
        for index, row in enumerate(dept_rows):
            lines.append("            <tr>")
            if index == 0:
                rowspan_attr = f' rowspan="{rowspan}"' if rowspan > 1 else ""
                lines.append(f'              <td{rowspan_attr} style="{CELL_LEFT_STYLE}">{esc(dept)}</td>')
            lines.append(f'              <td style="{CELL_LEFT_STYLE}">{esc(row["跟踪事项"])}</td>')
            lines.append(f'              <td style="{CELL_CENTER_STYLE}">{esc(row["事项类型"])}</td>')
            lines.append(f'              <td style="{CELL_CENTER_STYLE}">{esc(row["提出领导"])}</td>')
            lines.append(f'              <td style="{CELL_DONE_STYLE}">{esc(row["落实情况"])}</td>')
            lines.append("            </tr>")
    lines.append("          </tbody>")
    return "\n".join(lines)


def build_slide3(meta: dict, rows: list[dict[str, str]]) -> str:
    return f'''<section class="slide" data-slide="3">
<div class="slide-inner" style="padding: 0; gap: 0; position: relative;">
    <div class="detail-header" style="border-radius: 0; margin-bottom: 0;">
      <div class="detail-header-content">
        <h1 class="detail-title">创新委指示跟踪</h1>
        <div class="detail-meta">
          <div class="detail-meta-item"><span>📅</span><span>统计周期：{meta["year"]}年{meta["month"]}月</span></div>
        </div>
      </div>
    </div>
    <div class="slide-main" style="padding: 20px;">
      <div class="track-table-container" style="max-height: calc(var(--deck-design-height) - 180px); overflow-y: auto; background: #fff; border-radius: 15px; padding: 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
        <table class="track-table" style="width: 100%; border-collapse: collapse; font-size: 16px; color: #000;">
          <thead>
            <tr style="background: #2563eb; color: #fff;">
              <th style="width: 18%; border: 1px solid #000; padding: 14px 12px; text-align: center; vertical-align: middle; line-height: 1.5; font-weight: 700; position: sticky; top: 0; z-index: 10; background: #2563eb;">相关课题/部门</th>
              <th style="width: 37%; border: 1px solid #000; padding: 14px 12px; text-align: center; vertical-align: middle; line-height: 1.5; font-weight: 700; position: sticky; top: 0; z-index: 10; background: #2563eb;">跟踪事项</th>
              <th style="width: 10%; border: 1px solid #000; padding: 14px 12px; text-align: center; vertical-align: middle; line-height: 1.5; font-weight: 700; position: sticky; top: 0; z-index: 10; background: #2563eb;">事项类型</th>
              <th style="width: 10%; border: 1px solid #000; padding: 14px 12px; text-align: center; vertical-align: middle; line-height: 1.5; font-weight: 700; position: sticky; top: 0; z-index: 10; background: #2563eb;">提出人</th>
              <th style="width: 25%; border: 1px solid #000; padding: 14px 12px; text-align: center; vertical-align: middle; line-height: 1.5; font-weight: 700; position: sticky; top: 0; z-index: 10; background: #2563eb;">落实情况</th>
            </tr>
          </thead>
{build_zhizhai_tbody(rows)}
        </table>
      </div>
    </div>
  </div>
</section>'''


def split_plan_items(plan: str) -> list[str]:
    text = text_value(plan)
    if not text:
        return []
    matches = list(re.finditer(r"(?m)(?:^|\n)\s*(\d+)[.、．]\s*", text))
    if not matches:
        return [text]
    items = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        item = text[start:end].strip()
        if item:
            items.append(item)
    return items


def parse_plan_item(item: str) -> dict[str, str]:
    text = text_value(item).strip("()（） ")
    m = re.search(r"标题\s*[:：]\s*(.*?)\s*正文\s*[:：]\s*([\s\S]*)", text)
    if not m:
        return {"title": "", "body": text}
    return {
        "title": text_value(m.group(1)),
        "body": text_value(m.group(2)),
    }


def plan_title(index: int, item: str) -> str:
    base = re.split(r"[，,。；;：:]", item, maxsplit=1)[0].strip()
    if len(base) > 32:
        base = base[:32] + "..."
    return f"{index}. {base}"


def build_plan_cards(plan: str) -> str:
    items = split_plan_items(plan)
    if not items:
        items = ["暂无下月工作计划"]
    lines = ['                <div class="plan-grid">']
    for index, item in enumerate(items, 1):
        parsed = parse_plan_item(item)
        title = f"{index}. {parsed['title']}" if parsed["title"] else plan_title(index, item)
        body = parsed["body"] or item
        lines.extend(
            [
                '                    <div class="plan-card">',
                '                        <div class="plan-header">',
                '                            <div class="plan-icon">📋</div>',
                f'                            <div class="plan-title">{esc(title)}</div>',
                "                        </div>",
                '                        <ul class="plan-list">',
                f"                            <li>{esc(body)}</li>",
                "                        </ul>",
                "                    </div>",
            ]
        )
    lines.append("                </div>")
    return "\n".join(lines)


def build_milestone_items(rows: list[dict]) -> str:
    lines = []
    for row in rows:
        status = status_view(row.get("当前状态", ""))
        icon_style = status.get("icon_style", "")
        status_style = status.get("status_style", "")
        lines.extend(
            [
                '                        <div class="p4-item" style="height: 100%;">',
                f'                            <div class="p4-item-icon {status["class"]}"{icon_style}>{status["icon"]}</div>',
                '                            <div class="p4-item-content">',
                f'                                <div class="p4-item-title">{esc(row.get("课题分解", ""))}</div>',
                f'                                <div class="p4-item-desc">{esc(row.get("本月目标", ""))}</div>',
                "                            </div>",
                f'                            <span class="p4-item-status {status["class"]}"{status_style}>{status["label"]}</span>',
                "                        </div>",
            ]
        )
    return "\n".join(lines)


def js_string(value: str) -> str:
    return json.dumps(value or "", ensure_ascii=False)


def build_showcase_section(url: str) -> str:
    url = text_value(url)
    if not url:
        return ""
    return f'''            <!-- ==== 成果展示 ==== -->
            <div style="margin-bottom: 30px;">
                <h2 style="font-size: 20px; font-weight: 700; margin-bottom: 16px; color: #111827;">成果展示</h2>
                <div style="background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 15px; padding: 24px; text-align: center; cursor: pointer; transition: all 0.2s ease;" onclick="window.open({html.escape(js_string(url))}, '_blank')" onmouseover="this.style.borderColor='var(--primary-blue)'; this.style.boxShadow='0 4px 12px rgba(37,99,235,0.1)';" onmouseout="this.style.borderColor='var(--card-border)'; this.style.boxShadow='none';">
                    <span style="font-size: 16px; color: var(--primary-blue); font-weight: 600;">展示材料</span>
                </div>
            </div>
'''


def build_deliverable_items(rows: list[dict]) -> str:
    lines = []
    for row in rows:
        status = status_view(row.get("当前状态", ""))
        icon_style = status.get("icon_style", "")
        url = text_value(row.get("交付物存档地址", ""))
        onclick = f' onclick="window.open({html.escape(js_string(url))}, \'_blank\')"' if url else ""
        cursor = "cursor: pointer; " if url else ""
        lines.extend(
            [
                f'                        <div class="p4-item" style="{cursor}height: 100%;"{onclick}>',
                f'                            <div class="p4-item-icon {status["class"]}"{icon_style}>{status["icon"]}</div>',
                '                            <div class="p4-item-content">',
                f'                                <div class="p4-item-title">{esc(row.get("本月关键成果", ""))}</div>',
                f'                                <div class="p4-item-desc">{esc("交付物：" + text_value(row.get("里程碑交付物", "")) if text_value(row.get("里程碑交付物", "")) else "")}</div>',
                "                            </div>",
                "                        </div>",
            ]
        )
    return "\n".join(lines)


def build_milestone_pair_rows(rows: list[dict]) -> str:
    lines = []
    for row in rows:
        status = status_view(row.get("当前状态", ""))
        icon_style = status.get("icon_style", "")
        status_style = status.get("status_style", "")
        url = text_value(row.get("交付物存档地址", ""))
        onclick = f' onclick="window.open({html.escape(js_string(url))}, \'_blank\')"' if url else ""
        cursor = "cursor: pointer; " if url else ""
        lines.extend(
            [
                '                    <div class="p4-milestone-row-shell">',
                '                        <div class="p4-item" style="height: 100%;">',
                f'                            <div class="p4-item-icon {status["class"]}"{icon_style}>{status["icon"]}</div>',
                '                            <div class="p4-item-content">',
                f'                                <div class="p4-item-title">{esc(row.get("课题分解", ""))}</div>',
                f'                                <div class="p4-item-desc">{esc(row.get("本月目标", ""))}</div>',
                "                            </div>",
                f'                            <span class="p4-item-status {status["class"]}"{status_style}>{status["label"]}</span>',
                "                        </div>",
                f'                        <div class="p4-item" style="{cursor}height: 100%;"{onclick}>',
                f'                            <div class="p4-item-icon {status["class"]}"{icon_style}>{status["icon"]}</div>',
                '                            <div class="p4-item-content">',
                f'                                <div class="p4-item-title">{esc(row.get("本月关键成果", ""))}</div>',
                f'                                <div class="p4-item-desc">{esc("交付物：" + text_value(row.get("里程碑交付物", "")) if text_value(row.get("里程碑交付物", "")) else "")}</div>',
                "                            </div>",
                "                        </div>",
                "                    </div>",
            ]
        )
    return "\n".join(lines)


def pmo_colors(risk: str) -> dict[str, str]:
    if re.search(r"高|严重|重大|红", risk or ""):
        return {"bg": "#fee2e2", "border": "#fecaca", "label": "#dc2626", "text": "#991b1b"}
    if re.search(r"中", risk or ""):
        return {"bg": "#fff4e5", "border": "#ffcc80", "label": "#ff6700", "text": "#cc5500"}
    if re.search(r"轻微|低|黄", risk or ""):
        return {"bg": "#fef9c3", "border": "#fde68a", "label": "#ca8a04", "text": "#854d0e"}
    return {"bg": "#dcfce7", "border": "#86efac", "label": "#15803d", "text": "#166534"}


def build_risk_rows(rows: list[dict]) -> str:
    risk_rows = [r for r in rows if text_value(r.get("课题风险"))]
    if not risk_rows:
        return '                        <div style="background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 15px; padding: 20px; text-align: center; color: var(--text-muted);">暂无本月风险项</div>'
    blocks = []
    for index, row in enumerate(risk_rows, 1):
        margin = " margin-bottom: 20px;" if index < len(risk_rows) else ""
        blocks.append(
            f'''                        <div style="display: grid; grid-template-columns: 40% 35% 22%; gap: 20px;{margin}">
                            <div style="background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 15px; padding: 20px; height: 100%;">
                                <div class="risk-row-label">⚠️ 风险{index}</div>
                                <div class="risk-row-action">{esc(row.get("课题风险", ""))}</div>
                            </div>
                            <div style="background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 15px; padding: 20px; height: 100%;">
                                <div class="risk-row-label">💡 应对措施</div>
                                <div class="risk-row-action">{esc(row.get("应对计划", ""))}</div>
                            </div>
                            <div style="background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 15px; padding: 20px; height: 100%; color: #000;">
                                <div class="risk-row-label">📌 当前进展</div>
                                <div class="risk-row-action">{esc(row.get("当前进展", ""))}</div>
                            </div>
                        </div>'''
        )
    return "\n".join(blocks)


def build_project_slide(project_rows: list[dict], slide_no: int) -> str:
    info = next((r for r in project_rows if text_value(r.get("课题名称"))), project_rows[0])
    project_name = text_value(info.get("课题名称"))
    project_no_match = re.match(r"0?(\d+)\.\s*(.*)", project_name)
    project_no = project_no_match.group(1) if project_no_match else "1"
    project_title = project_no_match.group(2) if project_no_match else project_name
    risk = text_value(info.get("风险等级"))
    risk_short = risk_view(risk)["short"]
    pmo = text_value(info.get("PMO评价"))
    plan = text_value(info.get("下月工作计划"))
    showcase_url = text_value(info.get("展示材料"))
    owner = inline_meta_value(info.get("课题owner", ""))
    project_manager = inline_meta_value(info.get("项目经理", ""))
    milestone_rows = [r for r in project_rows if text_value(r.get("当前状态"))]
    total = len(milestone_rows)
    completed = len([r for r in milestone_rows if "完成" in text_value(r.get("当前状态"))])
    early = len([r for r in milestone_rows if "提前" in text_value(r.get("当前状态"))])
    rate = (completed / total * 100) if total else 0
    grid_rows = max(len(milestone_rows), 1)
    colors = pmo_colors(risk)
    pmo_text = risk_short if risk_short == "正常推进" else (f"{risk_short}，{pmo}" if pmo else risk_short)

    return f'''<section class="slide" data-slide="{slide_no}">
    <div class="slide-inner">
        <div class="detail-header">
            <div class="detail-header-content">
                <h1 class="detail-title">课题{project_no}：{esc(project_title)}</h1>
                <div class="detail-meta">
                    <div class="detail-meta-item"><span>👤</span><span>课题牵头人：{esc(info.get("课题牵头人", ""))}</span></div>
                    <div class="detail-meta-item"><span>📋</span><span>Owner：{esc(owner)} 📊 PM：{esc(project_manager)}</span></div>
                    <div class="detail-meta-item"><span>⚠️</span><span>风险等级：{esc(risk_short)}</span></div>
                    <div class="detail-meta-item"><span>📊</span><span>里程碑完成率：{pct_text(rate, 0)}</span></div>
                </div>
            </div>
        </div>

        <div class="slide-main" style="overflow-y: auto; padding-bottom: 20px;">
            <!-- ==== 本月里程碑 ==== -->
            <div style="margin-bottom: 30px;">
                <h2 style="font-size: 20px; font-weight: 700; margin-bottom: 16px; color: #111827;">本月里程碑完成情况</h2>
                <div class="kpi-grid" style="margin-bottom: 16px; grid-template-columns: repeat(3,1fr); display: grid; gap: 20px;">
                    <div class="kpi-card" style="background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 15px; padding: 20px; display: flex; align-items: center; gap: 16px;">
                        <div class="kpi-icon green" style="width: 48px; height: 48px; border-radius: 12px; background: #E8FFEA; color: var(--accent-success); display: flex; align-items: center; justify-content: center; font-size: 24px;">✅</div>
                        <div class="kpi-content">
                            <div class="kpi-value" style="font-size: 24px; font-weight: 700; color: var(--text);">{completed}</div>
                            <div class="kpi-label" style="font-size: 14px; color: var(--text-muted);">已完成里程碑</div>
                        </div>
                    </div>
                    <div class="kpi-card" style="background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 15px; padding: 20px; display: flex; align-items: center; gap: 16px;">
                        <div class="kpi-icon purple" style="width: 48px; height: 48px; border-radius: 12px; background: #F9F0FF; color: var(--primary-purple); display: flex; align-items: center; justify-content: center; font-size: 24px;">🎉</div>
                        <div class="kpi-content">
                            <div class="kpi-value" style="font-size: 24px; font-weight: 700; color: var(--text);">{early}</div>
                            <div class="kpi-label" style="font-size: 14px; color: var(--text-muted);">提前完成</div>
                        </div>
                    </div>
                    <div class="kpi-card" style="background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 15px; padding: 20px; display: flex; align-items: center; gap: 16px;">
                        <div class="kpi-icon blue" style="width: 48px; height: 48px; border-radius: 12px; background: #E8F3FF; color: var(--primary-blue); display: flex; align-items: center; justify-content: center; font-size: 24px;">📋</div>
                        <div class="kpi-content">
                            <div class="kpi-value" style="font-size: 24px; font-weight: 700; color: var(--text);">{pct_text(rate, 0)}</div>
                            <div class="kpi-label" style="font-size: 14px; color: var(--text-muted);">里程碑完成率</div>
                        </div>
                    </div>
                </div>

                <div class="p4-milestone-pair-list">
                    <div class="p4-milestone-pair-head">
                        <div class="p4-col-header">📌 本月里程碑</div>
                        <div class="p4-col-header"></div>
                    </div>
{build_milestone_pair_rows(milestone_rows)}
                </div>
            </div>

{build_showcase_section(showcase_url)}
            <!-- ==== 下月行动计划 ==== -->
            <div style="margin-bottom: 30px;">
                <h2 style="font-size: 20px; font-weight: 700; margin-bottom: 16px; color: #111827;">下月行动计划</h2>
{build_plan_cards(plan)}
            </div>

            <!-- ==== 风险与PMO总结 ==== -->
            <div>
                <h2 style="font-size: 20px; font-weight: 700; margin-bottom: 16px; color: #111827;">课题风险与PMO总结</h2>
                <div style="display: flex; flex-direction: column; justify-content: space-between;">
                    <div style="overflow-y: auto;">
{build_risk_rows(project_rows)}
                    </div>
                    <div style="flex-shrink: 0; margin-top: 20px; display: grid; grid-template-columns: 10% 90%; gap: 10px; align-items: start; background: {colors["bg"]}; border: 1px solid {colors["border"]}; border-radius: 15px; padding: 20px;">
                        <div style="font-weight: 700; color: {colors["label"]}; text-align: right; line-height: 1.5;">PMO总结：</div>
                        <div style="color: {colors["text"]}; line-height: 1.5;">{esc(pmo_text)}</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>'''


def replace_section(html_text: str, slide_no: int, new_section: str, next_slide_no: int | None = None) -> str:
    if next_slide_no:
        pattern = rf'<section class="slide" data-slide="{slide_no}">.*?</section>\s*(?=<section class="slide" data-slide="{next_slide_no}">)'
    else:
        pattern = rf'<section class="slide" data-slide="{slide_no}">.*?</section>'
    updated, count = re.subn(pattern, new_section + "\n", html_text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f'未能唯一定位 data-slide="{slide_no}" 区块')
    return updated


def render_dashboard_html(template_path=None, output_path=None):
    template_path = template_path or DASHBOARD_TEMPLATE_PATH
    output_path = output_path or DASHBOARD_OUTPUT_PATH
    meta = report_meta()
    progress_data = load_progress_data()
    if not progress_data:
        print("❌ 因缺少看板数据，未生成 HTML 看板。")
        return

    if not os.path.exists(template_path):
        print(f"❌ 未找到 HTML 看板模板: {template_path}")
        print("   -> 请将 HTML 模板放在 Fetch_Data.py 同级目录，或设置 DASHBOARD_TEMPLATE_PATH。")
        return

    try:
        project_data = read_json_rows("课题清单.json")
    except Exception:
        project_data = []

    try:
        risk_data = read_json_rows("课题风险与指摘落实（课题组）.json")
    except Exception:
        risk_data = []

    metrics, metric_table = load_milestone_metrics(progress_data, project_data)
    zhizhai_rows = load_zhizhai_rows(meta["target_month"])

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(template_path, "r", encoding="utf-8") as f:
        html_text = f.read()

    html_text = update_slide_1_2(html_text, meta, metrics, metric_table)
    html_text = replace_section(html_text, 3, build_slide3(meta, zhizhai_rows), next_slide_no=4)

    project_counts = []
    for offset, full_name in enumerate(sorted(fixed_decompositions.keys()), start=4):
        project_rows = build_progress_rows(progress_data, full_name, project_data, risk_data)
        next_slide = offset + 1 if offset < 13 else None
        html_text = replace_section(html_text, offset, build_project_slide(project_rows, offset), next_slide_no=next_slide)
        project_counts.append(len([r for r in project_rows if text_value(r.get("当前状态"))]))

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_text)

    print(f"✅ HTML看板已生成: {output_path}")
    print(f"   -> 模板来源: {template_path}")
    print(f"   -> 指摘落实 {len(zhizhai_rows)} 条")
    print(f"   -> 课题详情页里程碑数: {project_counts}")

# ====================== 主入口 ======================
if __name__ == "__main__":
    print('=== 开始抽取并生成 artifacts 目录下 12 个CSV ===')
    
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    
    progress_data = load_progress_data()

    try:
        json_path = os.path.join(BASE_DIR, '课题清单.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            project_data = json.load(f)['tables'][0]['rows']
    except:
        project_data = []

    try:
        json_path = os.path.join(BASE_DIR, '课题风险与指摘落实（课题组）.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            risk_data = json.load(f)['tables'][0]['rows']
    except:
        risk_data = []

    if progress_data:
        # 1. 里程碑完成率指标统计表
        save_csv(generate_milestone_completion_table(progress_data, project_data), '里程碑完成率指标统计表.csv')
        # 2. 指摘落实表
        process_zhizhai()
        # 3. 10个扩展进度表
        process_all_progress(project_data, risk_data)
        # 4. 静态渲染 HTML 看板
        render_dashboard_html()
        print(f'\n🎉 全部 12 个 CSV 报表与 HTML 看板已完美生成！')
    else:
        print("\n❌ 因缺少看板数据，未生成任何报表，请确保数据源存在并命名规范。")
