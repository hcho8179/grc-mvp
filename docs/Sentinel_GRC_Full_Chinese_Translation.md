# Greenlight — 简报

一份 200 道题的安全问卷，人工填写通常需要 3 天。Greenlight 在 1 小时内完成——而且你做的每一份问卷，都让下一份变得更快。

---

## 问题所在

当一家公司想把产品卖给大型企业时，对方通常会发来 security questionnaire——有时 50 道题，有时 300 道以上。回答这些问题重复、耗时，而且往往压在一个人身上。每份问卷的答案其实大同小异，只是换了不同说法。花在这里的每一个小时，都是没有用来推进交易的时间。

---

## 目标客户

两类客户，同样的问题，不同的切入方式。

**类型一 — 拥有内部安全团队的公司**
处于 B 轮至 C 轮阶段的 SaaS 公司，内部有专职的 GRC 分析师或安全工程师。他们定期收到安全问卷，有时每月多达 5–10 份，分析师是整个流程的瓶颈。这类公司直接购买 Greenlight 自行使用。CISO 或 GRC 分析师既是购买决策者，也是日常使用者。

**类型二 — 没有内部安全团队的公司**
规模较小的公司（10–100 人），没有专职安全人员。当大客户发来安全问卷时，他们会聘请 GRC 咨询公司代为处理。咨询公司用 Greenlight 同时服务所有客户——一个工具，多个客户 workspace，每个完全隔离。咨询公司是购买方，他们的客户是最终受益者。

两类客户面对的是同一个痛点，区别在于谁在链条中感受最深，谁来做购买决定。

---

## 完整产品流程

### Step 1 — 建立 knowledge base

在回答任何 questionnaires 之前，团队先上传公司的 security documentation：

- Security policies（access control、incident response、encryption 等）
- Compliance reports（SOC 2、ISO 27001、pen test results）
- 任何描述公司如何处理 security 的内部文档

系统会处理每份文档，并拆分成 searchable chunks。当后续问题出现时，系统会找到这些文档中最相关的部分，并利用它们生成 draft answer。

**对于还没有正式文档的新客户：**
工具内置了 20 个 starter policy templates，涵盖常见 SOC 2 与 ISO 27001 topics，方便团队立刻开始使用。系统会通过 banner 提醒这些只是 generic templates，并鼓励他们上传真实 policies。

---

### Step 2 — 上传 questionnaire

Reviewer 上传客户发送的 questionnaire（通常是 Excel 文件）。

由于每家公司格式都不同，系统通过 two-step column picker 处理：

1. **Preview** — 系统显示文件前几行，让 reviewer 知道每一列内容是什么
2. **Map columns** — reviewer 手动指定：
   - 哪一列是 question
   - 哪一列是 Yes/No answer
   - 哪一列是 evidence/explanation（可选）

这意味着系统能兼容任何 Excel layout，而不需要固定 template。

---

### Step 3 — Draft answers

Questionnaire 设置完成后，reviewer 点击 “Draft Answers”。

系统会逐题：

1. 在 knowledge base 搜索最相关的 policy chunks
2. 生成完整 answer（evidence/explanation）
3. 生成简短 Yes/No/Partial/N-A answer
4. 根据 source documents 与 question 的匹配程度给出 confidence score（High / Medium / Low）
5. 显示使用了哪些具体 policy documents 作为来源

通常完整 questionnaire 只需要 1–3 分钟即可完成初稿。

---

### Step 4 — Review workspace

这里是 human reviewer 审核每个 drafted answer 的地方。Workspace 会显示：

- 原始 question text
- drafted answer（可编辑）
- short Yes/No answer
- confidence badge（High / Medium / Low）
- 系统引用的 exact source documents 与 passages，并附带 match score
- 系统为什么选择这些 sources 的 reasoning

对于每个问题，reviewer 可以：

- **Edit** — 直接编辑 draft answer
- **Approve** — 标记为最终答案，并加入 export
- **Reject / Flag** — 标记为排除，不会出现在 export 中
- **Re-draft** — 要求系统重新生成（适用于第一次 draft 没抓到重点）
- **Assign** — 分配给特定 team member（例如 network 问题交给 infra engineer）
- **Comment** — 对特定问题留下内部备注

顶部会显示 progress counter，展示当前已 approve 的问题数量与总数。

---

### Step 5 — Export

当 reviewer 完成审核后，点击 Export。

