# 定制火车票生成器 - The Implementation Plan (Decomposed and Prioritized Task List)

## [ ] Task 1: 保存模板图片并安装依赖
- **Priority**: high
- **Depends On**: None
- **Description**: 
  - 将用户提供的空白火车票模板保存到前端 `frontend/public/assets/` 目录
  - 在前端项目中安装 qrcode 和 html2canvas 依赖包
  - 安装对应 TypeScript 类型定义
- **Acceptance Criteria Addressed**: [AC-3, AC-4]
- **Test Requirements**:
  - `programmatic` TR-1.1: 模板图片存在于 public/assets/ticket-template.png
  - `programmatic` TR-1.2: package.json 中包含 qrcode 和 html2canvas 依赖
  - `programmatic` TR-1.3: 运行 npm install 无错误
- **Notes**: 使用 npm install qrcode html2canvas @types/qrcode

## [ ] Task 2: 创建火车票数据类型定义
- **Priority**: high
- **Depends On**: None
- **Description**: 
  - 在 frontend/src/types/ 中创建 ticket.ts 类型文件
  - 定义 TicketFormData 接口，包含所有表单字段
  - 定义默认表单数据示例值
- **Acceptance Criteria Addressed**: [AC-1]
- **Test Requirements**:
  - `programmatic` TR-2.1: TypeScript 编译无类型错误
  - `human-judgement` TR-2.2: 类型定义包含所有必要字段（出发站、到达站、年、月、日、时、分、车次、姓名、席别、座位号、票价、检票口、身份证号）

## [ ] Task 3: 创建火车票预览组件
- **Priority**: high
- **Depends On**: [Task 1, Task 2]
- **Description**: 
  - 创建 TicketPreview.tsx 组件
  - 使用相对定位容器，背景为火车票模板图片
  - 使用绝对定位精确定位各个文字字段位置
  - 样式匹配火车票字体（黑体/宋体）、字号、颜色
  - 添加"仅供娱乐纪念，非真实有效车票"水印或提示
- **Acceptance Criteria Addressed**: [AC-2, AC-3, AC-9]
- **Test Requirements**:
  - `human-judgement` TR-3.1: 所有文字位置与模板占位符对齐
  - `human-judgement` TR-3.2: 字体样式、大小、颜色看起来像真实火车票
  - `human-judgement` TR-3.3: 能看到免责提示文字
  - `programmatic` TR-3.4: 组件接收 TicketFormData 作为 props 并正确渲染

## [ ] Task 4: 创建二维码组件
- **Priority**: high
- **Depends On**: [Task 2]
- **Description**: 
  - 创建 TicketQRCode.tsx 组件
  - 使用 qrcode 库根据表单数据生成二维码
  - 将车票信息格式化为易读的纯文本
  - 生成的二维码渲染在指定大小的容器内
- **Acceptance Criteria Addressed**: [AC-4, AC-5]
- **Test Requirements**:
  - `programmatic` TR-4.1: 二维码正确生成，无报错
  - `human-judgement` TR-4.2: 手机扫码后显示格式化的纯文本车票信息
  - `programmatic` TR-4.3: 二维码内容包含所有关键字段
- **Notes**: 二维码文本格式示例：
  ```
  🚄 G1234次
  北京南 → 上海虹桥
  2024年08月22日 08:30开
  乘客：张三
  席别：二等座
  座位：05车12A号
  票价：¥553.00元
  检票口：12A
  ```

## [ ] Task 5: 创建表单输入组件
- **Priority**: high
- **Depends On**: [Task 2]
- **Description**: 
  - 创建 TicketForm.tsx 组件
  - 使用受控组件管理表单状态
  - 布局采用两列或表单分组，使用方便
  - 添加输入验证（如日期、时间格式）
  - 席别使用下拉选择（二等座、一等座、商务座、硬座、硬卧、软卧、无座）
  - 包含"生成预览"和"重置"按钮
