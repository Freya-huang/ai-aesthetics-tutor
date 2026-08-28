# AI美学导师智能体 - 实现计划（任务分解与优先级）

## [x] Task 1: 项目初始化与技术栈搭建
- **Priority**: high
- **Depends On**: None
- **Description**: 
  - 初始化项目结构（前后端分离架构）
  - 配置Python后端环境（FastAPI、依赖管理）
  - 配置前端项目（React + TypeScript + Vite）
  - 配置环境变量管理（API密钥、模型配置）
  - 设置基础目录结构和配置文件
- **Acceptance Criteria Addressed**: NFR-5
- **Test Requirements**:
  - `programmatic` TR-1.1: 后端服务可启动，健康检查接口返回200
  - `programmatic` TR-1.2: 前端开发服务器可启动，可访问首页
  - `programmatic` TR-1.3: 环境变量可正确加载和读取
- **Notes**: 建议后端使用FastAPI，前端使用React+TypeScript，向量数据库先用Chroma或FAISS

## [x] Task 2: 知识库文档解析与导入
- **Priority**: high
- **Depends On**: Task 1
- **Description**: 
  - 解压知识库文件
  - 编写.docx文档解析器，提取文本内容和元数据（文档编号、分类、标题、版本）
  - 实现文档分块策略（按章节、按语义块）
  - 设计知识条目数据结构（包含内容、来源、分类标签、版本信息）
  - 实现批量导入脚本
- **Acceptance Criteria Addressed**: FR-15
- **Test Requirements**:
  - `programmatic` TR-2.1: 所有知识库文档可成功解析，无遗漏
  - `programmatic` TR-2.2: 解析后的元数据正确（文档ID、分类、标题）
  - `programmatic` TR-2.3: 文档分块大小合理（200-1000字符），无截断乱码
  - `human-judgement` TR-2.4: 抽查解析文本，内容完整无乱码
- **Notes**: 知识库包含AIA/THE/VIS三类，注意文件名编码问题（中文文件名在zip中可能乱码）

## [x] Task 3: RAG检索引擎实现
- **Priority**: high
- **Depends On**: Task 2
- **Description**: 
  - 集成文本Embedding模型
  - 搭建向量数据库（本地优先，Chroma/FAISS）
  - 实现向量检索功能（支持相似度搜索、Top-K检索）
  - 实现检索结果重排序（可选）
  - 实现检索API接口（接收查询文本，返回相关知识条目）
  - 添加检索结果元数据过滤（按分类、来源）
- **Acceptance Criteria Addressed**: FR-16, FR-17, FR-18, AC-8
- **Test Requirements**:
  - `programmatic` TR-3.1: 知识库向量化完成，索引可正常加载
  - `programmatic` TR-3.2: 检索API可调用，返回结果格式正确
  - `human-judgement` TR-3.3: 使用"构图"、"色彩"、"模仿说"等关键词检索，返回相关条目
  - `programmatic` TR-3.4: 检索结果包含完整元数据（来源、ID、分类）
- **Notes**: 支持按知识库分类过滤检索结果

## [x] Task 4: LLM与视觉模型集成层
- **Priority**: high
- **Depends On**: Task 1
- **Description**: 
  - 封装LLM调用接口（支持OpenAI兼容API）
  - 封装视觉模型调用接口（支持图片理解）
  - 实现Prompt模板管理
  - 实现对话历史管理（按会话隔离）
  - 添加错误处理和重试机制
- **Acceptance Criteria Addressed**: NFR-4
- **Test Requirements**:
  - `programmatic` TR-4.1: LLM接口可正常调用，返回文本结果
  - `programmatic` TR-4.2: 视觉模型接口可接收图片并返回描述
  - `programmatic` TR-4.3: 不同会话的对话历史完全隔离
  - `programmatic` TR-4.4: API调用失败时有合理的错误提示

