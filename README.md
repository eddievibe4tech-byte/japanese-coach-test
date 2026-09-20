# 🗡️ 日語學習 RPG 教練（Japanese Learning RPG Coach）

> 結合 **Habitica 遊戲化**、**Groq AI 動態出題** 與 **Supabase 跨裝置同步** 的日語學習網頁應用。

![GitHub Pages](https://img.shields.io/badge/GitHub_Pages-Live-blue)
![Supabase](https://img.shields.io/badge/Supabase-Powered-green)
![PWA](https://img.shields.io/badge/PWA-Ready-orange)

---

## ✨ 功能特色

| 功能 | 說明 |
|------|------|
| 🧠 **AI 動態出題** | 透過 Groq API 根據你的狀態與等級，即時生成適合的日語學習任務 |
| 🎮 **Habitica 同步** | 一鍵將生成的任務推送到 Habitica，打怪升級賺經驗 |
| ☁️ **跨裝置同步** | 使用 Supabase 保存學習進度，手機、電腦無縫切換 |
| 📱 **PWA 支援** | 可安裝到手機主螢幕，像原生 App 一樣使用 |
| 📊 **難度自動調整** | 根據測驗結果與自我評估，動態調整任務難度 |

---

## 🏗️ 技術架構

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   前端頁面   │────▶│  Supabase   │────▶│ PostgreSQL  │
│ (GitHub     │     │  (Auth +    │     │  (用戶狀態)  │
│  Pages)     │     │   DB)       │     │             │
└──────┬──────┘     └─────────────┘     └─────────────┘
       │
       ├──────────────────────────────▶ 🤖 Groq API
       │                                (動態生成任務)
       │
       └──────────────────────────────▶ 🎮 Habitica API
                                        (同步任務/打怪)
```

### 技術棧

- **前端**：HTML / Tailwind CSS / Vanilla JavaScript
- **後端/資料庫**：[Supabase](https://supabase.com/)（PostgreSQL + Auth + Realtime）
- **AI 引擎**：[Groq API](https://console.groq.com/)（Llama 3）
- **遊戲化**：[Habitica API](https://habitica.com/apidoc/)
- **部署**：GitHub Pages
- **PWA**：Service Worker + Web App Manifest

---

## 🚀 快速開始

### 1. 建立 Supabase 專案

1. 前往 [supabase.com](https://supabase.com/) 註冊並建立新專案。
2. 進入 **SQL Editor**，執行以下腳本建立資料表：

```sql
-- 用戶資料表（關聯 Supabase Auth）
create table public.profiles (
  id uuid references auth.users on delete cascade not null primary key,
  habitica_user_id text,
  habitica_api_token text,
  groq_api_key text,
  current_level text default '五十音',
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 遊戲狀態表
create table public.game_state (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  unlocked_stages jsonb default '["新手村"]'::jsonb,
  energy integer default 100,
  total_tasks_completed integer default 0,
  last_played timestamp with time zone default timezone('utc'::text, now()),
  unique(user_id)
);

-- 學習記錄表
create table public.learning_logs (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  task_text text not null,
  task_type text not null,
  difficulty text,
  completed boolean default false,
  created_at timestamp with time zone default timezone('utc'::text, now())
);

-- 啟用 Row Level Security
alter table public.profiles enable row level security;
alter table public.game_state enable row level security;
alter table public.learning_logs enable row level security;

-- RLS 策略：用戶只能訪問自己的資料
create policy "Users can view own profile" on public.profiles
  for select using (auth.uid() = id);

create policy "Users can update own profile" on public.profiles
  for update using (auth.uid() = id);

create policy "Users can view own game state" on public.game_state
  for select using (auth.uid() = user_id);

create policy "Users can update own game state" on public.game_state
  for update using (auth.uid() = user_id);

create policy "Users can insert own game state" on public.game_state
  for insert with check (auth.uid() = user_id);

create policy "Users can view own logs" on public.learning_logs
  for select using (auth.uid() = user_id);

create policy "Users can insert own logs" on public.learning_logs
  for insert with check (auth.uid() = user_id);

-- 建立索引
create index idx_game_state_user_id on public.game_state(user_id);
create index idx_learning_logs_user_id on public.learning_logs(user_id);
```

3. 進入 **Settings** ➡️ **API**，記下：
   - **Project URL**（例如：`https://xxxxx.supabase.co`）
   - **anon public key**

### 2. 取得 API 金鑰

| 服務 | 取得方式 |
|------|----------|
| **Habitica** | Habitica ➡️ Settings ➡️ API ➡️ 複製 User ID 與 API Token |
| **Groq** | [console.groq.com](https://console.groq.com/) ➡️ API Keys ➡️ Create API Key |

### 3. 部署到 GitHub Pages

1. Fork 或建立新的 GitHub Repository。
2. 將專案檔案上傳至根目錄。
3. 進入 **Settings** ➡️ **Pages**：
   - Source：`Deploy from a branch`
   - Branch：`main` / `/ (root)` ➡️ Save
4. 等待部署完成，訪問 `https://你的帳號.github.io/倉庫名稱/`。

### 4. 首次使用

1. 打開網頁，註冊/登入帳號（Supabase Auth）。
2. 進入「設定」頁面，輸入：
   - Habitica User ID 與 API Token
   - Groq API Key
3. 選擇當前日語等級，輸入今日狀態。
4. 點擊「✨ 生成任務」➡️「🚀 推送到 Habitica」。

---

## 📁 專案結構

```
.
├── index.html          # 主頁面
├── manifest.json       # PWA 設定檔
├── sw.js               # Service Worker
├── icons/              # App 圖示
│   ├── icon-192.png
│   └── icon-512.png
├── js/
│   ├── auth.js         # Supabase 認證邏輯
│   ├── supabase.js     # Supabase 資料庫操作
│   ├── groq.js         # Groq API 呼叫
│   ├── habitica.js     # Habitica API 呼叫
│   └── app.js          # 主應用邏輯
└── css/
    └── styles.css      # 自訂樣式（可選）
```

---

## 🗺️ 使用流程

```
1. 打開網頁 / PWA
   │
2. 登入（Supabase Auth）
   │
3. 載入雲端存檔（當前等級、解鎖進度）
   │
4. 輸入今日狀態 / 選擇難度
   │
5. AI 生成任務（Groq API）
   │
6. 預覽任務 ➡️ 推送到 Habitica
   │
7. 完成任務後，更新雲端進度
   │
8. 解鎖下一階段 🎉
```

---

## 🛣️ 路線圖

- [ ] 加入「每日測驗」模組，自動評估學習成效
- [ ] 根據測驗分數自動調整難度
- [ ] 學習統計圖表（連續天數、完成任務數）
- [ ] 多語言支援（韓語、英語等）
- [ ] 離線模式（Service Worker 快取）
- [ ] 社交功能（學習排行榜、組隊打怪）

---

## ⚠️ 安全注意事項

> **重要**：本專案為純前端應用，API 金鑰的安全處理至關重要。

| 項目 | 儲存位置 | 說明 |
|------|----------|------|
| Supabase 用戶資料 | ☁️ Supabase DB | 加密儲存，受 RLS 保護 |
| Habitica API Token | 🔒 Supabase DB（選用）或 📱 本地瀏覽器 | 建議初學者存本地，進階用戶可加密存 DB |
| Groq API Key | 📱 本地瀏覽器（localStorage） | 避免上傳到公開倉庫 |

**絕對不要**將 API Key 寫死在程式碼中並 Push 到 GitHub！

---

## 📄 授權

本專案採用 [MIT License](LICENSE) 授權。

---

## 🙏 致謝

- [Habitica](https://habitica.com/) - 遊戲化任務管理
- [Groq](https://groq.com/) - 超高速 LLM 推理
- [Supabase](https://supabase.com/) - 開源 Firebase 替代品
- [Tailwind CSS](https://tailwindcss.com/) - 原子化 CSS 框架
```

---

## 🔑 關鍵技術詳解

### 1. Supabase 認證（Auth）

Supabase Auth 提供完整的用戶認證系統，支援：
- 邮箱/密碼註冊登入
- OAuth（Google、GitHub 等）
- Magic Link（免密碼登入）

#### 前端初始化

```javascript
// js/supabase.js
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://你的專案.supabase.co'
const supabaseAnonKey = '你的 anon key'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// 註冊
export async function signUp(email, password) {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
  })
  return { data, error }
}

// 登入
export async function signIn(email, password) {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })
  return { data, error }
}

// 登出
export async function signOut() {
  await supabase.auth.signOut()
}

// 監聽認證狀態變化
supabase.auth.onAuthStateChange((event, session) => {
  if (event === 'SIGNED_IN') {
    console.log('用戶已登入', session.user.id)
    loadUserData(session.user.id)
  }
  if (event === 'SIGNED_OUT') {
    console.log('用戶已登出')
    window.location.reload()
  }
})
```

### 2. 跨裝置狀態同步（核心）

#### 讀取遊戲狀態

```javascript
// js/supabase.js
export async function loadGameState(userId) {
  const { data, error } = await supabase
    .from('game_state')
    .select('*')
    .eq('user_id', userId)
    .single()

  if (error && error.code === 'PGRST116') {
    // 如果沒有記錄，建立新的
    const newState = {
      user_id: userId,
      unlocked_stages: ['新手村'],
      energy: 100,
      total_tasks_completed: 0,
    }
    const { data: newData } = await supabase
      .from('game_state')
      .insert(newState)
      .select()
      .single()
    return newData
  }

  return data
}
```

#### 更新遊戲狀態

```javascript
export async function updateGameState(userId, updates) {
  const { data, error } = await supabase
    .from('game_state')
    .update(updates)
    .eq('user_id', userId)
    .select()

  return { data, error }
}

// 使用範例：解鎖新階段
async function unlockStage(userId, stageName) {
  const currentState = await loadGameState(userId)
  const updatedStages = [...currentState.unlocked_stages, stageName]
  
  await updateGameState(userId, {
    unlocked_stages: updatedStages,
    last_played: new Date().toISOString(),
  })
}
```

#### 記錄學習日誌

```javascript
export async function logLearning(userId, task) {
  await supabase.from('learning_logs').insert({
    user_id: userId,
    task_text: task.text,
    task_type: task.type,
    difficulty: task.difficulty,
    completed: true,
  })
}
```

### 3. Groq API 動態出題

```javascript
// js/groq.js
export async function generateTasks(groqApiKey, level, status) {
  const prompt = `
    你是一位日語學習教練兼 RPG 遊戲設計師。
    使用者當前的日語等級：${level}
    使用者今日狀態：${status}
    
    請生成 2-3 個適合的日語學習任務。
    要求：
    1. 任務名稱要像 RPG 遊戲（例如：👾 平假名史萊姆）
    2. 難度必須符合使用者狀態
    3. 輸出格式必須是嚴格的 JSON 陣列
    
    JSON 格式：
    [
      {
        "text": "任務名稱",
        "type": "daily",
        "difficulty": "easy",
        "notes": "任務說明",
        "checklist": ["子任務1", "子任務2"]
      }
    ]
  `

  const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${groqApiKey}`
    },
    body: JSON.stringify({
      model: "llama3-8b-8192",
      messages: [
        { role: "system", content: "你是一位精通日語教學與遊戲化的教練，只輸出 JSON。" },
        { role: "user", content: prompt }
      ],
      temperature: 0.7,
      response_format: { type: "json_object" }
    })
  })

  const data = await response.json()
  return JSON.parse(data.choices[0].message.content)
}
```

### 4. Habitica API 同步

```javascript
// js/habitica.js
export async function createHabiticaTask(userId, token, task) {
  const response = await fetch("https://habitica.com/api/v3/tasks/user", {
    method: "POST",
    headers: {
      "x-api-user": userId,
      "x-api-key": token,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(task)
  })
  return response.json()
}

export async function completeHabiticaTask(userId, token, taskId) {
  const response = await fetch(`https://habitica.com/api/v3/tasks/${taskId}/score/up`, {
    method: "POST",
    headers: {
      "x-api-user": userId,
      "x-api-key": token,
    }
  })
  return response.json()
}
```

### 5. PWA 設定

#### `manifest.json`

```json
{
  "name": "日語學習 RPG 教練",
  "short_name": "日語教練",
  "description": "結合 AI 與 Habitica 的日語學習工具",
  "start_url": ".",
  "display": "standalone",
  "background_color": "#f3f4f6",
  "theme_color": "#4f46e5",
  "lang": "zh-TW",
  "icons": [
    {
      "src": "icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ]
}
```

#### `sw.js`（Service Worker）

```javascript
const CACHE_NAME = 'japanese-coach-v1'
const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json',
  '/js/app.js',
  '/js/supabase.js',
  '/js/groq.js',
  '/js/habitica.js',
]

// 安裝：快取靜態資源
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(urlsToCache)
    })
  )
})

