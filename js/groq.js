// Groq API Module

/**
 * 使用 Groq API 生成日語學習任務
 * @param {string} apiKey - Groq API Key
 * @param {string} level - 當前日語等級
 * @param {string} status - 今日狀態
 * @returns {Promise<Array>} 生成的任務列表
 */
export async function generateTasks(apiKey, level, status) {
  const prompt = `你是一位日語學習教練兼 RPG 遊戲設計師。
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
    "checklist": ["子任務 1", "子任務 2"]
  }
]

只輸出 JSON，不要有其他文字。`

  try {
    const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: 'llama3-8b-8192',
        messages: [
          { 
            role: 'system', 
            content: '你是一位精通日語教學與遊戲化的教練，只輸出 JSON。' 
          },
          { 
            role: 'user', 
            content: prompt 
          }
        ],
        temperature: 0.7,
        response_format: { type: 'json_object' }
      }),
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.message || 'Groq API 請求失敗')
    }

    const data = await response.json()
    const content = data.choices[0].message.content
    
    // 解析 JSON 回應
    try {
      const tasks = JSON.parse(content)
      return Array.isArray(tasks) ? tasks : [tasks]
    } catch (parseError) {
      console.error('JSON 解析失敗:', parseError)
      // 如果解析失敗，嘗試從內容中提取 JSON
      const jsonMatch = content.match(/\[[\s\S]*\]/)
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0])
      }
      throw new Error('無法解析 AI 回應')
    }
  } catch (error) {
    console.error('Groq API 錯誤:', error)
    throw error
  }
}

/**
 * 格式化任務顯示
 * @param {Array} tasks - 任務列表
 * @returns {string} HTML 字串
 */
export function formatTasksForDisplay(tasks) {
  if (!tasks || tasks.length === 0) {
    return '<p class="text-gray-500 text-center py-4">沒有生成任務</p>'
  }

  return tasks.map((task, index) => `
    <div class="task-card bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg p-4 border-l-4 border-indigo-500">
      <h4 class="font-bold text-gray-800 mb-2">${task.text || '未命名任務'}</h4>
      <div class="flex items-center space-x-2 mb-2">
        <span class="px-2 py-1 bg-indigo-100 text-indigo-700 text-xs rounded-full font-medium">
          ${task.difficulty || 'normal'}
        </span>
        <span class="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full font-medium">
          ${task.type || 'daily'}
        </span>
      </div>
      ${task.notes ? `<p class="text-gray-600 text-sm mb-2">${task.notes}</p>` : ''}
      ${task.checklist && task.checklist.length > 0 ? `
        <ul class="text-sm text-gray-700 space-y-1 mt-2">
          ${task.checklist.map(item => `<li class="flex items-center"><span class="mr-2">▢</span>${item}</li>`).join('')}
        </ul>
      ` : ''}
    </div>
  `).join('')
}
