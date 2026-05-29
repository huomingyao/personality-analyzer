// Side panel script for Relation Warning extension
const API_URL = 'http://localhost:5001';

// State
let dialogueHistory = [];
let myColor = '蓝色';
let theirColor = '红色';

// DOM Elements
const riskValueEl = document.getElementById('riskValue');
const riskBarEl = document.getElementById('riskBar');
const signalsEl = document.getElementById('signals');
const myColorEl = document.getElementById('myColor');
const theirColorEl = document.getElementById('theirColor');

// Load saved settings
async function loadSettings() {
  const result = await chrome.storage.local.get(['myColor', 'theirColor', 'dialogueHistory']);
  if (result.myColor) {
    myColor = result.myColor;
    myColorEl.value = myColor;
  }
  if (result.theirColor) {
    theirColor = result.theirColor;
    theirColorEl.value = theirColor;
  }
  if (result.dialogueHistory) {
    dialogueHistory = result.dialogueHistory;
    if (dialogueHistory.length > 0) {
      analyzeDialogue();
    }
  }
}

// Save settings
async function saveSettings() {
  await chrome.storage.local.set({ myColor, theirColor, dialogueHistory });
}

// Update UI with analysis result
function updateUI(result) {
  const riskIndex = Math.round(result.risk_index || 0);

  // Update risk value
  riskValueEl.textContent = riskIndex;

  // Update color based on risk level
  let riskClass, barColor;
  if (riskIndex < 30) {
    riskClass = 'risk-low';
    barColor = '#52c41a';
  } else if (riskIndex < 60) {
    riskClass = 'risk-medium';
    barColor = '#faad14';
  } else {
    riskClass = 'risk-high';
    barColor = '#ff4d4f';
  }

  riskValueEl.className = 'risk-value ' + riskClass;
  riskBarEl.style.width = riskIndex + '%';
  riskBarEl.style.background = barColor;

  // Update signals
  if (!result.signals || result.signals.length === 0) {
    signalsEl.innerHTML = `
      <div class="empty-state">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <div>对话氛围良好</div>
        <div style="font-size: 12px; margin-top: 4px;">${result.summary || '未检测到明显冲突'}</div>
      </div>
    `;
  } else {
    signalsEl.innerHTML = result.signals.map(s => `
      <div class="signal-item signal-${s.risk_level}">
        <div class="signal-type">${getTypeLabel(s.type)}</div>
        <div class="signal-reason">${s.reason}</div>
        ${s.suggestion ? `<div class="turn-indicator">💡 建议：${s.suggestion}</div>` : ''}
        <div class="turn-indicator">第 ${s.turn} 轮 · ${s.speaker}</div>
      </div>
    `).join('');
  }
}

// Get Chinese label for conflict type
function getTypeLabel(type) {
  const labels = {
    'blue_logic_pressure': '🔵 蓝色逻辑施压',
    'blue_perfectionism': '🔵 蓝色完美主义',
    'red_emotional_dumping': '🔴 红色情感宣泄',
    'red_dramatic_reaction': '🔴 红色情绪化反应',
    'yellow_impatience': '🟡 黄色催促',
    'yellow_demanding': '🟡 黄色要求过高',
    'green_passivity': '🟢 绿色被动',
    'green_avoidance': '🟢 绿色回避',
    'emotional_withdrawal': '😶 情感撤回',
    'escalation_detected': '⚠️ 对话升级',
  };
  return labels[type] || type;
}

// Send analysis request to API
async function analyzeDialogue() {
  if (dialogueHistory.length === 0) {
    updateUI({ risk_index: 0, signals: [], summary: '暂无对话数据' });
    return;
  }

  try {
    const response = await fetch(`${API_URL}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        dialogue: dialogueHistory,
        my_color: myColor,
        their_color: theirColor,
      }),
    });

    const result = await response.json();
    updateUI(result);
  } catch (error) {
    console.error('Analysis error:', error);
    signalsEl.innerHTML = `
      <div class="empty-state">
        <div>API 连接失败</div>
        <div style="font-size: 12px; margin-top: 4px;">请确保后端服务已启动</div>
      </div>
    `;
  }
}

// Event listeners
myColorEl.addEventListener('change', (e) => {
  myColor = e.target.value;
  saveSettings();
  analyzeDialogue();
});

theirColorEl.addEventListener('change', (e) => {
  theirColor = e.target.value;
  saveSettings();
  analyzeDialogue();
});

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'dialogueUpdated') {
    dialogueHistory = request.dialogue;
    saveSettings();
    analyzeDialogue();
  }
});

// Initialize
loadSettings();