// 激活：清除舊快取
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      )
    })
  )
})

// 攔截請求：快取優先，網路備援
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      if (response) return response
      
      return fetch(event.request).then((response) => {
        // 只快取靜態資源，不快取 API 請求
        if (!event.request.url.includes('supabase.co') && 
            !event.request.url.includes('habitica.com') && 
            !event.request.url.includes('groq.com')) {
          const responseToCache = response.clone()
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache)
          })
        }
        return response
      })
    })
  )
})
```

#### 在 `index.html` 中註冊

```html
<head>
  <link rel="manifest" href="manifest.json">
  <meta name="theme-color" content="#4f46e5">
  <link rel="apple-touch-icon" href="icons/icon-192.png">
  <meta name="apple-mobile-web-app-capable" content="yes">
</head>

<script>
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js')
        .then(reg => console.log('SW registered'))
        .catch(err => console.log('SW registration failed'))
    })
  }
</script>
```

---

### 6. 安全最佳實踐

#### Supabase Row Level Security（RLS）

RLS 是 Supabase 最強大的安全機制，確保**每個用戶只能訪問自己的資料**。

```sql
-- 確保用戶只能看到自己的資料
create policy "Users can only see own data" on public.game_state
  for select using (auth.uid() = user_id);

-- 確保用戶只能修改自己的資料
create policy "Users can only update own data" on public.game_state
  for update using (auth.uid() = user_id);