系统会把 approved answers 写回原本 Excel layout，并保留客户原始 column structure。

未 approved、被 flagged 或编辑后但尚未 approve 的答案绝不会 export。

如果客户的 questionnaire 文件包含 Excel 宏或 VBA 脚本（金融机构等大客户常见，用于自动锁定或联动单元格），系统会自动检测并在导出文件中保留这些宏，不会因为处理而损坏文件。答案也会自动匹配单元格的下拉菜单选项，确保符合客户 Excel 的验证规则。

导出的文件名称会包含 questionnaire 名称与当天日期，可直接发送给客户。

---

### 如果 AI 答错了怎么办？

没有人工审核批准，任何答案都不会发出去。每一条答案在被 reviewer 亲自确认之前，都只是草稿状态。Greenlight 的定位是副驾驶，不是自动驾驶——AI 负责调研和起草，人来做每一个最终决定。

审计日志会完整记录谁批准了哪条答案、什么时候批准的、引用了哪些来源文件。如果客户日后对某个答案提出质疑，你有完整的可追溯记录。如果发现某条答案有误，拒绝它、重新生成，几秒钟完成——系统同时从这次纠错中学习。

置信度评分正是为此而设计：低置信度答案会被标记出来，让 reviewer 知道应该把注意力放在哪里。你永远不会在不知情的情况下发出一个没把握的答案。

---

### Greenlight 的核心差异——复利式答案库

每一个被 approve 的答案都会自动保存到一个可搜索的答案库中。当未来的问卷出现相似问题时，系统会自动把之前已审核、已信任的答案作为建议浮现出来——不需要重新写，不需要重新找。

与竞争对手把每份问卷当作白纸重新开始不同，Greenlight 会随着你完成的每一份问卷变得更聪明。你的第 10 份问卷所花的时间，只是第 1 份的一小部分。团队的安全知识不再散落在某个人的收件箱里，而是持续沉淀为一项可复用的资产。

---

### Other features（其他功能）

**My Assignments**
Team members 会看到属于自己的 assignment inbox，显示所有被分配的问题、confidence，以及直接跳转到 questionnaire 的链接。

**Trash and restore**
删除的 questionnaires 与 documents 会先进入 trash bin，而不是永久删除。Owners 与 admins 可随时恢复，避免误删。

**Audit log**
所有行为都会被记录：
谁上传了什么、谁 approve 哪个 answer、谁 export、谁把问题分配给谁、发生时间等。完整 trail 用于 compliance purposes。

**Dashboard**
展示：
- 所有 questionnaires 概览
- 已回答问题总数
- approval rate
- average confidence score
- estimated time saved

**Knowledge base health**
专门页面显示：
- 哪些 questions 的 confidence 较低
- 哪些 topics 存在 gaps
- 上传哪些 documentation 会帮助改善结果

**Team management**
Owners 可通过 email 邀请 team members。

三种角色：

- **Owner** — 完整权限，可管理 billing 与 team
- **Admin** — 可管理 questionnaires、knowledge base 与 team members
- **User** — 可审核与 approve 分配给自己的 questionnaires

---

## 产品自身的 Security Features

因为这是 security product，所以我希望清楚说明产品本身如何被保护：

### Accounts and authentication

- Password requirements：8+ characters、至少一个 uppercase、一个 number、一个 symbol
- Passwords 使用 Argon2id hashing（OWASP 推荐的 industry standard）
- Login sessions 使用 secure httponly cookies（JavaScript 无法访问 token，可防止 XSS）
- Login 与 registration 均有限流（每 IP 每分钟最多 5 次），用于阻止 brute-force attacks
- Signup 必须 email verification
- Password reset 通过 time-limited email token

### Data protection

- 上传文件（Excel questionnaires、policy documents）储存在 S3-compatible object storage，而不是数据库
- 所有数据都按 organisation 隔离，一个客户永远看不到另一个客户数据
- Soft delete only —— 数据不会被永久删除，除非 explicit action

### AI 答案安全