## [x] Task 5: PDF解析模块实现
- **Priority**: high
- **Depends On**: Task 1
- **Description**: 
  - 集成PDF解析库（PyMuPDF/pdfplumber等）
  - 实现PDF文字提取，保留页码信息
  - 实现章节结构识别（基于字体大小、位置等）
  - 实现PDF图片提取功能
  - 提取的图片暂存，供视觉模型分析
- **Acceptance Criteria Addressed**: FR-8, FR-9, AC-5
- **Test Requirements**:
  - `programmatic` TR-5.1: 上传PDF可成功解析，无报错
  - `programmatic` TR-5.2: 提取的文字段落标注正确页码
  - `programmatic` TR-5.3: PDF中的图片可被提取和保存
  - `human-judgement` TR-5.4: 抽查提取文本，页码对应正确
- **Notes**: 注意处理扫描版PDF（一期可暂不支持OCR，仅支持文字版PDF）

## [x] Task 6: 作品诊断智能体核心逻辑
- **Priority**: high
- **Depends On**: Task 3, Task 4
- **Description**: 
  - 实现图片上传验证（格式、大小、清晰度检查）
  - 实现视觉观察Prompt：引导模型只输出可观察记录，不做评价
  - 实现基于观察记录的RAG检索查询改写
  - 实现教学反馈生成Prompt，严格按照输出模板
  - 实现知识来源标注和知识点推荐逻辑
  - 实现追问处理逻辑（知识点名称+任务摘要）
  - 封装为API接口
- **Acceptance Criteria Addressed**: FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, FR-7, AC-1, AC-2, AC-3, AC-4
- **Test Requirements**:
  - `programmatic` TR-6.1: 无效格式/超大图片上传返回明确错误
  - `human-judgement` TR-6.2: 视觉观察记录仅包含客观描述，无"好看/不错"等评价词
  - `human-judgement` TR-6.3: 教学反馈包含模板要求的全部10个板块
  - `programmatic` TR-6.4: 所有知识引用都有来源标识，推荐知识点≤3个
  - `programmatic` TR-6.5: 追问功能可正常触发，生成追加反馈

## [x] Task 7: 论文解读智能体核心逻辑
- **Priority**: high
- **Depends On**: Task 3, Task 4, Task 5
- **Description**: 
  - 实现PDF上传接口
  - 实现PDF内容分析Prompt：提炼研究问题、核心观点、关键概念、论证结构
  - 实现论文图片观察：调用视觉模型生成图片描述
  - 实现关键概念提取和RAG检索
  - 实现概念史关联逻辑（仅在证据充分时关联）
  - 实现解读报告生成Prompt，严格按照输出模板
  - 实现页码引用标注和来源展示
  - 实现追问处理逻辑
  - 封装为API接口
- **Acceptance Criteria Addressed**: FR-10, FR-11, FR-12, FR-13, FR-14, AC-6, AC-7
- **Test Requirements**:
  - `programmatic` TR-7.1: PDF上传和解析流程正常
  - `human-judgement` TR-7.2: 核心观点都标注对应页码
  - `human-judgement` TR-7.3: 解读报告包含模板要求的全部10个板块
  - `human-judgement` TR-7.4: 经典问题关联有依据，无虚构理论关联
  - `programmatic` TR-7.5: 追问功能可正常触发

## [x] Task 8: 后端API完整集成
- **Priority**: high
- **Depends On**: Task 6, Task 7
- **Description**: 
  - 统一文件上传处理接口
  - 定义完整的API schema（请求/响应结构）
  - 实现会话管理（创建会话、两个智能体会话隔离）
  - 实现来源卡片数据结构
  - 添加CORS配置
  - 添加全局异常处理
  - 编写API文档
- **Acceptance Criteria Addressed**: AC-9, AC-10, AC-11
- **Test Requirements**:
  - `programmatic` TR-8.1: 所有API接口可正常调用，返回格式统一
  - `programmatic` TR-8.2: 作品诊断和论文解读使用不同会话ID，历史隔离
  - `programmatic` TR-8.3: 来源卡片数据包含所有必要字段（标题、来源ID、摘要）
  - `programmatic` TR-8.4: 异常情况返回友好错误信息