- **Acceptance Criteria Addressed**: [AC-1, AC-7]
- **Test Requirements**:
  - `human-judgement` TR-5.1: 表单布局清晰，输入方便
  - `programmatic` TR-5.2: 重置按钮能清空所有字段恢复默认
  - `human-judgement` TR-5.3: 席别有合理的预设选项
  - `programmatic` TR-5.4: 表单状态变化正确传递给父组件

## [ ] Task 6: 创建火车票生成主页面
- **Priority**: high
- **Depends On**: [Task 3, Task 4, Task 5]
- **Description**: 
  - 创建 TrainTicket.tsx 页面组件
  - 组合 TicketForm 和 TicketPreview（左侧表单右侧预览布局，或上下布局响应式）
  - 集成 TicketQRCode 组件到预览右下角
  - 实现实时预览（表单变化立即更新预览）
  - 添加页面标题和说明
- **Acceptance Criteria Addressed**: [AC-1, AC-2, AC-3, AC-4]
- **Test Requirements**:
  - `human-judgement` TR-6.1: 页面布局美观，响应式适配
  - `human-judgement` TR-6.2: 修改表单任意字段，预览实时更新
  - `human-judgement` TR-6.3: 二维码在预览中正确显示在右下角方框位置

## [ ] Task 7: 实现图片下载功能
- **Priority**: high
- **Depends On**: [Task 6]
- **Description**: 
  - 添加"下载车票"按钮
  - 使用 html2canvas 将火车票预览区域转换为 Canvas
  - 以 2x 像素比生成高清图片
  - 转换为 PNG 格式触发浏览器下载
  - 文件名自动包含日期和车次（如：火车票_G1234_20240822.png）
- **Acceptance Criteria Addressed**: [AC-6]
- **Test Requirements**:
  - `programmatic` TR-7.1: 点击下载按钮触发文件下载
  - `human-judgement` TR-7.2: 下载的图片清晰，文字完整，二维码可扫描
  - `programmatic` TR-7.3: 下载的文件名格式正确

## [ ] Task 8: 配置路由和样式
- **Priority**: medium
- **Depends On**: [Task 6]
- **Description**: 
  - 在 App.tsx 中添加 /ticket 路由
  - 注意：不添加到主导航菜单，作为独立路由
  - 添加页面 CSS 样式，保持与现有项目风格协调
  - 确保响应式布局在手机上也能正常使用
- **Acceptance Criteria Addressed**: [AC-8]
- **Test Requirements**:
  - `programmatic` TR-8.1: 访问 http://localhost:5173/ticket 能正确打开页面
  - `human-judgement` TR-8.2: 不影响现有主页和其他功能页面
  - `human-judgement` TR-8.3: 手机端布局可用

## [ ] Task 9: 添加身份证号脱敏和格式化
- **Priority**: medium
- **Depends On**: [Task 3, Task 5]
- **Description**: 
  - 身份证号输入框自动格式化显示（中间8位用*替代）
  - 票价自动格式化为两位小数
  - 日期和时间不足两位补零
- **Acceptance Criteria Addressed**: [AC-3]
- **Test Requirements**:
  - `human-judgement` TR-9.1: 身份证号显示类似 110***********1234
  - `programmatic` TR-9.2: 票价始终显示两位小数（如：¥553.00）
  - `programmatic` TR-9.3: 月日时分小于10时自动补零（如：08月05日 09:05）

## [ ] Task 10: 端到端测试和优化
- **Priority**: medium
- **Depends On**: [Task 7, Task 8, Task 9]
- **Description**: 
  - 完整流程测试：填写所有字段→预览→扫码→下载
  - 测试不同席别、不同站点、不同日期的显示
  - 测试二维码在不同手机扫码软件上的可读性
  - 优化文字位置微调，确保与模板对齐
  - 测试图片下载质量
- **Acceptance Criteria Addressed**: [AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9]
- **Test Requirements**:
  - `human-judgement` TR-10.1: 完整流程顺畅，无控制台错误
  - `human-judgement` TR-10.2: 下载的图片打印/保存效果良好
  - `human-judgement` TR-10.3: 二维码扫码清晰，文本可读
