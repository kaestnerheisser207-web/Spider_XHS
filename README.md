<div align="center">

<p align="center">
  <a href="https://github.com/cv-cat/Spider_XHS" target="_blank">
    <picture>
      <img width="220" src="./author/logo.jpg" alt="Spider_XHS logo">
    </picture>
  </a>
</p>

# Spider_XHS

### The All-in-One Manager for XHS

[![Skills](https://img.shields.io/badge/skills-supported-success)](https://github.com/cv-cat/XhsSkills)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/nodejs-20%2B-green)](https://nodejs.org/)
[![License](https://img.shields.io/badge/license-MIT-orange)](LICENSE)

<a href="https://trendshift.io/repositories/13631" target="_blank"><img src="https://trendshift.io/api/badge/repositories/13631" alt="cv-cat%2FSpider_XHS | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

</div>

## ❤️Sponsor

> [想出现在这里？](mailto:992822653@qq.com)

<details open>
<summary>点击折叠</summary>

<div align="center">

[![FastAIToken](https://github.com/TheSmallHanCat/flow2api/blob/main/static/sponsors/fastaitoken-banner.png)](https://www.fastaitoken.com/register?aff=48J4VXUABAAV)

</div>

**FastAIToken** 是面向开发者的 AI API 聚合平台，支持 OpenAI、Claude、Gemini 等主流大模型，兼容 OpenAI API 协议，可无缝接入 **Claude Code、Codex、Gemini CLI、Cherry Studio、Cline、Continue** 等各类 AI 开发工具。平台采用 **充值 1:1（1 元 = 1 美元 API 额度）**，帮助开发者以更低成本、更高效率地使用全球领先的大模型服务。

平台提供多个可选分组与公开状态页，开发者可根据成本、响应速度和稳定性自由选择不同渠道，并享受 **7×24 小时真人技术支持**（非机器人）。

**主要做 AI 开发接入？可以试试 [FastAIToken](https://www.fastaitoken.com/register?aff=48J4VXUABAAV)，兼容 Codex / Claude Code / Gemini CLI 等主流工具。**


---

<table>
<tr>
<td width="180"><a href="https://www.ipwo.net/?ref=githubcvcat"><img src="https://github.com/user-attachments/assets/174f644d-779e-42b9-82ba-37973201fb20" alt="ipwo" width="150"></a></td>
<td><a href="https://www.ipwo.net/?ref=githubcvcat">IPWO</a> 全球住宅代理，为开发者提供灵活的网络访问资源，适用于数据采集、市场研究、AI 应用开发等场景。开发者在不同应用场景下优化访问体验，为小红书数据研究、内容分析以及自动化开发提供更多支持。HTTP/HTTPS/socks5多种协议，免费试用，优惠折扣码“0109”</td>
</tr>

</table>

</details>

## 为什么需要这个项目？

> **在 AI 大模型爆发的时代，内容运营的竞争本质是效率竞争。**
> 本项目封装了小红书平台完整的数据采集与内容发布能力，为开发者构建 AI 运营智能体提供可靠、稳定的底层 API 支撑。

**⚠️ 本项目仅供学习交流使用，禁止任何商业化行为，如有违反，后果自负**

```
采集竞品笔记 ──► [Spider_XHS] ──► 你的 AI Agent（改写 / 生成 / 分析）──► 自动上传发布
                     ▲                                                        │
                     └──────────── 获取数据 / 管理账号 ◄──────────────────────┘
```

小红书没有开放完整的内容运营接口。想要接入 AI 大模型实现内容批量采集、智能改写、一键发布，首先需要能**稳定读写平台数据**。Spider_XHS 解决的正是这个前置问题：

- 逆向还原了小红书 PC 端与创作者平台的签名算法（a1 / web_id / b1 / websectiga / sec_poison_id / gid / x-s / x-t / x-s-common / x-b3-traceid / x-xray-traceid / x-rap-param / search_id / request_id / sign / q-signature 等参数）
- 封装全部核心 HTTP 接口，签名参数已透明处理
- 同时覆盖 **数据采集**（PC端）、**内容发布**（创作者平台）、**KOL数据**（蒲公英）三大场景

**你负责接 AI 大脑，我们负责打通小红书的神经。**

---

## 成品

### repo地址： [XHS_ALL_IN_ONE](https://github.com/cv-cat/XHS_ALL_IN_ONE)

### 账号矩阵 — 多账号绑定与健康管理

支持绑定多个 PC / Creator 账号，扫码登录、手机验证码、Cookie 导入三种方式。Cookie 加密存储，2 小时自动健康巡检，过期自动通知。

<img src="https://github.com/cv-cat/XHS_ALL_IN_ONE/blob/master/static/frontend_1.jpg" width="600" />

### 素材优化 — AI 图片润色

选择草稿中的任意图片，添加参考图，输入润色指令，AI 生成优化后的图片并原位替换。当前素材和优化结果并排对比，点击即可放大预览。

<img src="https://github.com/cv-cat/XHS_ALL_IN_ONE/blob/master/static/frontend_5.jpg" width="600" />

### 发布中心 — 一键发布到小红书

预览草稿内容和图片素材，选择 Creator 账号，设置可见性和发布模式（立即/定时），发布校验通过后一键发布到小红书创作者平台。

<img src="https://github.com/cv-cat/XHS_ALL_IN_ONE/blob/master/static/frontend_6.jpg" width="600" />

---

## 🧩 Skills 支持

当前项目已经支持基于 skills 的能力接入，既可以直接作为 `Spider_XHS` 的底层能力仓库使用，也可以通过标准化 skills 方式被上层 Agent 工具链引入。

如果你希望直接复用已经封装好的 skills，可以查看 [XhsSkills](https://github.com/cv-cat/XhsSkills)。该仓库专门用于存放基于 `Spider_XHS` 封装的 Agent Skills，目前可被 `Clawbot`、`Claude Code`、`Codex` 等支持 skills 的工具直接引入与集成。

---

## ⭐ 已实现功能

| 模块 | 功能 | 状态 |
|------|------|------|
| **小红书 PC 端** | 二维码登录 / 手机验证码登录 | ✅ |
| | 获取主页所有频道 & 推荐笔记 | ✅ |
| | 获取用户主页信息 / 自己的账号信息 | ✅ |
| | 获取用户发布 / 喜欢 / 收藏的所有笔记 | ✅ |
| | 获取笔记详细内容（无水印图片 & 视频） | ✅ |
| | 搜索笔记 & 搜索用户 | ✅ |
| | 获取笔记评论 | ✅ |
| | 获取未读消息 / 评论@提醒 / 点赞收藏 / 新增关注 | ✅ |
| **创作者平台** | 二维码登录 / 手机验证码登录 | ✅ |
| | 登录会话级自动重试（406 概率闸门） | ✅ |
| | 上传图集作品 | ✅ |
| | 上传视频作品（含转码轮询） | ✅ |
| | 查看已发布作品列表 | ✅ |
| | 发布接口 Creator RAP 本地纯算 | ✅ |
| **蒲公英平台** | 获取 KOL 博主列表 & 详细数据 | ✅ |
| | 获取博主粉丝画像 & 历史趋势 | ✅ |
| | 发起合作邀请 | ✅ |
| **千帆平台** | 获取分销商列表 & 详细数据 | ✅ |
| | 获取分销商合作品类 / 店铺 / 商品信息 | ✅ |

---

## 🤖 接入 AI 智能体

Spider_XHS 天然适合作为 AI 运营 Agent 的数据底座，以下是几种典型用法：

### 场景一：竞品笔记采集 + AI 改写 + 自动发布

```python
from apis.xhs_pc_apis import XHS_Apis
from apis.xhs_creator_apis import XHS_Creator_Apis
from xhs_utils.xhs_pc import XHSPcAuth
from xhs_utils.xhs_creator import XHSCreatorAuth

pc_auth = XHSPcAuth.from_cookie(pc_cookie)
pc_api = XHS_Apis(pc_auth).bootstrap()
creator_auth = XHSCreatorAuth.from_cookie(creator_cookie)
creator_api = XHS_Creator_Apis(creator_auth).bootstrap()

# 1. 采集竞品笔记
success, msg, note = pc_api.get_note_info(note_url)

# 2. 交给 AI 改写（接入任意大模型）
rewritten = your_ai_agent(note['content'])   # GPT / Claude / Qwen / 本地模型

# 3. 自动上传到创作者平台
creator_api.post_note({
    "title": rewritten['title'],
    "desc": rewritten['desc'],
    "media_type": "image",
    "images": [...],
    ...
})
```

### 场景二：关键词监控 + AI 情报分析

```python
# 搜索指定关键词的最新笔记，交给 AI 分析趋势
success, msg, notes = pc_api.search_some_note(query, require_num, ...)
analysis = your_ai_agent(notes)
```

### 场景三：KOL 筛选 + 智能匹配

```python
from apis.xhs_pugongying_apis import PuGongYingAPI

pgy = PuGongYingAPI()
# 获取目标类目的 KOL 数据，交给 AI 评估匹配度
kol_list = pgy.get_some_user(num=50, cookies=cookies)
best_kols = your_ai_agent(kol_list, brand_profile)
```

---

## 🎨 爬虫效果图

### 处理后的所有用户
![image](https://github.com/cv-cat/Spider_XHS/assets/94289429/00902dbd-4da1-45bc-90bb-19f5856a04ad)

### 某个用户所有的笔记
![image](https://github.com/cv-cat/Spider_XHS/assets/94289429/880884e8-4a1d-4dc1-a4dc-e168dd0e9896)

### 某个笔记具体的内容
![image](https://github.com/cv-cat/Spider_XHS/assets/94289429/d17f3f4e-cd44-4d3a-b9f6-d880da626cc8)

### 保存的 Excel
![image](https://github.com/user-attachments/assets/707f20ed-be27-4482-89b3-a5863bc360e7)

---

## 🛠️ 快速开始

### ⛳ 环境要求

- Python 3.10+
- Node.js 20+

### 🎯 安装依赖

```bash
pip install -r requirements.txt
npm install
```

### 🎨 配置登录方式

项目运行不依赖浏览器。直接在 `spider/spider.py` 中设置：

```python
login_type = 'cookie'  # cookie / qrcode / phone
```

- `qrcode`：项目本地请求二维码，用小红书 App 扫码。
- `phone`：项目直接调用手机号验证码登录接口。
- `cookie`：用户登录后直接复制完整 Cookie，或复用本项目登录流程之前保存的完整 Cookie。

只有 `cookie` 模式需要复制 `.env.example` 为 `.env`：

```
COOKIES='your_cookie_here'
```

PC 端统一通过 `XHSPcAuth` 管理登录状态、b1、DS、MNS 环境材料和会话计数：

```python
from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.xhs_pc import XHSPcAuth

# 无浏览器二维码登录
auth = XHSPcAuth.from_qrcode_login()

# 或复用已保存的登录 Cookie
# auth = XHSPcAuth.from_cookie(cookies_str)

api = XHS_Apis(auth).bootstrap()
success, message, data = api.get_unread_message()
```

`XHSPcAuth` 的登录 Cookie 有三个来源：二维码登录、手机号登录、用户直接提供完整 Cookie。前两种会按 PC 页面顺序完成 `DS → 两段 scripting → login/activate → webprofile`：项目本地生成 `a1/webId/loadts/ets`、请求签名、`websectiga` 和约 11KB 的 `profileData`，匿名 `webprofile` 验收取得 `gid` 后才允许用户扫码或发送验证码，登录成功后用服务端正式 `web_session` 覆盖访客会话。整个过程不启动、不连接浏览器。第三种原样接收用户复制过来的完整 Cookie，不重造其登录态。

Creator 端同样只允许通过三个工厂创建，业务 API 不再散传 Cookie、a1、b1 或 dsl：

```python
from apis.xhs_creator_apis import XHS_Creator_Apis
from xhs_utils.xhs_creator import XHSCreatorAuth

# 三选一：
creator_auth = XHSCreatorAuth.from_qrcode_login()
# creator_auth = XHSCreatorAuth.from_phone_login()
# creator_auth = XHSCreatorAuth.from_cookie(完整_creator_cookie)

creator_api = XHS_Creator_Apis(creator_auth).bootstrap()
success, message, notes = creator_api.get_all_posted_notes()
```

Creator 当前按浏览器 4.3.6 链路实现：`appId=ugc`、`webBuild=1.18.0`，启动阶段使用 `mns0201/nop`，安全状态就绪后切到 `mns0101/a1`。b1、MNS 装配、X-s、X-t、X-S-Common 和 profileData 均在本地计算；`mns0101` 尾部使用服务端 DS 程序导出的 `_dsf`，该程序在隔离的本地 Node VM 中执行。`_dsl`、DS/scripting code、登录 Cookie、gid 等仍按浏览器行为从服务端取得，用户无需填写。二维码和手机号登录都不启动或连接浏览器。

关于登录与发布的可靠性（26/07/25 补充）：Creator customer 域登录动作存在按设备会话标记的概率性 HTTP 406（与字段和签名无关），登录流程已内置会话级自动重试（整包重建匿名设备，上限 16 次）。b1 增加每会话抖动（x36/x37/x39/x84），避免静态指纹跨设备聚类。发布链路已按浏览器实抓对齐：permit 与 query_transcode 使用 `mns0101/nop` 冷档签名（视频转码轮询依赖 PC 侧 `web_session`，可通过 PC 扫码登录取得）、未选地点时省略 `post_loc` 键、发布请求携带 Creator 436B 指纹模板的 `x-rap-param`（浏览器信封 AES 解密还原，Uuid 每次随机）、code=-1 概率拒绝自动重发。全部 XHR 请求不再携带 `sec-ch-ua*` 客户端提示头（与浏览器行为一致，仅导航请求保留）。

`profileData` 已提纯为显式字段纯算：按固定顺序序列化 `x1..x84`，再执行 UTF-8/Base64、DES-ECB 零填充和 hex 编码。项目不会构造浏览器对象，也不会加载或执行原始指纹 SDK。正常用户无需填写这些字段；需要复现特定设备时，可通过三个工厂方法的 `web_profile_fields={...}` 参数覆盖字段，或用 `web_profile_i12_seed`、`web_profile_fi` 对齐两个小型动态段。

正常运行不需要传 b1、DSL 或浏览器 Storage。只有逆向调试、版本升级对齐时，才使用 `b1_state`、Storage 快照、`web_build` 或 `mns_env` 覆盖。

b1 默认不是从浏览器读取，而是“仓库内置的本地设备/页面指纹模板 + 当前时间与会话动态计数”，交给本地 JS 算法纯算生成。这里的“内置”指项目固化的逆向模板，不是内置或托管了一个浏览器。

PC 参数来源是明确分层的：

| 来源 | 参数 |
|------|------|
| 用户选择 | `cookie`、`qrcode` 或 `phone` 登录模式 |
| 仅逆向对齐可选 | 预计算 `b1`、`dsl`、`user_id`、保存的运行时状态、`b1_state`、`web_build`、`mns_env`、RAP 指纹、webprofile 字段/动态段覆盖 |
| JS 算法生成 | b1、MNS0101/0201/0301、X-s、X-t、X-S-Common、x-rap-param、websectiga、profileData |
| Python 状态与请求组装 | loadts、ets、seq、traceid、xy-direction、search_id、request_id |
| 自动维护的生命周期 | dsllt、last_tiga_update_time、p1、sc、tab device ID、RWP fingerprint、unread |
| 远程程序或锚点 | `_dsl`、websectiga scripting code |
| 服务端签发 | `web_session`、`id_token`、`gid`、`sec_poison_id`、验证码挑战、登录 token、RWP login token |

签名加密没有 JS/Python 两套实现：PC 与 Creator 共用算法唯一来源 `xhs_utils/xhs_core/js/`，平台目录只保留各自状态、参数装配和兼容入口；Python 的 `runtime.py` 只负责调用 Node 和校验结果。

> `web_session` 是服务端登录凭证，不能通过算法伪造；二维码和手机号模式会通过服务端登录流程取得，但全程不需要浏览器。

### 🚀 运行项目

笔记链接、用户链接、搜索关键词、保存方式和搜索筛选参数直接在 `spider/spider.py` 的入口示例中修改。

```bash
python -m spider.spider
```

### 🐳 Docker 部署（可选）

Docker 镜像默认启动独立 HTTP 服务，而不是运行示例爬虫。服务密钥是必填项；
所有 `/v1` 业务接口都要求 `Authorization: Bearer <key>`。

```bash
docker build -t spider_xhs .
docker run --rm \
  -p 127.0.0.1:5000:5000 \
  -e XHS_SERVICE_API_KEY='replace-with-a-long-random-value' \
  spider_xhs
```

启动后可访问 OpenAPI 页面 `http://127.0.0.1:5000/docs`，健康检查为
`GET /healthz`，就绪状态为 `GET /readyz`。如果仍要运行原来的本地爬虫示例，
可覆盖容器命令：

```bash
docker run --rm -e COOKIES='your_cookie_here' spider_xhs \
  python -m spider.spider
```

生产 Compose 使用同一个镜像，但把密钥、监听地址和端口留给部署环境：

```bash
XHS_SERVICE_IMAGE=spider-xhs-service:release \
XHS_SERVICE_API_KEY='至少32位高熵随机值' \
XHS_SERVICE_BIND_ADDRESS=172.17.0.1 \
XHS_SERVICE_BIND_PORT=4130 \
docker compose -f compose.production.yml up -d
```

`172.17.0.1` 适用于同一 Docker 主机上的其他容器通过
`host.docker.internal:4130` 调用，同时不会把 XHS Service 直接暴露到公网；其他
环境应按实际 Docker 网桥地址配置，不要把这个地址写进应用代码。

### 🌐 Creator HTTP 服务

HTTP 层直接复用本仓库的全部 Creator 登录、账号、作品、媒体与发布能力，不要求
调用方了解 b1、MNS、DS、X-s 或上传签名。它维护两类带 TTL 的进程内状态：未完成
的登录流程和已经认证的 Creator 会话。默认登录流程保留 10 分钟，认证会话保留 24 小时；
分别通过 `XHS_LOGIN_TTL_SECONDS` 和 `XHS_SESSION_TTL_SECONDS` 调整。

服务固定使用一个 Uvicorn worker，因为每个登录流程都持有可变的设备指纹、Cookie
和 HTTP/2 Session。容器重启会清空 `login_id` 和 `session_id`；调用方可重新扫码，
或用自己保存的完整 Creator Cookie 重建会话。多个实例应由调用方保持会话粘性，
不要对同一个 `session_id` 做无状态负载均衡。

生产环境只应监听回环地址或私有网络，并由可信入口终止 TLS、限制请求体大小；不要把
容器的 `5000` 端口直接暴露到公网。API 密钥和 `session_id` 都按账号操作凭据保护。

主要接口：

| 方法 | 路径 | 用途 |
|------|------|------|
| `POST` | `/v1/creator/sessions/cookie` | 导入并可选验证完整 Creator Cookie |
| `POST` | `/v1/creator/logins/qr` | 创建二维码登录，立即返回二维码 URL |
| `GET` | `/v1/creator/logins/qr/{login_id}` | 查询扫码/确认状态，成功后返回 `session_id` |
| `POST` | `/v1/creator/logins/phone` | 发送短信验证码 |
| `POST` | `/v1/creator/logins/phone/{login_id}/verify` | 验证短信并返回 `session_id` |
| `POST` | `/v1/creator/account` | 获取当前 Creator 账号信息并验证登录态 |
| `POST` | `/v1/creator/topics/search` | 按关键词搜索 Creator 话题 |
| `POST` | `/v1/creator/locations/search` | 按关键词搜索发布地点/POI |
| `POST` | `/v1/creator/media/permit` | 获取图片或视频上传许可 |
| `POST` | `/v1/creator/media/upload` | 上传单张图片或单个视频并返回媒体标识 |
| `POST` | `/v1/creator/videos/transcode` | 查询视频转码状态；上游可能要求 PC `web_session` |
| `POST` | `/v1/creator/files/encryption` | 获取图片文件的 Creator 加密信息 |
| `POST` | `/v1/creator/posts/posted/page` | 获取一页已发布作品及下一页游标 |
| `POST` | `/v1/creator/posts/posted/all` | 跟随游标获取全部已发布作品 |
| `POST` | `/v1/creator/posts` | 使用会话发布图文或视频笔记 |
| `GET`/`DELETE` | `/v1/creator/sessions/{session_id}` | 检查或关闭会话 |

除登录状态查询和会话检查/关闭外，认证后的 Creator 能力统一通过 JSON 请求体接收
`session_id`，避免账号操作凭据出现在查询字符串中。账号信息、话题、地点、上传许可、
媒体上传、转码、文件加密和作品列表都可以独立调用，不要求先调用发布接口。

导入 Cookie：

```bash
curl http://127.0.0.1:5000/v1/creator/sessions/cookie \
  -H 'Authorization: Bearer replace-with-a-long-random-value' \
  -H 'Content-Type: application/json' \
  -d '{"cookies":"完整 Creator Cookie","validate":true}'
```

二维码登录分两步。第一步返回 `login_id`、`qr_url` 和过期时间，调用方展示
`qr_url`；第二步按合理间隔查询，状态依次可能为 `waiting_scan`、
`waiting_confirm` 和 `authenticated`：

```bash
curl -X POST http://127.0.0.1:5000/v1/creator/logins/qr \
  -H 'Authorization: Bearer replace-with-a-long-random-value' \
  -H 'Content-Type: application/json' \
  -d '{}'

curl http://127.0.0.1:5000/v1/creator/logins/qr/login_xxx \
  -H 'Authorization: Bearer replace-with-a-long-random-value'
```

发布接口接受 base64 字节或 base64 data URL。图文使用 `images`，视频使用
`video`；服务内部继续执行 Spider_XHS 已实现的媒体许可、上传、视频封面与转码
检查、地点/话题解析和最终发布流程：

```bash
curl http://127.0.0.1:5000/v1/creator/posts \
  -H 'Authorization: Bearer replace-with-a-long-random-value' \
  -H 'Content-Type: application/json' \
  -d '{
    "session_id":"session_xxx",
    "title":"标题",
    "description":"正文",
    "media_type":"image",
    "images":[{"data":"BASE64_IMAGE_BYTES"}],
    "topics":["旅行"]
  }'
```

`proxies` 可在登录、Cookie 导入或单次发布请求中传入，例如
`{"http":"http://user:pass@host:port","https":"http://user:pass@host:port"}`。
因为全部 XHS 上游地址都是 HTTPS，传入代理时必须至少包含 `https` 或 `all`；代理
URL 支持 HTTP、HTTPS、SOCKS4 和 SOCKS5。二维码轮询和短信验证固定继承创建登录
流程时的代理，登录成功后该代理继续成为认证会话的默认代理。

发布请求没有显式传 `proxies` 时，地点、话题、DS 安全素材、上传许可、图片/视频与
封面上传、转码查询和最终发布全部继承会话默认代理；显式传入时，则由这份代理完整
覆盖本次发布的所有子请求，不允许其中某一步回落为直连。服务不会在响应中返回
Cookie 或代理，但 `session_id` 本身具有账号操作权限，必须按凭据保护；不要启用
`XHS_CREATOR_DEBUG=1`，该逆向诊断开关会打印请求实况。

### 🖥️ PC Web HTTP 服务

PC Web 与 Creator 使用相同的服务进程和 Bearer 服务密钥，但拥有独立的登录流程与
会话命名空间。PC 会话支持完整 Cookie 导入、二维码登录和手机验证码登录；认证后
可调用 `apis/xhs_pc_apis.py` 中全部公开的数据能力。PC 的 `login_id`、`session_id`
同样只保存在当前进程内，重启后需要重新登录或重新导入 Cookie。

会话与登录：

| 方法 | 路径 | 用途 |
|------|------|------|
| `POST` | `/v1/pc/sessions/cookie` | 导入完整 PC Cookie，验证账号并创建会话 |
| `POST` | `/v1/pc/logins/qr` | 创建 PC 二维码登录并返回二维码 URL |
| `GET` | `/v1/pc/logins/qr/{login_id}` | 查询扫码/确认状态，成功后返回 PC `session_id` |
| `POST` | `/v1/pc/logins/phone` | 发送 PC 登录短信验证码 |
| `POST` | `/v1/pc/logins/phone/{login_id}/verify` | 验证短信并返回 PC `session_id` |
| `GET`/`DELETE` | `/v1/pc/sessions/{session_id}` | 检查或关闭 PC 会话 |

Rednote PC 手机登录是独立 surface，不复用上述 Xiaohongshu PC 的客户端、Cookie、
`login_id` 或 `session_id`。它使用 `www.rednote.com`、`webapi.rednote.com` 和
`as.rednote.com`，并在发送验证码前独立完成匿名 Cookie、DS/scripting、
`login/activate` 与 `webprofile` 初始化。

| 方法 | 路径 | 用途 |
|------|------|------|
| `POST` | `/v1/rednote/logins/phone` | 初始化 Rednote 访客态并发送登录短信验证码 |
| `POST` | `/v1/rednote/logins/phone/{login_id}/verify` | 验证短信并返回 Rednote `session_id` |
| `GET`/`DELETE` | `/v1/rednote/sessions/{session_id}` | 检查或关闭 Rednote 会话 |

搜索、内容和用户：

| 方法 | 路径 | 用途 |
|------|------|------|
| `POST` | `/v1/pc/account` | 读取当前 PC 账号信息 |
| `POST` | `/v1/pc/search/keywords` | 获取搜索联想词 |
| `POST` | `/v1/pc/search/notes/page` | 按页搜索笔记，完整暴露筛选参数和 `search_id` |
| `POST` | `/v1/pc/search/notes/all` | 按数量连续读取搜索笔记 |
| `POST` | `/v1/pc/search/users/page` | 按页搜索用户 |
| `POST` | `/v1/pc/search/users/all` | 按数量连续读取搜索用户 |
| `POST` | `/v1/pc/notes/detail` | 读取笔记详情 |
| `POST` | `/v1/pc/notes/comments/outer/page` | 读取一页一级评论 |
| `POST` | `/v1/pc/notes/comments/outer/all` | 读取全部一级评论 |
| `POST` | `/v1/pc/notes/comments/inner/page` | 读取一页二级评论 |
| `POST` | `/v1/pc/notes/comments/inner/all` | 读取某条一级评论的全部二级评论 |
| `POST` | `/v1/pc/notes/comments/all` | 读取笔记的全部一级和二级评论 |
| `POST` | `/v1/pc/users/profile` | 读取用户主页信息 |
| `POST` | `/v1/pc/users/posts/page` | 读取一页用户发布笔记 |
| `POST` | `/v1/pc/users/posts/all` | 读取用户全部发布笔记 |
| `POST` | `/v1/pc/users/likes/page` | 读取一页用户喜欢笔记 |
| `POST` | `/v1/pc/users/likes/all` | 读取用户全部喜欢笔记 |
| `POST` | `/v1/pc/users/collects/page` | 读取一页用户收藏笔记 |
| `POST` | `/v1/pc/users/collects/all` | 读取用户全部收藏笔记 |

首页、通知和媒体解析：

| 方法 | 路径 | 用途 |
|------|------|------|
| `POST` | `/v1/pc/feed/channels` | 读取首页全部频道 |
| `POST` | `/v1/pc/feed/page` | 读取一页首页推荐笔记 |
| `POST` | `/v1/pc/feed/all` | 按数量连续读取首页推荐笔记 |
| `POST` | `/v1/pc/notifications/unread` | 读取未读消息数量 |
| `POST` | `/v1/pc/notifications/mentions/page` | 读取一页评论与 @ 提醒 |
| `POST` | `/v1/pc/notifications/mentions/all` | 读取全部评论与 @ 提醒 |
| `POST` | `/v1/pc/notifications/reactions/page` | 读取一页点赞与收藏提醒 |
| `POST` | `/v1/pc/notifications/reactions/all` | 读取全部点赞与收藏提醒 |
| `POST` | `/v1/pc/notifications/follows/page` | 读取一页新增关注 |
| `POST` | `/v1/pc/notifications/follows/all` | 读取全部新增关注 |
| `POST` | `/v1/pc/media/video/resolve` | 根据笔记 ID 生成无水印视频地址 |
| `POST` | `/v1/pc/media/image/resolve` | 将图片地址转换为无水印原图地址 |

除两个纯 URL 转换接口外，PC 数据接口都通过 JSON 请求体接收 `session_id` 和可选的
`proxies`。例如先导入 Cookie，再查询笔记：

```bash
curl http://127.0.0.1:5000/v1/pc/sessions/cookie \
  -H 'Authorization: Bearer replace-with-a-long-random-value' \
  -H 'Content-Type: application/json' \
  -d '{"cookies":"完整 PC Cookie"}'

curl http://127.0.0.1:5000/v1/pc/notes/detail \
  -H 'Authorization: Bearer replace-with-a-long-random-value' \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"pc_session_xxx","url":"小红书笔记链接"}'
```

---

## 📁 项目结构

```
Spider_XHS/
├── spider/
│   ├── __init__.py
│   └── spider.py                    # 主入口：爬虫调用示例
├── apis/
│   ├── xhs_pc_apis.py               # 小红书PC端完整API（采集）
│   ├── xhs_creator_apis.py          # 创作者平台API（上传发布）
│   ├── xhs_pc_login_apis.py         # PC端登录（二维码/手机验证码）
│   ├── xhs_creator_login_apis.py    # 创作者平台登录
│   ├── xhs_pugongying_apis.py       # 蒲公英平台API（KOL数据）
│   └── xhs_qianfan_apis.py          # 千帆平台API（分销商数据）
├── xhs_utils/
│   ├── common_util.py               # 初始化工具（读取.env配置）
│   ├── cookie_util.py               # Cookie解析
│   ├── data_util.py                 # 数据处理（Excel保存、媒体下载）
│   ├── xhs_pc/                      # PC鉴权与签名完整模块
│   │   ├── auth.py                  # 用户输入与参数归属
│   │   ├── state.py                 # 设备、页面与会话状态
│   │   ├── params.py                # 请求参数和请求头组装
│   │   ├── runtime.py               # Node调用与输出校验，不重复算法
│   │   ├── dsl.py                   # DS远程锚点获取
│   │   └── js/                      # 仅 PC 特有模板（profile/rap/deflate/aes）
│   ├── xhs_creator/                 # Creator鉴权、4.3.6状态与请求装配
│   │   ├── auth.py                  # 三种登录来源和参数归属
│   │   ├── state.py                 # b1/MNS/profileData生命周期
│   │   ├── params.py                # X-s/X-S-Common与浏览器请求头
│   │   ├── runtime.py               # 共用算法的Node调用与门禁
│   │   └── js/                      # Creator 特有模板与上传签名（profile/reference/rap指纹/sign/signature）
│   ├── xhs_core/                    # PC/Creator共用纯算和DS/websectiga核心
│   │   └── js/                      # b1/MNS/X-s/X-S-Common算法唯一实现
│   ├── xhs_auth.py                  # PC/Creator统一兼容导入层
│   ├── xhs_util.py                  # 旧导入路径兼容层
│   ├── xhs_creator_util.py          # Creator上传/发布业务数据辅助
│   ├── xhs_pugongying_util.py       # 蒲公英平台工具
│   └── xhs_qianfan_util.py          # 千帆平台工具
├── xhs_service/                      # 独立 Xiaohongshu PC、Rednote PC 与 Creator HTTP 服务
│   ├── app.py                        # FastAPI 应用、鉴权和全部 surface 路由
│   ├── pc.py                         # PC 登录、数据、通知和媒体路由
│   ├── rednote.py                    # Rednote PC 手机登录与会话路由
│   ├── models.py                     # 各 surface 共用的登录与能力请求模型
│   └── state.py                      # 各 surface 相互隔离的登录与认证会话状态
├── service_tests/                    # HTTP 服务与非交互登录测试
├── .env.example                     # 本地配置模板；复制为 .env 使用
├── requirements.txt
├── Dockerfile
└── package.json
```

---

## 🗝️ 注意事项

- `spider/spider.py` 是爬虫入口，可根据需求修改调用逻辑
- `apis/xhs_pc_apis.py` 包含所有 PC 端数据接口
- `apis/xhs_creator_apis.py` 包含创作者平台发布接口
- `xhs_utils/xhs_pc/` 是 PC 端鉴权、参数状态和签名算法的统一入口
- `xhs_utils/xhs_creator/` 是 Creator 端鉴权、参数状态和签名装配的统一入口
- Cookie 有时效性，失效后需重新获取
- 建议配合代理（proxies 参数）使用，降低封号风险

---

## 🍥 更新日志

| 日期 | 说明 |
|------|------|
| 23/08/09 | 首次提交 |
| 23/09/13 | API 更改 params 增加两个字段，修复图片无法下载，修复部分页面无法访问报错 |
| 23/09/16 | 修复较大视频编码问题，加入异常处理 |
| 23/09/18 | 代码重构，加入失败重试 |
| 23/09/19 | 新增下载搜索结果功能 |
| 23/10/05 | 新增跳过已下载功能，获取更详细的笔记和用户信息 |
| 23/10/08 | 上传至 PyPI，可通过 pip install 安装 |
| 23/10/17 | 搜索下载新增排序方式（综合 / 热门 / 最新） |
| 23/10/21 | 新增图形化界面，上传至 release v2.1.0 |
| 23/10/28 | Fix Bug：修复搜索功能隐藏问题 |
| 25/03/18 | 更新 API，修复部分问题 |
| 25/06/07 | 更新 search 接口，区分视频和图集下载，新增创作者平台 API |
| 25/07/15 | 更新 xs version56 & 小红书创作者接口 |
| 26/04/11 | 重构创作者平台 API（图集 / 视频上传），新增蒲公英 KOL 数据 API，新增千帆分销商 API，签名算法升级至最新版 |
| 26/04/28 | 更新 PC 端搜索与笔记详情风控参数，新增 `search_id` 当前算法与 `x-rap-param` 本地 JSVMP 生成，补充 `a1`、`web_id`、`websectiga` 等签名参数说明 |
| 26/07/25 | 更新全部算法：登录内置按设备会话的 406 概率闸门自动重试；b1 会话级抖动防指纹聚类；发布链路对齐浏览器（permit/query_transcode 冷档签名、省略空 post_loc、上传 header 对齐、发布携带 Creator 436B 指纹 x-rap-param、code=-1 自动重发）；X-S-Common 空 b1 阶段对齐浏览器（x8:null）；全部 XHR 去除 sec-ch-ua* 客户端提示头 |

---

## 🧸 额外说明

1. 感谢 Star ⭐ 和 Follow，项目会持续更新
2. 作者联系方式在主页，有问题随时联系
3. 欢迎 PR 和 Issue，也欢迎关注作者其他项目
4. 如果此项目对您有帮助，欢迎请作者喝一杯奶茶 ~~（开心一整天 😊）

<div align="center">
  <img src="./author/wx_pay.png" width="380px" alt="微信赞赏码">
  <img src="./author/zfb_pay.jpg" width="380px" alt="支付宝收款码">
</div>

---

## 📈 Star 趋势

<a href="https://cvcat.site/star-history/svg?repos=cv-cat/Spider_XHS&type=Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://cvcat.site/star-history/svg?repos=cv-cat/Spider_XHS&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://cvcat.site/star-history/svg?repos=cv-cat/Spider_XHS&type=Date" />
    <img alt="Star History Chart" src="https://cvcat.site/star-history/svg?repos=cv-cat/Spider_XHS&type=Date" />
  </picture>
</a>

---


## 🍔 交流群

如果你对爬虫和 AI Agent 感兴趣，请加作者主页 wx 通过邀请加入群聊

ps: 请加群，人满或者过期 issue | wx 提醒

| group-1 | group-2 | group-3 |
|:--:|:--:|:--:|
| <img width="280" alt="group1" src="https://cvcat.site/assets/group1.jpg" /> | <img width="280" alt="group2" src="https://cvcat.site/assets/group2.jpg" /> | <img width="280" alt="group3" src="https://cvcat.site/assets/group3.jpg" /> |
