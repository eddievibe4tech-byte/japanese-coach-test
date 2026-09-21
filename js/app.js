// Main Application Logic
import { initAuth, handleSignUp, handleSignIn, handleSignOut, saveSettings, getGroqApiKey, getHabiticaCredentials } from './auth.js'
import { generateTasks, formatTasksForDisplay } from './groq.js'
import { createMultipleHabiticaTasks, formatHabiticaResults } from './habitica.js'
import { getCurrentUser, loadGameState, updateGameState, logLearning } from './supabase.js'

let currentTasks = []

/**
 * 初始化應用
 */
async function initApp() {
  // 初始化認證
  await initAuth()
  
  // 綁定事件監聽器
  bindEventListeners()
}

/**
 * 綁定所有事件監聽器
 */
function bindEventListeners() {
  // 認證表單
  const authForm = document.getElementById('auth-form')
  if (authForm) {
    authForm.addEventListener('submit', handleSignIn)
  }
  
  // 註冊按鈕
  const signupBtn = document.getElementById('signup-btn')
  if (signupBtn) {
    signupBtn.addEventListener('click', handleSignUp)
  }
  
  // 登出按鈕
  const logoutBtn = document.getElementById('logout-btn')
  if (logoutBtn) {
    logoutBtn.addEventListener('click', handleSignOut)
  }
  
  // 設定表單
  const settingsForm = document.getElementById('settings-form')
  if (settingsForm) {
    settingsForm.addEventListener('submit', (e) => {
      e.preventDefault()
      saveSettings()
    })
  }
  
  // 任務生成表單
  const taskForm = document.getElementById('task-form')
  if (taskForm) {
    taskForm.addEventListener('submit', handleGenerateTasks)
  }
  
  // 推送到 Habitica 按鈕
  const pushHabiticaBtn = document.getElementById('push-habitica-btn')
  if (pushHabiticaBtn) {
    pushHabiticaBtn.addEventListener('click', handlePushToHabitica)
  }
  
  // 導航按鈕
  bindNavigationButtons()
}

/**
 * 綁定導航按鈕
 */
function bindNavigationButtons() {
  const navHome = document.getElementById('nav-home')
  const navSettings = document.getElementById('nav-settings')
  const navStats = document.getElementById('nav-stats')
  
  if (navHome) {
    navHome.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    })
  }
  
  if (navSettings) {
    navSettings.addEventListener('click', () => {
      const settingsSection = document.querySelector('.mt-8.bg-white')
      if (settingsSection) {
        settingsSection.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    })
  }
  
  if (navStats) {
    navStats.addEventListener('click', () => {
      alert('統計功能開發中！📊')
    })
  }
}

/**
 * 處理生成任務
 * @param {Event} event
 */
async function handleGenerateTasks(event) {
  event.preventDefault()
  
  const level = document.getElementById('level-select').value
  const status = document.getElementById('status-input').value
  const apiKey = getGroqApiKey()
  
  if (!apiKey) {
    alert('⚠️ 請先在設定中輸入 Groq API Key！')
    return
  }
  
  const previewDiv = document.getElementById('tasks-preview')
  const pushBtn = document.getElementById('push-habitica-btn')
  
  // 顯示載入狀態
  previewDiv.innerHTML = `
    <div class="flex justify-center items-center py-8">
      <div class="spinner mr-2"></div>
      <span class="text-gray-600">AI 正在生成任務...</span>
    </div>
  `
  pushBtn.classList.add('hidden')
  
  try {
    currentTasks = await generateTasks(apiKey, level, status)
    
    // 顯示生成的任務
    previewDiv.innerHTML = formatTasksForDisplay(currentTasks)
    
    // 顯示推送按鈕
    if (currentTasks.length > 0) {
      pushBtn.classList.remove('hidden')
    }
  } catch (error) {
    console.error('生成任務失敗:', error)
    previewDiv.innerHTML = `
      <div class="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
        <p class="text-red-600 font-semibold">❌ 生成失敗</p>
        <p class="text-red-500 text-sm mt-1">${error.message}</p>
      </div>
    `
  }
}

/**
 * 處理推送到 Habitica
 */
async function handlePushToHabitica() {
  const { userId, token } = getHabiticaCredentials()
  
  if (!userId || !token) {
    alert('⚠️ 請先在設定中輸入 Habitica User ID 和 API Token！')
    return
  }
  
  const pushBtn = document.getElementById('push-habitica-btn')
  const originalText = pushBtn.textContent
  
  // 顯示載入狀態
  pushBtn.disabled = true
  pushBtn.textContent = '🔄 推送中...'
  
  try {
    const results = await createMultipleHabiticaTasks(userId, token, currentTasks)
    
    // 顯示結果
    const message = formatHabiticaResults(results)
    alert(message)
    
    // 如果有成功推送的任務，記錄到學習日誌並更新遊戲狀態
    const successTasks = results.filter(r => r.success).map(r => r.task)
    if (successTasks.length > 0) {
      const user = await getCurrentUser()
      if (user) {
        // 記錄學習日誌
        for (const task of successTasks) {
          await logLearning(user.id, { ...task, completed: false })
        }
        
        // 更新遊戲狀態
        const gameState = await loadGameState(user.id)
        await updateGameState(user.id, {
          total_tasks_completed: gameState.total_tasks_completed + successTasks.length,
          last_played: new Date().toISOString(),
        })
        
        // 更新 UI
        document.getElementById('tasks-completed-display').textContent = 
          gameState.total_tasks_completed + successTasks.length
      }
    }
    
    // 重置按鈕
    pushBtn.disabled = false
    pushBtn.textContent = originalText
    
  } catch (error) {
    console.error('推送到 Habitica 失敗:', error)
    alert('❌ 推送失敗：' + error.message)
    pushBtn.disabled = false
    pushBtn.textContent = originalText
  }
}

// 啟動應用
document.addEventListener('DOMContentLoaded', initApp)
