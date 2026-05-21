# Additional Strategic Positioning（额外战略定位）

Sentinel GRC 是一个 organizational security memory 与 questionnaire workflow platform，面向成长中的 B2B SaaS 公司。

这个平台并不只是另一个自动填表工具。长期目标是通过 approved answers、review history、evidence linkage、stale-answer detection 以及 operational trust workflows，帮助组织随着时间不断积累可复用的 institutional security knowledge。

核心问题不仅仅是“更快回答问卷”，而是减少 duplicated work、inconsistent responses、scattered knowledge，以及 enterprise security review 过程中的 operational bottlenecks。


# Sentinel GRC — 简报

你好！我正在开发一个 B2B SaaS 工具，帮助 security teams 更快回应客户发送的 security questionnaires。我非常希望获得你作为真实从业者的诚实反馈。

---

## 我正在解决的问题

当一家 vendor 想把产品卖给大型公司时，对方通常会发送 security questionnaire —— 有时 50 个问题，有时 300+ 个问题，例如：

- “Do you encrypt data at rest?”
- “Do you have a SOC 2 report?”
- “What is your password policy?”
- “Describe your incident response process.”

回答这些问题通常重复、缓慢，而且往往落在一个人身上处理。实际上，不同 questionnaires 的答案大部分都差不多，只是换了不同说法。

---

## 目标客户

两类客户，同样的问题，不同的切入方式。

**类型一 — 拥有内部安全团队的公司**
处于 B 轮至 C 轮阶段的 SaaS 公司，内部有专职的 GRC 分析师或安全工程师。他们定期收到安全问卷，有时每月多达 5–10 份，分析师是整个流程的瓶颈。这类公司直接购买 Sentinel 自行使用。CISO 或 GRC 分析师既是购买决策者，也是日常使用者。

**类型二 — 没有内部安全团队的公司**
规模较小的公司（10–100 人），没有专职安全人员。当大客户发来安全问卷时，他们会聘请 GRC 咨询公司代为处理。咨询公司用 Sentinel 同时服务所有客户——一个工具，多个客户 workspace，每个完全隔离。咨询公司是购买方，他们的客户是最终受益者。

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

Reviewer 也可以：

- 一键 bulk approve 所有 high-confidence answers，加快流程

顶部会显示 progress counter，展示当前已 approve 的问题数量与总数。

---

### Step 5 — Export

当 reviewer 完成审核后，点击 Export。

系统会把 approved answers 写回原本 Excel layout，并保留客户原始 column structure。

未 approved、被 flagged 或编辑后但尚未 approve 的答案绝不会 export。

导出的文件名称会包含 questionnaire 名称与当天日期，可直接发送给客户。

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

**Answer library（答案库）**
每一个被 approve 的答案都会自动保存到一个可搜索的答案库中。当未来的 questionnaire 出现相似问题时，系统会自动把之前 approved 的答案作为建议浮现出来，并附带 match score 显示相似程度。每条答案都会记录被复用了多少次。答案按类别归类（access control、encryption、incident response 等），并支持关键词搜索。答案库会随使用时间不断积累：团队做的 questionnaires 越多，下一次就越快。

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

### Application security

- 每个 response 都带有 security headers：
  Content Security Policy、X-Frame-Options、Referrer-Policy、Permissions-Policy
- Production 环境使用 HTTPS-only + HSTS
- CORS 仅允许 configured frontend domain
- File uploads：仅允许 Excel files，最大 20MB
- 所有行为写入 immutable audit log

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
- Multi-sheet Excel support
- Word 与 PDF questionnaire upload
- Web portal integrations（OneTrust、Vanta、Whistic）
- Common framework templates（CAIQ、SIG Lite、VSA）

---

## 我最希望获得的反馈

### 1. Workflow 是否符合现实？

在你的经验里，questionnaire response process 实际上是如何运作的？
是一个人处理全部，还是团队协作？
我的 approve/reject/assign flow 是否符合真实企业 workflow？

### 2. Knowledge base 的想法

系统通过 uploaded policy documents draft answers。

现实中，公司 policies 是否通常已经 structured 到足够支持这种 workflow？
还是经常 outdated、scattered、inconsistent？

“policy 写的是 X，但现实做的是 Y” 这种情况有多常见？

### 3. Confidence 与 flagging

当系统对答案不确定时（low confidence），它会 flag 进行 manual review。

这是正确的 signal 吗？

还有什么 signal 更有价值？
例如：
- “这个问题引用了我不认识的 regulation”
- “这个 answer 与另一份 questionnaire 冲突”

### 4. Questionnaire formats

大部分 questionnaires 是 Excel 吗？
现实中是否常见：
- Word
- PDF
- web portals（例如 OneTrust、Vanta、Whistic）

我是否应该优先支持某些格式？

### 5. 谁是真正的 buyer？

现实中，谁负责 questionnaire response process？
- CISO
- GRC analyst
- sales engineer

谁会真正购买这种工具？
谁会日常使用？
两者是否是同一个人？

### 6. 缺了什么？

有没有明显缺失的部分，会导致这个产品“不值得使用”？
有没有 workflow 哪部分明显不现实？

### 7. Pricing gut-check

我目前在考虑：
- per questionnaire
- per seat per month

哪种 pricing model 更符合 security teams 的真实预算方式？

---