- **否定句式 / 陷阱问题检测** — 安全问卷有时会用反向提问来测试 vendor 是否诚实（例如："贵公司是否存在不接受年度背景调查的员工特例？"）。系统会明确指示 AI 识别这类句式，并在确定 Yes/No 答案前验证：该答案是在证明公司安全合规，还是无意中承认了漏洞。每个被识别为陷阱问题的答案都会附带一行说明，方便 reviewer 理解 AI 的判断逻辑。
- **Prompt injection 防御（知识库投毒攻击）** — 每份上传到 knowledge base 的文档，在被切片存入之前都会经过清洗。任何看起来像系统指令覆盖的文字（如 `System Instruction Override`、`Ignore previous instructions`、中文版"忽略指令"、"从现在起你必须"等）都会被移除并写入日志。在 AI 生成答案时，所有检索到的文档片段都会被明确标记为"纯数据内容"，即使文档里有看起来像指令的文字，AI 也不会将其当作命令执行。

### Application security

- 每个 response 都带有 security headers：
  Content Security Policy、X-Frame-Options、Referrer-Policy、Permissions-Policy
- Production 环境使用 HTTPS-only + HSTS
- CORS 仅允许 configured frontend domain
- File uploads：仅允许 Excel files，最大 20MB
- 所有行为写入 immutable audit log

### AI 检索质量（RAG 引擎）

驱动每道问题找到正确政策内容的引擎，使用了一套多层流水线，远超竞争对手的水平：

- **混合搜索** — 每个问题同时用两种方式搜索：语义向量搜索（理解意思）+ 全文关键词搜索（精准命中"SOC 2 Type II"、"AES-256"等专业合规词汇）。两路结果通过 Reciprocal Rank Fusion 合并，命中率大幅提升。
- **HyDE + 问题扩展** — 搜索前，系统先生成一个假设答案和三种问题变体，然后用全部五个版本同时搜索。对于措辞冗长的企业问卷问题，召回率显著提升。
- **来源权重分级** — 之前人工审核批准的答案权重自动提升 35%；通用入门模板权重降低 25%。团队完成的问卷越多，检索结果越倾向于使用他们自己经过验证的答案。
- **反馈学习机制** — 每次 reviewer 批准一个答案，对应的来源内容获得正向信号；每次拒绝或重新生成，对应内容获得负向信号。长期下来，经常产生差答案的内容会被自动降权——系统随着每一次审核决策变得更聪明，无需人工干预。
- **父子分块检索** — 文档存储为两个层级：小子块（约 150 字）用于精准检索定位，大父块（约 800 字）用于给 AI 提供丰富上下文。搜索用小块定位，AI 阅读完整段落——每个检索结果的上下文是原来的 5 倍。
- **语义分块** — 文档按结构边界切分（标题、编号章节、段落换行），而不是按固定字数盲切，确保同一条政策条款不会被截断分散到两个不同的检索块里。
- **Voyage 重排序** — 检索完成后，由专业重排序模型对 top 20 候选结果按真实相关性重新打分，再选出最终结果送给 LLM。
- **检索质量评测系统** — 内置评测工具（`/admin/rag-eval`），用组织自身的历史批准答案作为 ground truth，持续监测命中率、精准率和 MRR 等指标——确保 RAG 质量可量化、可监控，不靠感觉猜。

### Monitoring

- 使用 Sentry 做 error tracking（仅 crash reports，不包含 user data）
- 每次 code change 都会通过 CI pipeline 自动运行 test suite

### Team invites

- Owners 与 admins 从 Team page 生成 unique invite link，而不是永久 invite code
- 每个 link 都是 single-use，并在 48 小时后自动过期
- Admin 可随时 revoke 尚未使用的 link
- Invite token 本身不会直接存入数据库，只储存 hash，因此即使 database leak 也不会暴露 usable links

### Coming soon（即将推出）

- MFA（authenticator app / TOTP）
- Data retention / purge job
- Email notifications
- SSO / SAML（Google Workspace、Okta、Azure AD）
- Org-level admin settings
- Answer version history
- Answer source traceability（答案来源追溯）—— 每条 approved answer 记录其来源于哪份 questionnaire 与哪个客户，即使该 questionnaire 已归档也可追溯来源
- Archive / remove answer from library（从答案库中归档或删除答案）—— 让 reviewer 可以直接从答案库中归档或删除某条特定答案，无需删除整份 questionnaire
- Multi-sheet Excel support
- Word 与 PDF questionnaire upload
- Web portal integrations（OneTrust、Vanta、Whistic）
- Common framework templates（CAIQ、SIG Lite、VSA）
- 澳洲数据主权支持 — 所有客户数据（上传文档、问卷资产、AI 生成内容）将全部存储于 AWS 悉尼区域（ap-southeast-2），开箱即符合澳洲隐私法规与数据本地化要求

---