## [x] Task 9: 前端统一入口与导航
- **Priority**: high
- **Depends On**: Task 1
- **Description**: 
  - 实现首页：任务选择界面（作品诊断/论文解读两个入口）
  - 实现路由配置
  - 实现页面布局和导航组件
  - 实现全局样式和基础UI组件库
  - 添加加载状态和错误提示组件
- **Acceptance Criteria Addressed**: FR-19, AC-12
- **Test Requirements**:
  - `programmatic` TR-9.1: 首页可正常访问，显示两个任务入口
  - `programmatic` TR-9.2: 点击入口可正确跳转到对应功能页面
  - `human-judgement` TR-9.3: 页面布局清晰，导航顺畅
  - `programmatic` TR-9.4: 加载状态和错误提示正常显示

## [x] Task 10: 作品诊断前端页面
- **Priority**: high
- **Depends On**: Task 8, Task 9
- **Description**: 
  - 实现图片上传组件（拖拽上传+点击上传、预览）
  - 实现创作意图表单：作品类型、场景、表达意图、关注点
  - 实现诊断结果展示区，按模板板块展示
  - 实现来源卡片展示组件
  - 实现可点击知识点标签（交互按钮）
  - 实现追问结果追加展示
  - 对接后端API
- **Acceptance Criteria Addressed**: FR-20, FR-22, FR-23
- **Test Requirements**:
  - `programmatic` TR-10.1: 图片上传、预览功能正常
  - `programmatic` TR-10.2: 表单提交后可请求API并展示结果
  - `human-judgement` TR-10.3: 结果按板块清晰展示，来源卡片明显
  - `programmatic` TR-10.4: 点击知识点可触发追问，结果追加展示
  - `human-judgement` TR-10.5: 整体交互流畅，符合教学场景阅读体验

## [x] Task 11: 论文解读前端页面
- **Priority**: high
- **Depends On**: Task 8, Task 9
- **Description**: 
  - 实现PDF上传组件
  - 实现阅读目的表单：阅读目的、关注问题
  - 实现解读结果展示区，按模板板块展示
  - 实现页码引用高亮/标记展示
  - 实现论文图片展示组件
  - 实现来源卡片展示组件
  - 实现可点击知识点标签和追问功能
  - 对接后端API
- **Acceptance Criteria Addressed**: FR-21, FR-22, FR-23
- **Test Requirements**:
  - `programmatic` TR-11.1: PDF上传功能正常
  - `programmatic` TR-11.2: 表单提交后可请求API并展示结果
  - `human-judgement` TR-11.3: 页码引用清晰可见，来源卡片明显
  - `programmatic` TR-11.4: 论文图片可正常展示
  - `programmatic` TR-11.5: 点击知识点可触发追问，结果追加展示

## [x] Task 12: 端到端测试与优化
- **Priority**: medium
- **Depends On**: Task 10, Task 11
- **Description**: 
  - 编写端到端测试用例覆盖完整流程
  - 使用测试图片和测试PDF进行完整流程测试
  - 测试两个智能体切换时的上下文隔离
  - 测试异常情况处理（网络错误、无效文件、API超时）
  - 优化响应速度和用户体验
  - 修复发现的问题
- **Acceptance Criteria Addressed**: All ACs, NFR-1, NFR-2
- **Test Requirements**:
  - `programmatic` TR-12.1: 作品诊断完整流程（上传→填写→提交→展示→追问）可走通
  - `programmatic` TR-12.2: 论文解读完整流程（上传→填写→提交→展示→追问）可走通
  - `programmatic` TR-12.3: 两个智能体间切换无上下文污染
  - `programmatic` TR-12.4: 异常情况有友好提示，不崩溃
  - `human-judgement` TR-12.5: 整体响应速度在可接受范围内
- **Notes**: 准备若干测试样例（不同类型图片、不同PDF文档）
