// Habitica API Module

/**
 * 在 Habitica 中建立任務
 * @param {string} userId - Habitica User ID
 * @param {string} token - Habitica API Token
 * @param {object} task - 任務物件
 * @returns {Promise<object>} API 回應
 */
export async function createHabiticaTask(userId, token, task) {
  try {
    const response = await fetch('https://habitica.com/api/v3/tasks/user', {
      method: 'POST',
      headers: {
        'x-api-user': userId,
        'x-api-key': token,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: task.text,
        type: task.type || 'daily',
        difficulty: mapDifficulty(task.difficulty),
        notes: task.notes || '',
        checklist: task.checklist || [],
      }),
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.message || 'Habitica API 請求失敗')
    }

    const data = await response.json()
    return data
  } catch (error) {
    console.error('Habitica API 錯誤:', error)
    throw error
  }
}

/**
 * 完成 Habitica 任務
 * @param {string} userId - Habitica User ID
 * @param {string} token - Habitica API Token
 * @param {string} taskId - 任務 ID
 * @returns {Promise<object>} API 回應
 */
export async function completeHabiticaTask(userId, token, taskId) {
  try {
    const response = await fetch(`https://habitica.com/api/v3/tasks/${taskId}/score/up`, {
      method: 'POST',
      headers: {
        'x-api-user': userId,
        'x-api-key': token,
      },
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.message || 'Habitica API 請求失敗')
    }

    const data = await response.json()
    return data
  } catch (error) {
    console.error('Habitica API 錯誤:', error)
    throw error
  }
}

/**
 * 批量建立多個 Habitica 任務
 * @param {string} userId - Habitica User ID
 * @param {string} token - Habitica API Token
 * @param {Array} tasks - 任務列表
 * @returns {Promise<Array>} 所有任務的回應
 */
export async function createMultipleHabiticaTasks(userId, token, tasks) {
  const results = []
  
  for (const task of tasks) {
    try {
      const result = await createHabiticaTask(userId, token, task)
      results.push({ success: true, data: result, task })
    } catch (error) {
      results.push({ success: false, error: error.message, task })
    }
  }
  
  return results
}

/**
 * 將難度映射到 Habitica 的難度值
 * @param {string} difficulty - 難度字串
 * @returns {number} Habitica 難度值 (0.5, 1, 1.5)
 */
function mapDifficulty(difficulty) {
  switch (difficulty?.toLowerCase()) {
    case 'easy':
      return 0.5
    case 'medium':
    case 'normal':
      return 1
    case 'hard':
      return 1.5
    default:
      return 1
  }
}

/**
 * 格式化 Habitica 任務建立結果
 * @param {Array} results - 建立結果列表
 * @returns {string} 格式化訊息
 */
export function formatHabiticaResults(results) {
  const successCount = results.filter(r => r.success).length
  const failCount = results.length - successCount
  
  let message = `✅ 成功推送 ${successCount}/${results.length} 個任務到 Habitica\n`
  
  if (failCount > 0) {
    message += `⚠️ 失敗 ${failCount} 個任務\n`
    results.filter(r => !r.success).forEach(r => {
      message += `- ${r.task.text}: ${r.error}\n`
    })
  }
  
  return message
}
