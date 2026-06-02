# Greenlight — 完整产品技术与商业手册

> 本文档覆盖产品的每一个方面：商业背景、完整用户流程、数据库结构、RAG 管道、API、前端架构、安全机制、商业模式。读完本文，你应该能向任何人解释这个产品的任何部分。

---

## 目录

1. [产品定位与核心价值](#1-产品定位与核心价值)
2. [目标用户与市场](#2-目标用户与市场)
3. [完整用户工作流程](#3-完整用户工作流程)
4. [技术栈总览](#4-技术栈总览)
5. [数据库模型（所有表）](#5-数据库模型所有表)
6. [RAG 检索管道（8层）](#6-rag-检索管道8层)
7. [LLM 提供商级联](#7-llm-提供商级联)
8. [向量嵌入系统](#8-向量嵌入系统)
9. [文件上传与存储](#9-文件上传与存储)
10. [答案库系统](#10-答案库系统)
11. [多客户答案隔离](#11-多客户答案隔离)
12. [认证与安全](#12-认证与安全)
13. [多租户架构](#13-多租户架构)
14. [后台任务队列](#14-后台任务队列)
15. [审计日志](#15-审计日志)
16. [通知系统](#16-通知系统)
17. [API 路由完整清单](#17-api-路由完整清单)
18. [前端架构](#18-前端架构)
19. [导出系统](#19-导出系统)
20. [知识库健康检查](#20-知识库健康检查)
21. [测试架构](#21-测试架构)
22. [商业模式与市场策略](#22-商业模式与市场策略)
23. [已知局限与路线图](#23-已知局限与路线图)
24. [与竞品的对比](#24-与竞品的对比)

---

## 1. 产品定位与核心价值

### 解决什么问题

当一家 SaaS 公司想把产品卖给大型企业或政府机构时，对方通常会发来一份安全问卷。这份问卷可能有 50 道题，也可能有 300 道以上，涵盖：

- 你们怎么保护用户数据？
- 你们有没有入侵检测系统？
- 你们最近一次渗透测试是什么时候？
- 你们符合 Essential Eight 的哪个成熟度等级？

人工填写一份 200 道题的问卷通常需要 2-3 天。而每家公司收到的问卷，问题其实高度重复——只是换了不同的措辞。这些重复劳动压在 GRC 顾问或公司内部的合规团队身上。

### Greenlight 的解决方案

你上传公司的安全策略文件和过去填过的问卷，系统把这些内容向量化存入数据库。当你上传一份新问卷时，AI 自动为每道题：

1. 在你的知识库中搜索最相关的内容段落
2. 生成完整的答案草稿和简短的 Yes/No 答案
3. 标注置信度（高/中/低）
4. 显示参考来源的具体段落

人工只需审核、按需修改、批准，然后导出为填好的 Excel 文件直接发给对方。

每一个批准的答案都自动存入答案库，下次遇到相似问题时直接复用——做到第十份问卷时，速度是第一份的数倍。

---

## 2. 目标用户与市场

### 主要用户类型

**GRC 顾问（核心用户）**
- 同时服务 5-15 个客户
- 每个客户可能每年收到多份问卷
- 每份问卷都是重复劳动，但答案因客户而异
- Greenlight 为他们节省的是大量可计费小时数

**中小型 SaaS 公司（直接用户）**
- 第一次向企业客户销售时被问卷压垮
- 没有专职 GRC 团队
- 需要快速、准确地完成问卷以推进销售

**政府承包商**
- 必须持续证明符合 Essential Eight 等标准
- 问卷频率高，内容标准化

### 澳大利亚市场的独特性

Greenlight 专为澳大利亚市场打造，内置以下合规框架的知识：

- **ASD Essential Eight** — 澳大利亚信号局制定的八项缓解策略，几乎所有澳洲政府机构强制要求
- **澳大利亚隐私法 / 澳大利亚隐私原则（APPs）** — 处理澳洲个人数据的公司必须遵守
- **APRA CPS 234** — 受 APRA 监管的银行、保险、养老金机构的信息安全要求
- **ISO 27001** — 在金融服务和医疗健康行业广泛采用

每位新用户注册后自动获得 45 条预置的澳洲 GRC 问答对，第一天就有高质量的答案可用。

---

## 3. 完整用户工作流程

### 注册流程

1. 用户填写邮箱、密码、姓名、公司名
2. 系统创建 Workspace（租户）和 Owner 账号
3. 系统自动将 45 条澳洲合规问答对种入答案库
4. 邮件验证（通过 Resend 发送）

### 上传知识文档

1. 用户上传 PDF 或 DOCX 格式的安全策略文件
2. 系统用 SHA-256 校验文件哈希，防止重复上传
3. 文件内容被解析为文本
4. 文本经过层级分块（hierarchical chunking）处理：
   - 父块：较大的段落，提供上下文
   - 子块（leaf）：更细的片段，用于向量搜索
5. 每个子块用 Voyage AI 生成 1024 维向量嵌入
6. 存入 PostgreSQL + pgvector

### 上传问卷

**Excel 格式（主要格式）：**
1. 用户上传 .xlsx 文件并填写问卷名称和客户名称
2. 系统预览前几行，用户选择哪一列是问题、哪一列是答案
3. 系统检查是否有该客户的历史模板（QuestionnaireTemplate），如有则自动预填列选择
4. 用户确认后，系统正式解析所有题目行

**Word / PDF 格式：**
1. 上传后系统提取文本
2. 调用 LLM 识别哪些行是真正的问题
3. 用户确认识别结果

**共同步骤：**
- 每道题存为一个 Question 记录，状态为 `pending`
- 原始 Excel 文件存入 S3（或 PostgreSQL LargeBinary 作为备用）

### 生成答案

用户点击"Generate"按钮，系统为每道 `pending` 状态的题目：

1. 调用 8 层 RAG 管道检索最相关的知识块
2. 调用 LLM 生成答案
3. 返回：完整答案、Yes/No 简短答案、置信度（高/中/低）、参考块 ID、推理说明
4. 如果与答案库中已有答案存在矛盾，标注冲突警告
5. 问题状态更新为 `generated`
6. 每道题之间间隔 6 秒（控制 API 速率）
7. 生成完成后发送站内通知和邮件通知

### 人工审核

审核界面按题目逐条展示：

- 草稿答案（可直接编辑）
- Yes/No 简短答案
- 置信度标签（高/中/低）
- 参考来源（可点击查看原文段落）
- 冲突警告（如果与历史答案有矛盾）
- 标记功能（可添加备注，如"已通过 Slack 询问 DevOps"）
- 评论线程（团队成员可讨论）

审核人员对每道题可以：
- **批准**：答案进入最终答案，同时存入答案库供未来复用
- **拒绝**：标记为需手动填写，从答案库移除
- **重新生成**：要求 AI 重试，同时记录负向反馈信号
- **直接编辑**：修改草稿后再批准

### 导出

所有题目批准后，用户下载填好的 Excel 文件：
- 保留原始文件的列结构、合并单元格、列宽行高
- 如果工作空间启用了"白标导出"，Greenlight 品牌标识不会出现在导出文件中
- 文件名格式：`问卷名称_filled_日期.xlsx`

---

## 4. 技术栈总览

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端框架 | FastAPI | 异步 Python Web 框架 |
| ORM | SQLAlchemy 2.0 | 数据库映射层 |
| 数据库 | PostgreSQL 16 + pgvector | 关系数据 + 向量搜索 |
| 向量扩展 | pgvector | 1024 维向量，支持余弦相似度搜索 |
| 前端框架 | React 19 + Vite | 单页应用 |
| CSS | Tailwind CSS 4 | 原子化样式 |
| 主要 LLM | Gemini 2.5 Flash | 答案生成 |
| 备用 LLM | Groq、Cerebras、OpenRouter | 自动降级 |
| 向量嵌入 | Voyage AI (voyage-3) | 1024 维，专为检索优化 |
| 认证 | JWT + Argon2id | HttpOnly Cookie，7 天有效期 |
| 文件存储 | S3 兼容 / PostgreSQL | 优先 S3，无配置时回退到 DB |
| 包管理 | uv | 替代 pip，更快 |
| 数据库迁移 | Alembic | 版本化 schema 变更 |
| 限流 | slowapi | 防止 API 滥用 |
| 邮件 | Resend | 事务邮件发送 |

**端口分配：**
- 后端 API：`:8000`
- 前端开发服务器：`:5173`（`/api/*` 代理到 `:8000`）
- PostgreSQL：`:5434`（非标准端口，避免与本地 Postgres 冲突）

---

## 5. 数据库模型（所有表）

### Workspace（工作空间 / 租户）

每个工作空间是一个独立的租户。所有数据都在工作空间内隔离。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 主键 |
| name | String | 工作空间名称（公司名） |
| slug | String unique | URL 友好的唯一标识 |
| white_label_export | Boolean | 启用后导出文件不含 Greenlight 品牌 |
| workspace_type | String | `"consultant"` 或 `"direct"` |
| created_at | DateTime | 创建时间 |

`workspace_type` 区分：
- `consultant`：GRC 顾问，同时管理多个客户
- `direct`：公司自己管理合规，只有一个客户（自己）

### User（用户）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | |
| email | String unique | 登录邮箱 |
| hashed_password | String | Argon2id 哈希（兼容 bcrypt 历史账号） |
| full_name | String | 显示名称 |
| role | String | `owner` / `admin` / `member` |
| is_active | Boolean | 账号是否启用 |
| workspace_id | FK → Workspace | 所属工作空间 |
| email_verified | Boolean | 邮件是否已验证 |
| verification_token_hash | String | 验证 token 的 SHA-256 哈希 |
| reset_token_hash | String | 密码重置 token 哈希 |

角色权限：
- `owner`：全权限，包括永久删除（purge）和工作空间设置
- `admin`：可删除/恢复，可管理成员，不可 purge
- `member`：可上传、生成、审核，不可删除

### Document（知识文档）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | |
| filename | String | 原始文件名 |
| file_type | Enum | `pdf` / `docx` / `xlsx` |
| chunk_count | Integer | 子块数量 |
| content_hash | String | SHA-256 哈希，用于防重复上传 |
| is_starter | Boolean | 是否为系统预置文档（已废弃，现改用答案库种子） |
| deleted_at | DateTime | 软删除时间戳（NULL = 未删除） |
| content_updated_at | DateTime | 文件内容最后更新时间（用于过期检测） |
| workspace_id | FK → Workspace | 所属工作空间 |

### KnowledgeChunk（知识块）

这是 RAG 系统的核心表。每个文档被分解为多个知识块。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | |
| document_id | FK → Document | 来源文档 |
| source_document | String | 来源文件名（冗余存储，加速显示） |
| source_section | String | 来源章节（如 Excel 工作表名、标题） |
| source_type | Enum | `policy` / `past_answer` / `approved_answer` |
| customer_name | String nullable | NULL = 通用块；有值 = 客户专属块 |
| text | Text | 块的原始文本内容 |
| embedding | Vector(1024) | Voyage AI 生成的向量 |
| is_leaf | Boolean | true = 子块（用于检索）；false = 父块（提供上下文） |
| parent_chunk_id | FK → self | 层级结构：子块指向父块 |

`source_type` 的三种类型：
- `policy`：从上传的策略文件（PDF/DOCX）解析出的内容
- `past_answer`：从历史已填写的问卷（XLSX）解析出的答案
- `approved_answer`：用户在审核界面批准的答案，自动回写为知识块

### ChunkFeedback（块反馈）

记录每次审核操作对知识块的正/负向反馈，用于调整未来检索的排名。

| 字段 | 类型 | 说明 |
|------|------|------|
| chunk_id | FK → KnowledgeChunk | |
| workspace_id | FK → Workspace | 每个工作空间的反馈独立计算 |
| signal | String | `"positive"` 或 `"negative"` |

触发规则：
- 批准答案 → 引用该答案的所有块收到 `positive` 信号
- 拒绝答案 / 重新生成 → 引用块收到 `negative` 信号

### Questionnaire（问卷）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | |
| name | String | 问卷名称（用户自定义） |
| customer_name | String nullable | 客户名称（GRC 顾问填写） |
| source_filename | String | 原始上传文件名 |
| status | Enum | `draft` / `in_progress` / `complete` |
| question_count | Integer | 问题总数 |
| raw_xlsx_blob | LargeBinary | 原始文件（旧方式，存在 DB） |
| raw_xlsx_key | String | S3 对象键（新方式） |
| share_token | String unique | 只读分享链接的 token |
| question_col_index | Integer | 问题列的 0-based 列索引 |
| answer_col_index | Integer | 答案列索引（Yes/No 列） |
| secondary_answer_col_index | Integer | 附加答案列索引（详细说明列） |
| template_id | FK → QuestionnaireTemplate | 使用的格式模板 |
| deleted_at | DateTime | 软删除时间戳 |
| workspace_id | FK → Workspace | |

状态流转：`draft` → `in_progress`（开始生成）→ `complete`（全部批准）

### Question（问题）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | |
| questionnaire_id | FK → Questionnaire | |
| row_index | Integer | 原始 Excel 行号（0-based） |
| question_text | Text | 问题原文 |
| draft_answer | Text | AI 生成的草稿答案 |
| short_answer | String | `Yes` / `No` / `Partial` / `N/A` |
| final_answer | Text | 用户批准的最终答案 |
| status | Enum | `pending` / `generated` / `approved` / `rejected` |
| confidence | Enum | `high` / `medium` / `low` |
| cited_chunk_ids | JSON | 引用的知识块 ID 列表 |
| reasoning | Text | AI 对置信度的解释说明 |
| conflict_warning | Text | 与历史答案冲突时的警告文本 |
| category | String | 嵌入分类的话题类别 |
| flag_note | Text | 审核人员的标注备注 |

### QuestionnaireTemplate（问卷格式模板）

记录每个客户问卷的格式信息，下次上传同一客户的问卷时自动识别。

| 字段 | 类型 | 说明 |
|------|------|------|
| name | String | 模板名称 |
| customer_name | String | 关联的客户名 |
| question_col | Integer | 问题列索引 |
| answer_col | Integer | 答案列索引 |
| format_config | JSON | 合并单元格、列宽、行高等格式信息 |
| times_used | Integer | 使用次数 |

### ApprovedAnswer（答案库）

存储所有经人工批准的问答对，用于未来问卷的快速匹配。

| 字段 | 类型 | 说明 |
|------|------|------|
| question_text | Text | 问题原文 |
| answer_text | Text | 批准的答案 |
| short_answer | String | Yes/No 简答 |
| answer_category | String | 话题类别（访问控制、加密、事件响应等） |
| cited_chunk_ids | JSON | 引用的知识块 |
| confidence_score | Float | 0-1 置信度分数 |
| times_reused | Integer | 被复用次数 |
| status | String | `active` / `archived` |
| is_stale | Boolean | 当来源文档被替换时自动标为 true |
| customer_name | String nullable | NULL = 通用答案；有值 = 客户专属 |
| embedding | Vector(1024) | 问题文本的向量（用于相似性匹配） |
| source_question_id | FK → Question | 来源问题 |

### LLMCall（AI 调用记录）

记录每次 LLM 调用的 token 用量和费用估算，用于使用量仪表板。

| 字段 | 类型 | 说明 |
|------|------|------|
| model | String | 使用的模型名称 |
| input_tokens | Integer | 输入 token 数 |
| output_tokens | Integer | 输出 token 数 |
| cost_estimate | Float | 美元费用估算 |
| questionnaire_id | FK nullable | 关联问卷 |
| question_id | FK nullable | 关联问题 |
| workspace_id | FK | 所属工作空间 |

### AuditLog（审计日志）

不可篡改的操作记录，记录谁在何时做了什么。

| 字段 | 类型 | 说明 |
|------|------|------|
| workspace_id | FK | |
| user_id | FK nullable | |
| user_email | String | 冗余存储（防止用户删除后记录丢失） |
| action | String | 操作类型，如 `question.approved` |
| resource_type | String | `question` / `questionnaire` / `document` / `auth` |
| resource_id | Integer | 操作对象的 ID |
| detail | JSON | 额外上下文信息 |

### QuestionComment（问题评论）

| 字段 | 类型 | 说明 |
|------|------|------|
| question_id | FK | |
| questionnaire_id | FK | |
| workspace_id | FK | |
| user_email | String | 冗余存储 |
| body | Text | 评论内容 |

### AnswerVersion（答案版本历史）

每次编辑、批准、拒绝操作都自动保存一个快照。

| 字段 | 类型 | 说明 |
|------|------|------|
| question_id | FK | |
| user_email | String | 操作人 |
| action | String | `edited` / `approved` / `rejected` |
| draft_answer | Text | 操作时的答案内容 |
| short_answer | String | 操作时的简答 |

### Invite（邀请链接）

| 字段 | 类型 | 说明 |
|------|------|------|
| workspace_id | FK | |
| token_hash | String unique | token 的哈希值（不存明文） |
| expires_at | DateTime | 过期时间 |
| used_at | DateTime nullable | 使用时间 |
| used_by_id | FK nullable | 使用者 |
| revoked_at | DateTime nullable | 撤销时间 |

### Notification（站内通知）

| 字段 | 类型 | 说明 |
|------|------|------|
| type | String | `generation_complete` / `question_assigned` |
| title | Text | 通知标题 |
| body | Text | 通知内容 |
| read | Boolean | 是否已读 |
| resource_type | String | 关联资源类型 |
| resource_id | Integer | 关联资源 ID |

### JobQueue（后台任务队列）

| 字段 | 类型 | 说明 |
|------|------|------|
| job_type | String | 任务类型（如 `send_restore_notification`） |
| payload | JSON | 任务参数 |
| status | Enum | `pending` / `running` / `done` / `failed` |
| attempts | Integer | 已尝试次数 |
| last_error | Text | 最后一次失败的错误信息 |
| run_after | DateTime | 最早执行时间（用于重试退避） |

### question_citations（引用关联表）

连接 Question 和 KnowledgeChunk 的多对多关联表。

| 字段 | 类型 | 说明 |
|------|------|------|
| question_id | FK | |
| chunk_id | FK | |
| retrieval_score | Float | 余弦相似度分数 |

---

## 6. RAG 检索管道（8层）

每次为一道题检索相关内容时，系统经过以下 8 个步骤，每一步都有降级备用方案。

### 第1层：HyDE + 查询扩展

**问题：** 用户的原始问题措辞可能与知识库中的内容措辞不同。

**解决方案：**
- 调用 LLM 生成一个"假设性答案"（Hypothetical Document Embedding，HyDE）：即使没有真实答案，先生成一个听起来合理的答案，然后用这个答案去搜索——因为答案的措辞更接近知识库中的内容
- 同时将原始问题改写成 3 种不同的表达方式
- 共产生 4 个搜索查询（1 个 HyDE + 3 个改写版本）

### 第2层：多向量密集搜索

对第1层产生的每个查询：
- 生成向量嵌入
- 用 pgvector 做余弦相似度搜索（仅搜索 leaf 子块）
- 过滤条件：同一工作空间内，且满足客户名隔离规则
- 每个查询返回 top-K 结果

### 第3层：PostgreSQL 全文搜索

用 GIN 索引对原始问题做传统关键词搜索，补充向量搜索的盲点（向量搜索对专有名词和缩写效果较差）。

### 第4层：倒数排名融合（Reciprocal Rank Fusion, RRF）

将第2层和第3层的所有结果列表合并：
- RRF 公式：`score = Σ 1/(rank + k)` 其中 k=60
- 各列表中排名越高的结果，融合后得分越高
- 消除了不同搜索方法之间的量纲差异

### 第5层：来源类型加权

对 `source_type = approved_answer`（已人工批准的答案）的块额外加分 35%：
- 已批准答案的质量高于未审核的策略文档片段
- 鼓励系统优先复用已经过人工验证的内容

### 第6层：工作空间反馈评分

根据 ChunkFeedback 表中的历史信号调整排名：
- 同一工作空间内，曾经导致批准答案的块得分提升
- 曾经导致拒绝或重新生成的块得分降低
- 不同工作空间的反馈完全独立，不会互相影响

### 第7层：Voyage AI 重排序

将 top-20 候选块送入 Voyage AI 的 `rerank-2` 模型做精排：
- 重排序模型对"问题-段落"相关性的判断比向量相似度更准确
- 这一步计算成本较高，所以只对已经粗筛的 top-20 执行

### 第8层：去重

使用余弦相似度阈值（≥ 0.92）过滤几乎相同的块：
- 防止同一内容因措辞略有不同而重复出现在结果中
- 优先保留得分更高的那个

**降级机制：** 任何一层失败（如 Voyage API 超时），系统会使用上一层的输出继续，不会因为某个 API 报错而整体崩溃。

---

## 7. LLM 提供商级联

系统按优先级尝试以下提供商，自动处理配额限制和错误：

| 优先级 | 模型 | 说明 |
|--------|------|------|
| 1 | Gemini 2.5 Flash | 主要提供商，质量最高 |
| 2 | Gemma 3 27B | Gemini 备用 |
| 3 | Groq Llama 3.3 70B | 高质量免费层 |
| 4 | Groq Llama 4 Scout | Groq 备用 |
| 5 | Cerebras | 极快推理速度 |
| 6 | Groq Llama 3.1 8B | 最快最便宜 |
| 7+ | OpenRouter 备用 | 多个 OpenRouter 路由的免费模型 |

**错误处理逻辑：**
- 收到 `429`（配额耗尽）→ 将该提供商标记为"已耗尽"，24小时内跳过
- 收到 `503`（服务不可用）→ 原提供商重试 3 次，每次间隔 10 秒，仍失败则跳过
- 系统确保在当前可用提供商中找到一个能正常工作的

**成本控制：**
- 优先使用免费层配额（Gemini、Groq、Cerebras 都有慷慨的免费层）
- 每道题之间强制间隔 6 秒，控制每分钟请求数约 10 次，保持在免费层限制内

---

## 8. 向量嵌入系统

**主要提供商：** Voyage AI，模型 `voyage-3`
- 向量维度：1024
- 专为检索场景优化（不是通用嵌入）
- 文档和问题使用不同的 input_type：`document` vs `query`

**备用提供商：** OpenAI `text-embedding-3-small`
- 维度也是 1024（截断自 1536）
- 当 Voyage API key 未配置时自动使用

**嵌入时机：**
- 上传文档时 → 对每个 leaf 子块生成嵌入
- 批准答案时 → 对答案的问题文本生成嵌入（存入答案库）
- RAG 检索时 → 对查询文本生成嵌入

**嵌入前缀：** 文档块嵌入时加前缀 `Document: {filename}\n`，提升检索精度。

---

## 9. 文件上传与存储

### 知识文档（PDF/DOCX）

- 上传后只存解析出的文本和向量，原始文件不持久化
- 用 SHA-256 哈希去重：同一文件上传两次会被拒绝

### 问卷文件（XLSX/DOCX/PDF）

原始文件需要保留（用于导出时写回答案），存储方式：

**有 S3 配置时（生产推荐）：**
- 存储路径：`questionnaires/{workspace_id}/{uuid}.xlsx`
- 支持任意 S3 兼容存储：AWS S3、Cloudflare R2、MinIO

**无 S3 配置时（本地开发）：**
- 以 `LargeBinary` 格式直接存入 PostgreSQL

**相关环境变量：**
```
S3_BUCKET=
S3_ACCESS_KEY=
S3_SECRET_KEY=
S3_ENDPOINT_URL=
```

### 文件解析

- PDF → 使用 pdfplumber 提取文本
- DOCX → 使用 python-docx 提取段落
- XLSX 问卷 → 用 openpyxl 读取单元格，识别合并单元格

---

## 10. 答案库系统

答案库（ApprovedAnswer 表）是系统的"记忆"核心。

### 内容来源

1. **注册时自动种入** — 45 条澳洲合规框架预置问答（Essential Eight、Privacy Act、APRA CPS 234、ISO 27001）
2. **用户批准答案时自动添加** — 每次批准一道题，该问答对自动存入答案库

### 类别检测

每条答案自动分配类别，分两种方法：

**关键词匹配（`detect_category`）：**
- 快速、无需 API 调用
- 用于批量处理
- 类别示例：访问控制、加密、事件响应、漏洞管理、数据保护...

**嵌入相似性分类（`classify_category`）：**
- 更准确
- 将问题文本与每个类别的锚点句子做向量相似度比较
- 用于问题生成时的实时分类

### 在 RAG 中的作用

当系统为新问题检索相关内容时，答案库条目作为 `approved_answer` 类型的知识块参与检索，并享有 35% 的额外加权（第5层）。这意味着：

- 做得越多，下次越快
- 系统优先复用已经人工验证的答案，而不是从头生成

### 过期检测（Staleness）

当文档被替换（`/knowledge/{id}/replace`）或删除时，系统自动检查哪些答案库条目引用了该文档的块，将其 `is_stale` 标记为 `true`。用户在界面上看到"已过期"提示，可以选择重新审核或手动标为"仍有效"。

### 冲突检测

生成答案时，系统检查新答案的 Yes/No 简答是否与答案库中同类问题的历史答案相矛盾。如果矛盾，在审核界面显示冲突警告，让审核人员知道这里可能有问题需要特别关注。

---

## 11. 多客户答案隔离

这是 GRC 顾问场景的核心安全特性。

### 问题场景

GRC 顾问同时服务 Atlas Bank 和 HealthCo 两个客户。Atlas Bank 的某些安全策略（如特定的访问控制配置）是商业机密，不能被 HealthCo 看到，反之亦然。

### 实现机制

`KnowledgeChunk.customer_name` 和 `ApprovedAnswer.customer_name`：
- `NULL` = 通用内容，可被所有客户使用
- `"Atlas Bank"` = 仅对 Atlas Bank 的查询可见

RAG 检索的 SQL 过滤条件：
```sql
WHERE customer_name IS NULL
   OR customer_name = :current_customer_name
```
这不是界面层的过滤，而是数据库查询层面的强制执行。系统在结构上无法检索到其他客户的专属内容。

### 通用答案的逻辑

当顾问批准一个答案时，系统自动判断：如果问题是"你们有没有防火墙"，这种通用性问题的答案可以跨客户复用，`customer_name` 设为 NULL。如果问题是"你们在 ANZ 数据中心的备份策略是什么"，这显然是客户专属信息，`customer_name` 设为当前客户名。

顾问也可以手动在界面上将一个客户专属答案"升级"为通用答案（"Make Generic"按钮），此操作同时更新 ApprovedAnswer 和对应的 KnowledgeChunk。

---

## 12. 认证与安全

### JWT + HttpOnly Cookie

- 用户登录后，服务端生成 JWT token
- Token 存储在 `greenlight_token` 这个 HttpOnly Cookie 中
- Cookie 属性：`SameSite=Strict`，防止 CSRF 攻击
- Token 有效期：7 天
- 前端无法通过 JavaScript 读取这个 Cookie，防止 XSS 窃取

### 密码哈希

- 新密码：Argon2id（内存硬函数，抗 GPU 暴力破解）
- 历史密码：支持 bcrypt 读取（向后兼容），下次登录时自动迁移为 Argon2id

### 密码重置流程

1. 用户请求重置 → 系统生成随机 token
2. Token 的 SHA-256 哈希存入数据库（不存明文）
3. 原始 token 通过邮件发送给用户
4. 用户点击链接 → 系统 SHA-256 哈希请求中的 token，与数据库比对
5. 匹配且未过期 → 允许设置新密码

### 邮件验证

- 注册时发送验证邮件
- 验证 token 哈希存入数据库
- 过期时间可配置

### API 限流

使用 slowapi 对关键端点做速率限制，防止暴力破解和滥用。

### 输入清理

上传的文档文本经过 `sanitize_text()` 处理，移除可能干扰 RAG 的噪声内容。

---

## 13. 多租户架构

### 隔离原则

所有数据库查询都包含 `workspace_id` 过滤条件。这不是可选的惯例，而是架构上的强制要求：

```python
# 所有查询模式如此
db.query(Questionnaire).filter(
    Questionnaire.workspace_id == current_user.workspace_id,
    ...
)
```

跨租户的数据访问在应用层和数据库约束层都是不可能的。

### 用户与工作空间的关系

- 一个用户只属于一个工作空间
- 工作空间可以有多个用户
- 邀请机制：通过一次性邀请链接（token）添加新成员

### 白标导出

工作空间级别的功能。启用后，导出的 Excel 文件中不包含 Greenlight 的品牌信息，顾问可以将其作为自己的工具输出交给客户。

---

## 14. 后台任务队列

### 为什么不用 FastAPI BackgroundTasks？

FastAPI 的 `BackgroundTasks` 在服务器重启时会丢失。Greenlight 使用 Postgres 支持的任务队列，任务状态持久化在数据库中，服务器重启后任务不会丢失。

### 工作原理

Worker 循环在应用启动时作为 asyncio 任务运行，每 10 秒轮询 `job_queue` 表：
1. 查询所有 `status = pending` 且 `run_after <= now` 的任务
2. 将任务标记为 `running`
3. 执行任务
4. 更新状态为 `done` 或 `failed`

### 失败重试

失败的任务记录 `last_error`，可配置指数退避重试（`run_after` 字段控制下次最早执行时间）。

### 添加任务

```python
from app.services.jobs import enqueue
enqueue("send_restore_notification", {
    "owner_email": "...",
    "item_name": "...",
})
```

---

## 15. 审计日志

每一个用户操作都记录在 `audit_logs` 表中，不可删除、不可修改。

记录的操作类型包括：
- `auth.login` / `auth.logout`
- `document.uploaded` / `document.deleted` / `document.replaced` / `document.restored` / `document.purged`
- `questionnaire.uploaded` / `questionnaire.deleted` / `questionnaire.restored` / `questionnaire.purged` / `questionnaire.exported`
- `answer.generated` / `answer.archived`
- `question.approved` / `question.rejected` / `question.edited`
- `reassign_questionnaire`

`user_email` 字段冗余存储：即使用户账号被删除，审计记录仍然完整保留操作人信息。

---

## 16. 通知系统

### 站内通知

生成完成后，系统创建 Notification 记录，前端轮询显示。包含：
- 完成多少道题的草稿
- 有多少冲突被标记

### 邮件通知

通过 Resend 发送，包括：
- 生成完成通知（含问卷链接）
- 恢复删除内容通知（通知 owner）

所有邮件发送都是"尽力而为"（try/except），失败不影响主流程。

---

## 17. API 路由完整清单

所有路由都在 `/api` 前缀下，需要 JWT 认证。

### 仪表板
- `GET /api/dashboard` — 总问卷数、已答题数、平均置信度、节省工时、最近问卷

### 问卷管理
- `POST /api/questionnaires/upload/preview` — 上传预览，返回列结构
- `POST /api/questionnaires/upload/{temp_id}/finalize` — 确认上传
- `GET /api/questionnaires` — 分页列表
- `GET /api/questionnaires/{id}` — 详情 + 所有问题
- `GET /api/questionnaires/clients` — 自动补全的客户名列表
- `POST /api/questionnaires/{id}/generate` — 触发 AI 生成
- `POST /api/questionnaires/{id}/delete` — 软删除
- `POST /api/questionnaires/{id}/restore` — 从回收站恢复
- `POST /api/questionnaires/{id}/purge` — 永久删除（仅 owner）
- `GET /api/questionnaires/{id}/export` — 下载填好的 Excel
- `PATCH /api/questionnaires/{id}/reassign` — 改变客户归属

### 问题操作
- `POST /api/questionnaires/{qid}/questions/{id}/approve` — 批准（含 make_generic 参数）
- `POST /api/questionnaires/{qid}/questions/{id}/reject` — 拒绝
- `POST /api/questionnaires/{qid}/questions/{id}/regenerate` — 重新生成
- `PATCH /api/questionnaires/{qid}/questions/{id}` — 编辑草稿
- `PATCH /api/questionnaires/{qid}/questions/{id}/flag` — 添加/清除标记
- `GET/POST/DELETE /api/questionnaires/{qid}/questions/{id}/comments` — 评论线程

### 知识库
- `POST /api/knowledge/upload` — 上传策略文档
- `POST /api/knowledge/{id}/replace` — 替换文档内容
- `GET /api/knowledge` — 分页列表
- `POST /api/knowledge/{id}/delete` — 软删除
- `POST /api/knowledge/{id}/restore` — 恢复
- `POST /api/knowledge/{id}/purge` — 永久删除
- `GET /api/chunks/{id}` — 获取单个知识块原文

### 答案库
- `GET /api/answers/library` — 带搜索和分类过滤的列表
- `POST /api/answers/library/{id}/mark-fresh` — 清除过期标记
- `POST /api/answers/library/{id}/make-generic` — 改为通用答案
- `POST /api/answers/library/{id}/archive` — 归档答案

### 格式模板
- `GET /api/templates` — 列表
- `POST /api/templates/{id}/delete` — 删除

### 统计与分析
- `GET /api/usage` — AI 调用量和费用统计
- `GET /api/kb-health` — 知识库健康状态分析

### 回收站
- `GET /api/trash` — 已软删除的问卷和文档

### 用户与工作空间
- `GET /api/me` — 当前用户信息
- `PATCH /api/me` — 更新姓名/密码
- `GET /api/workspace` — 工作空间信息
- `PATCH /api/workspace` — 更新工作空间设置（仅 owner）
- `GET /api/users` — 工作空间成员列表
- `DELETE /api/users/{id}` — 移除成员
- `POST /api/invites` — 创建邀请链接
- `GET /api/invites` — 邀请列表
- `DELETE /api/invites/{id}` — 撤销邀请

### 认证（无需登录）
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `POST /api/auth/request-password-reset`
- `POST /api/auth/reset-password`
- `GET /api/auth/verify-email`
- `GET /api/invite/info/{token}` — 查看邀请信息
- `POST /api/invite/accept/{token}` — 接受邀请注册

### 分享（无需登录）
- `GET /api/share/{token}` — 通过分享链接只读查看问卷进度

---

## 18. 前端架构

### 目录结构

```
frontend/src/
├── api.js              # 所有 API 调用的封装层
├── context/
│   └── AuthContext.jsx # 全局用户认证状态
├── pages/              # 路由级页面组件
│   ├── Dashboard.jsx
│   ├── Questionnaires.jsx
│   ├── QuestionnaireDetail.jsx
│   ├── KnowledgeBase.jsx
│   ├── AnswerLibrary.jsx
│   ├── KBHealth.jsx
│   ├── Usage.jsx
│   ├── Settings.jsx
│   ├── Team.jsx
│   ├── Trash.jsx
│   └── ...
└── components/         # 可复用组件
```

### API 层（api.js）

所有 fetch 调用都通过这个文件：
- 所有请求带 `credentials: 'include'`（发送 HttpOnly Cookie）
- 收到 401 → 自动跳转到 `/login`
- 统一错误处理

### 路由

使用 React Router v6，所有路由在 `App.jsx` 中定义：
- `/` → 仪表板
- `/questionnaires` → 问卷列表
- `/questionnaires/:id` → 问卷详情（审核界面）
- `/knowledge` → 知识库
- `/answers` → 答案库
- `/kb-health` → 知识库健康
- `/usage` → 使用量统计
- `/settings` → 工作空间设置
- `/team` → 团队管理
- `/trash` → 回收站
- `/share/:token` → 公开只读分享页

### 认证状态

`AuthContext.jsx` 在应用顶层维护当前用户信息（`/api/me`），所有子组件通过 `useAuth()` hook 获取。

---

## 19. 导出系统

导出逻辑在 `app/services/export.py`：

1. 从 S3 或 PostgreSQL 取回原始 XLSX 文件
2. 用 openpyxl 打开
3. 对每道已批准的题目，将 `final_answer` 写入对应的答案列单元格
4. 如果有次要答案列（evidence/comments），写入详细答案
5. 保留原始格式：合并单元格、列宽、行高、字体
6. 如果 `white_label_export = False`，在文件中添加 Greenlight 水印/备注
7. 返回文件字节流

---

## 20. 知识库健康检查

`/api/kb-health` 端点分析整个工作空间的答案质量：

**按类别分组统计：**
- 每个话题类别的总问题数
- 批准率 / 拒绝率
- 低置信度比例
- 无来源（无知识块匹配）的比例
- 平均检索相似度分数

**计算整体健康分（0-100）：**
- 低置信度和无来源问题越多，健康分越低
- 审核人员可以看到哪些话题的知识库内容不足，针对性地上传相关策略文档

---

## 21. 测试架构

### 测试原则

- 使用真实 PostgreSQL 数据库（不用 mock）
- 每个测试用 transaction 包裹，测试结束后 rollback — 数据不持久化
- 所有 LLM 和嵌入调用使用 `unittest.mock.patch` 模拟
- FastAPI 的 `get_db` 依赖被 fixture 覆盖

### 主要测试文件

- `tests/test_critical_path.py` — 完整流程：注册 → 上传 → 生成 → 批准 → 导出
- `tests/test_retrieval.py` — RAG 管道的每一层
- `tests/test_generation.py` — LLM 提供商级联逻辑

### 运行测试

```bash
pytest                              # 全部测试
pytest tests/test_critical_path.py  # 只跑关键路径
pytest tests/test_critical_path.py::test_name -v  # 单个测试
```

---

## 22. 商业模式与市场策略

### 目标细分市场（澳大利亚）

1. **GRC 顾问（优先）** — 同时服务多个客户，问卷工作是核心收入来源，工具直接影响利润率
2. **中小型 SaaS 公司** — 首次进入企业销售市场，被问卷拦截
3. **金融服务公司** — APRA CPS 234 监管要求，问卷频率极高
4. **政府供应商** — Essential Eight 合规要求

### 增长路径

1. 获取顾问导师作为第一个真实用户，收集实践反馈
2. 通过顾问的口碑转介同行（GRC 社区小且紧密）
3. AISA / ISACA Sydney 活动建立行业知名度
4. 从悉尼扩展到全澳大利亚，再到新西兰、英国（类似监管环境）
5. 从 GRC 顾问扩展到 SMB SaaS 直接用户

### 竞争壁垒

- **澳洲合规知识**：美国竞品不懂 Essential Eight 和 APRA，这是原生内置的差距
- **答案库复利效应**：用得越多，准确率越高，切换成本随时间增加
- **顾问工作流**：多客户隔离、白标导出、客户级别的知识分区，专门为顾问设计

---

## 23. 已知局限与路线图

### 当前已知局限

| 问题 | 现状 |
|------|------|
| 不支持跨多工作表的 Excel 问卷 | 路线图中 |
| 答案生成不支持并行（同时只能一个问卷） | 路线图中 |
| 问卷没有截止日期/SLA 跟踪 | 未计划 |
| 过期答案检测（已实现 is_stale 标记，但不主动提醒） | 部分实现 |
| Essential Eight 答案未区分成熟度等级（Level 1/2/3），可能给出错误等级的答案 | 路线图中 |

### 路线图功能

- 多因素认证（MFA）
- 单点登录（SSO：Google Workspace / Okta / Azure AD）
- 多工作表 Excel 支持
- 问题分配给团队成员
- OneTrust / Vanta / Whistic 集成
- 澳大利亚数据主权（AWS 悉尼节点托管）
- Google Drive / SharePoint 文档同步
- 合规框架映射（将答案自动标注至对应的 Essential Eight 策略、ISO 27001 控制项等）
- 并行答案生成
- Essential Eight 成熟度等级支持（给知识块加入 framework、maturity_level、control 元数据标签，按等级精确检索）

---

## 24. 与竞品的对比

| 特性 | Greenlight | Hypercomply | Conveyor |
|------|------------|-------------|---------|
| 澳洲合规框架（Essential Eight、APRA） | 原生内置 | 不支持 | 不支持 |
| 多客户答案隔离 | 数据库层强制 | 无此概念 | 无此概念 |
| 白标导出 | 支持 | 无 | 无 |
| 定价 | 待定 | 企业定价 | 企业定价 |
| 自托管选项 | 技术上可行 | 不可能 | 不可能 |
| 答案库复利效应 | 核心机制 | 有限 | 有限 |
| GRC 顾问工作流 | 专门设计 | 非重点 | 非重点 |

Hypercomply 和 Conveyor 主要面向美国企业，面向大型企业客户，对澳洲中小市场和 GRC 顾问来说过于昂贵且功能不匹配。Greenlight 的切入点是这两者明显忽视的角落。

---

*最后更新：2026-05-31*
