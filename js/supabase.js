// Supabase Configuration
import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm'

// ⚠️ 請在 GitHub Pages 部署後，將這些值替換為你的實際配置
const SUPABASE_URL = 'https://YOUR_PROJECT.supabase.co'
const SUPABASE_ANON_KEY = 'YOUR_ANON_KEY'

// 初始化 Supabase 客戶端
export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

/**
 * 用戶註冊
 * @param {string} email - 電子郵件
 * @param {string} password - 密碼
 * @returns {Promise<{data: any, error: any}>}
 */
export async function signUp(email, password) {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
  })
  return { data, error }
}

/**
 * 用戶登入
 * @param {string} email - 電子郵件
 * @param {string} password - 密碼
 * @returns {Promise<{data: any, error: any}>}
 */
export async function signIn(email, password) {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })
  return { data, error }
}

/**
 * 用戶登出
 * @returns {Promise<void>}
 */
export async function signOut() {
  await supabase.auth.signOut()
}

/**
 * 獲取當前會話
 * @returns {Promise<any>}
 */
export async function getCurrentSession() {
  const { data: { session } } = await supabase.auth.getSession()
  return session
}

/**
 * 獲取當前用戶
 * @returns {Promise<any>}
 */
export async function getCurrentUser() {
  const { data: { user } } = await supabase.auth.getUser()
  return user
}

/**
 * 監聽認證狀態變化
 * @param {Function} callback - 回調函數
 */
export function onAuthStateChange(callback) {
  supabase.auth.onAuthStateChange((event, session) => {
    callback(event, session)
  })
}

/**
 * 載入用戶資料
 * @param {string} userId - 用戶 ID
 * @returns {Promise<any>}
 */
export async function loadUserProfile(userId) {
  const { data, error } = await supabase
    .from('profiles')
    .select('*')
    .eq('id', userId)
    .single()

  if (error && error.code === 'PGRST116') {
    // 如果沒有記錄，建立新的
    const newProfile = {
      id: userId,
      habitica_user_id: null,
      habitica_api_token: null,
      groq_api_key: null,
      current_level: '五十音',
    }
    const { data: newData } = await supabase
      .from('profiles')
      .insert(newProfile)
      .select()
      .single()
    return newData
  }

  return data
}

/**
 * 更新用戶資料
 * @param {string} userId - 用戶 ID
 * @param {object} updates - 更新內容
 * @returns {Promise<{data: any, error: any}>}
 */
export async function updateUserProfile(userId, updates) {
  const { data, error } = await supabase
    .from('profiles')
    .update(updates)
    .eq('id', userId)
    .select()
  
  return { data, error }
}

/**
 * 載入遊戲狀態
 * @param {string} userId - 用戶 ID
 * @returns {Promise<any>}
 */
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

/**
 * 更新遊戲狀態
 * @param {string} userId - 用戶 ID
 * @param {object} updates - 更新內容
 * @returns {Promise<{data: any, error: any}>}
 */
export async function updateGameState(userId, updates) {
  const { data, error } = await supabase
    .from('game_state')
    .update(updates)
    .eq('user_id', userId)
    .select()
  
  return { data, error }
}

/**
 * 記錄學習日誌
 * @param {string} userId - 用戶 ID
 * @param {object} task - 任務資訊
 * @returns {Promise<{data: any, error: any}>}
 */
export async function logLearning(userId, task) {
  const { data, error } = await supabase
    .from('learning_logs')
    .insert({
      user_id: userId,
      task_text: task.text,
      task_type: task.type || 'daily',
      difficulty: task.difficulty || 'normal',
      completed: task.completed || false,
    })
  
  return { data, error }
}

/**
 * 解鎖新階段
 * @param {string} userId - 用戶 ID
 * @param {string} stageName - 階段名稱
 * @returns {Promise<void>}
 */
export async function unlockStage(userId, stageName) {
  const currentState = await loadGameState(userId)
  if (!currentState.unlocked_stages.includes(stageName)) {
    const updatedStages = [...currentState.unlocked_stages, stageName]
    
    await updateGameState(userId, {
      unlocked_stages: updatedStages,
      last_played: new Date().toISOString(),
    })
  }
}
