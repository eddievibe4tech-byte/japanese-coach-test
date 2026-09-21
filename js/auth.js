// Authentication Module
import { signUp, signIn, signOut, getCurrentUser, onAuthStateChange, loadUserProfile } from './supabase.js'

let currentUser = null

/**
 * 初始化認證模組
 */
export async function initAuth() {
  // 檢查當前用戶
  currentUser = await getCurrentUser()
  
  if (currentUser) {
    showAppSection()
    await loadUserData(currentUser.id)
  } else {
    showAuthSection()
  }
  
  // 監聽認證狀態變化
  onAuthStateChange(async (event, session) => {
    if (event === 'SIGNED_IN') {
      currentUser = session.user
      showAppSection()
      await loadUserData(currentUser.id)
    }
    
    if (event === 'SIGNED_OUT') {
      currentUser = null
      showAuthSection()
      window.location.reload()
    }
  })
}

/**
 * 顯示認證區塊
 */
function showAuthSection() {
  document.getElementById('auth-section').classList.remove('hidden')
  document.getElementById('app-section').classList.add('hidden')
  document.getElementById('auth-btn').textContent = '登入'
}

/**
 * 顯示應用區塊
 */
function showAppSection() {
  document.getElementById('auth-section').classList.add('hidden')
  document.getElementById('app-section').classList.remove('hidden')
  document.getElementById('auth-btn').textContent = '帳號'
}

/**
 * 載入用戶資料
 * @param {string} userId - 用戶 ID
 */
async function loadUserData(userId) {
  try {
    const profile = await loadUserProfile(userId)
    
    if (profile) {
      document.getElementById('user-email').textContent = currentUser.email
      document.getElementById('current-level').textContent = profile.current_level || '五十音'
      
      // 載入設定的 API Keys（從 localStorage）
      const habiticaUserId = localStorage.getItem('habitica_user_id')
      const habiticaToken = localStorage.getItem('habitica_token')
      const groqApiKey = localStorage.getItem('groq_api_key')
      
      if (habiticaUserId) document.getElementById('habitica-user-id').value = habiticaUserId
      if (habiticaToken) document.getElementById('habitica-token').value = habiticaToken
      if (groqApiKey) document.getElementById('groq-api-key').value = groqApiKey
      
      // 載入遊戲狀態
      loadGameState(userId)
    }
  } catch (error) {
    console.error('載入用戶資料失敗:', error)
  }
}

/**
 * 載入遊戲狀態並更新 UI
 * @param {string} userId - 用戶 ID
 */
async function loadGameState(userId) {
  // 這裡會從 supabase.js 的 loadGameState 載入
  // 暫時使用預設值，實際實作時需要從 Supabase 載入
  document.getElementById('energy-display').textContent = '100'
  document.getElementById('tasks-completed-display').textContent = '0'
  document.getElementById('stages-unlocked-display').textContent = '1'
}

/**
 * 處理註冊
 * @param {Event} event
 */
export async function handleSignUp(event) {
  event.preventDefault()
  
  const email = document.getElementById('email').value
  const password = document.getElementById('password').value
  
  const { data, error } = await signUp(email, password)
  
  if (error) {
    alert('註冊失敗：' + error.message)
  } else {
    alert('註冊成功！請檢查您的電子郵件以驗證帳號。')
  }
}

/**
 * 處理登入
 * @param {Event} event
 */
export async function handleSignIn(event) {
  event.preventDefault()
  
  const email = document.getElementById('email').value
  const password = document.getElementById('password').value
  
  const { data, error } = await signIn(email, password)
  
  if (error) {
    alert('登入失敗：' + error.message)
  }
  // 成功後會由 onAuthStateChange 自動處理
}

/**
 * 處理登出
 */
export async function handleSignOut() {
  await signOut()
}

/**
 * 儲存設定到 localStorage
 */
export function saveSettings() {
  const habiticaUserId = document.getElementById('habitica-user-id').value
  const habiticaToken = document.getElementById('habitica-token').value
  const groqApiKey = document.getElementById('groq-api-key').value
  
  localStorage.setItem('habitica_user_id', habiticaUserId)
  localStorage.setItem('habitica_token', habiticaToken)
  localStorage.setItem('groq_api_key', groqApiKey)
  
  alert('✅ 設定已儲存！')
}

/**
 * 獲取儲存的 Groq API Key
 * @returns {string|null}
 */
export function getGroqApiKey() {
  return localStorage.getItem('groq_api_key')
}

/**
 * 獲取儲存的 Habitica 憑證
 * @returns {{userId: string|null, token: string|null}}
 */
export function getHabiticaCredentials() {
  return {
    userId: localStorage.getItem('habitica_user_id'),
    token: localStorage.getItem('habitica_token'),
  }
}