-- 確保用戶只能新增自己的資料
create policy "Users can only insert own data" on public.game_state
  for insert with check (auth.uid() = user_id);
```

#### API Key 處理策略

| 場景 | 建議做法 |
|------|----------|
| **開發階段** | 存在 `.env` 檔案中，加入 `.gitignore` |
| **生產環境（純前端）** | 讓用戶在網頁上輸入，存於 `localStorage` |
| **進階做法** | 將 Habitica Token 加密後存入 Supabase，每次使用時解密 |

#### 加密存儲 API Key（進階）

如果你希望用戶在多台裝置上不用重新輸入 Habitica Token，可以將其加密後存入 Supabase：

```javascript
// 使用 Web Crypto API 加密
async function encryptText(text, secretKey) {
  const encoder = new TextEncoder()
  const data = encoder.encode(text)
  const key = await crypto.subtle.importKey(
    'raw',
    encoder.encode(secretKey),
    { name: 'AES-GCM' },
    false,
    ['encrypt']
  )
  const iv = crypto.getRandomValues(new Uint8Array(12))
  const encrypted = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    key,
    data
  )
  return { iv: Array.from(iv), data: Array.from(new Uint8Array(encrypted)) }
}

// 解密
async function decryptText(encryptedObj, secretKey) {
  const encoder = new TextEncoder()
  const key = await crypto.subtle.importKey(
    'raw',
    encoder.encode(secretKey),
    { name: 'AES-GCM' },
    false,
    ['decrypt']
  )
  const decrypted = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: new Uint8Array(encryptedObj.iv) },
    key,
    new Uint8Array(encryptedObj.data)
  )
  return new TextDecoder().decode(decrypted)
}
```

---

### 7. 環境變數設定（選用）

如果你使用 Vite 或類似工具構建，可以建立 `.env` 檔案：

```env
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

> ⚠️ **注意**：`.env` 必須加入 `.gitignore`，絕對不要上傳到 GitHub！

```gitignore
# .gitignore
.env
.env.local
node_modules/
```

