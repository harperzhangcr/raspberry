# Project Memory

## Long-Term Notes
- Active collection model workbook is in this directory: `贷后风险等级卡+处置动作卡0625_动作角色编码版.xlsx`.
- The user is building post-loan risk/action cards for passenger vehicle and four commercial vehicle lines.
- Current task family often involves extracting, coding, and validating action/rule logic from Excel workbooks.
- Temporary analysis convention: ACT001, ACT011, ACT012, and ACT013 can be treated as one broad action category named `外呼` for rule summarization, without changing source tables.
- Added `动作大类` to `action_role_coding_final/动作编码表.csv` and the main workbook action cards. ACT001/ACT011/ACT012/ACT013 map to `外呼（ACT001/ACT011/ACT012/ACT013）`; other rows use `统一动作（动作代码）`.
- Rule correction: passenger conventional `ACT020 提交委外电催申请` and passenger abnormal `ACT126 申请委外` must include `未进入委外阶段`; tracking/supervision actions remain gated by `进入委外阶段`.
- Confirmed regular action categories: `发函（ACT022/ACT025）`, `锁车（ACT026/ACT027/ACT037）`, and `委外（ACT023/ACT017/ACT018/ACT020/ACT034）`; these are written to the action category field.
- Confirmed regular litigation category: `诉讼（ACT024/ACT033）` for `梳理并发送诉讼清单至区域` and `诉讼执行`.
- Requirements for rebuilding dual-card simultaneous trigger tables: treat `客户阶段=新增` and `客户阶段=存量` as mutually exclusive; group similar trigger conditions together; deduplicate repeated actions in the output. Do not reuse the old five-line dual-card table format unless explicitly requested.
- Created sample rebuilt dual-card simultaneous trigger table for `商用车-轻卡-燃油` at `轻卡-燃油_双卡同时触发情况表_新版.xlsx`; structure uses one sheet per line, A-C merged for abnormal-card axis, D-H as unmerged regular-card detail rows, with dedup/conflict markers.
- Updated dual-card table convention: do not use `已归并` markers; `冲突提示` only contains business markers such as委外/诉讼/投诉/相似动作; concrete duplicate action removal is marked separately in the final column `去重提示`.
- Created full five-line rebuilt dual-card simultaneous trigger table at `五条线_双卡同时触发情况表_新版.xlsx`, with one sheet each for `乘用车`, `中重卡-担保`, `中重卡-非担保`, `轻卡-燃油`, and `轻卡-新能源`.
- Dedup marker convention update: if the same action is repeated only because passenger regular rules are split across `低风险/中风险/高风险`, do not mark `去重提示`; keep the action deduplicated in display but only mark duplicate actions caused by non-risk-tier conditions.
- In the rebuilt dual-card table, `常规大类备注` for merged regular categories should use the rule-summary format such as `发函（中重卡-担保首次逾期当月 + 逾期15天 + 无有效期内还款承诺下梳理发函清单并发送至区域；...）`, rather than only listing deduplicated actions.
- In merged regular category notes, separate each `条件下动作` item with a line break rather than semicolons.
- Conflict marker convention update: `冲突提示` must include `收车相关` and `车辆处置相关` when the abnormal/regular action text involves those actions. If both `收车` and `车辆处置` appear in the same row, add `明确冲突：收车与车辆处置冲突` and fill that conflict cell dark red. Similar-action detection should be based on action text/category text, not merely abnormal type wording.
- Confirmed similar-action pairs to retain in `冲突提示`: `人工外呼（异常处置）（ACT100）` vs `外呼（ACT001/ACT011/ACT012/ACT013）`; `诉讼执行（ACT128）` vs `人工发催收施压短信（申请上门、诉讼）（ACT004）`; `诉讼执行（ACT128）` vs `诉讼（ACT024/ACT033）`; `申请委外（ACT126）` vs `委外（ACT023/ACT017/ACT018/ACT020/ACT034）`; `发送工单给区域（协调经销商督促客户保存回访号码）（ACT105）` vs `外呼（ACT001/ACT011/ACT012/ACT013）`; `发送工单给区域（协调经销商告知客户回访计划）（ACT104）` vs `外呼（ACT001/ACT011/ACT012/ACT013）`; `发送工单给区域（核实情况，记录台帐，反馈区域，制定催收计划）（ACT111）` vs `反馈区域（ACT014）`; `发送工单（委外上门）（ACT108）` vs `委外（ACT023/ACT017/ACT018/ACT020/ACT034）`; `发送工单（诉讼）（ACT115）` vs `诉讼（ACT024/ACT033）`. All other reviewed candidate pairs are not similar.
- Final display convention for `五条线_双卡同时触发情况表_新版.xlsx`: remove the `去重提示` column; keep `常规大类备注（含动作与角色）` and `动作关系` in the workbook but hidden.
