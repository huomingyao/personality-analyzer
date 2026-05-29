// Content script - 聊天平台消息提取
// 支持：微信网页版、钉钉网页版、飞书、Telegram Web

console.log('[RelationWarn] Content script loaded');

// ==================== 平台配置 ====================

const PLATFORMS = {
  // 微信网页版
  wechat: {
    name: '微信',
    detect: () => document.domain.includes('wx.qq') || document.domain.includes('weixin.qq'),
    // 消息列表容器
    containerSelector: '.chat__content, .message_list, [class*="chat"]',
    // 单条消息
    messageSelector: '.message_item, .message, [class*="message-item"]',
    // 消息内容
    contentSelector: '.message_text, [class*="content"]',
    // 发送者判断：通过头像位置、消息方向
    isMeBy: (el) => {
      const bubble = el.querySelector('[class*="bubble"]');
      if (!bubble) return null;
      return bubble.classList.contains('me') || bubble.classList.contains('self')
        ? 'me' : 'them';
    },
  },

  // 钉钉网页版
  dingtalk: {
    name: '钉钉',
    detect: () => document.domain.includes('dingtalk') || document.domain.includes('im.dingtalk'),
    containerSelector: '.conversation-view, .message-list, [class*="message-list"]',
    messageSelector: '.message-item, .msg-item, [class*="message-item"]',
    contentSelector: '.msg-content, [class*="text"]',
    isMeBy: (el) => {
      // 钉钉消息有自己的类名
      const container = el.closest('[class*="conversation"]');
      if (container) {
        const name = el.querySelector('[class*="sender"]');
        // 如果是私聊，可以通过名字判断
      }
      return el.querySelector('[class*="mine"]') ? 'me' : 'them';
    },
  },

  // 飞书
  feishu: {
    name: '飞书',
    detect: () => document.domain.includes('feishu') || document.domain.includes('larksuite'),
    containerSelector: '.messages-container, [class*="message-list"]',
    messageSelector: '.message, [class*="message-item"]',
    contentSelector: '[class*="content"], [class*="text"]',
    isMeBy: (el) => el.querySelector('[class*="own"]') ? 'me' : 'them',
  },

  // Telegram Web
  telegram: {
    name: 'Telegram',
    detect: () => document.domain.includes('web.telegram') || document.domain.includes('telegram'),
    containerSelector: '.messages-container, .chat-messages',
    messageSelector: '.message, [class*="message"]',
    contentSelector: '.message-text, [class*="text"]',
    isMeBy: (el) => {
      const bubble = el.querySelector('.bubble');
      return bubble && bubble.classList.contains('out') ? 'me' : 'them';
    },
  },
};

// ==================== 消息提取 ====================

function detectPlatform() {
  for (const [key, platform] of Object.entries(PLATFORMS)) {
    if (platform.detect()) {
      console.log(`[RelationWarn] Detected platform: ${platform.name}`);
      return platform;
    }
  }
  console.log('[RelationWarn] Unknown platform, using generic mode');
  return null;
}

function extractMessages() {
  const platform = detectPlatform();
  const messages = [];

  if (!platform) {
    // 兜底：尝试通用选择器
    return extractGeneric();
  }

  // 尝试多种选择器
  const selectors = platform.containerSelector.split(', ');
  let container = null;

  for (const sel of selectors) {
    container = document.querySelector(sel);
    if (container) break;
  }

  if (!container) {
    console.log('[RelationWarn] Container not found, trying generic');
    return extractGeneric();
  }

  // 提取消息
  const msgSelectors = platform.messageSelector.split(', ');
  let messageEls = [];

  for (const sel of msgSelectors) {
    messageEls = container.querySelectorAll(sel);
    if (messageEls.length > 0) break;
  }

  if (messageEls.length === 0) {
    console.log('[RelationWarn] No messages found');
    return [];
  }

  messageEls.forEach((el, index) => {
    // 提取内容
    let content = '';
    for (const sel of platform.contentSelector.split(', ')) {
      const contentEl = el.querySelector(sel);
      if (contentEl) {
        content = contentEl.textContent.trim();
        break;
      }
    }
    if (!content) {
      content = el.textContent.trim();
    }

    // 判断发送者
    let speaker = '对方';
    if (platform.isMeBy) {
      const who = platform.isMeBy(el);
      if (who === 'me') speaker = '我';
      else if (who === 'them') speaker = '对方';
    }

    // 过滤系统消息
    if (content && !isSystemMessage(content)) {
      messages.push({
        turn: messages.length + 1,
        speaker,
        content: content.substring(0, 500),
      });
    }
  });

  return messages;
}

function extractGeneric() {
  // 通用兜底：查找所有可能包含聊天气泡的元素
  const messages = [];

  // 尝试常见的聊天容器
  const containers = document.querySelectorAll('body');
  const bubbles = document.querySelectorAll('[class*="bubble"], [class*="message"], [class*="chat"]');

  bubbles.forEach((el, index) => {
    const text = el.textContent.trim();
    if (text && text.length > 1 && text.length < 1000) {
      // 简单判断：如果包含"我"相关的词，或者位置靠右，可能是我的消息
      let speaker = '对方';
      if (el.className.includes('self') || el.className.includes('me') || el.className.includes('out')) {
        speaker = '我';
      }

      messages.push({
        turn: messages.length + 1,
        speaker,
        content: text.substring(0, 500),
      });
    }
  });

  return messages;
}

function isSystemMessage(content) {
  const systemKeywords = ['拍了拍', '撤回了一条消息', '已收到', '对方已成为', '加入了群聊'];
  return systemKeywords.some(k => content.includes(k));
}

// ==================== 调试工具 ====================

// 在控制台执行 window.debugMessages() 查看提取结果
window.debugMessages = function() {
  const messages = extractMessages();
  console.log('=== Extracted Messages ===');
  messages.forEach(m => {
    console.log(`[${m.turn}] ${m.speaker}: ${m.content.substring(0, 50)}`);
  });
  return messages;
};

// ==================== 主动检测 ====================

let lastMessageCount = 0;
let lastMessages = [];

function checkForNewMessages() {
  const messages = extractMessages();

  if (messages.length !== lastMessageCount && messages.length > 0) {
    lastMessageCount = messages.length;
    lastMessages = messages;

    console.log(`[RelationWarn] ${messages.length} messages found`);

    // 通知 side panel
    notifySidePanel(messages);
  }
}

// 通知 side panel
function notifySidePanel(messages) {
  chrome.runtime.sendMessage({
    type: 'dialogueUpdated',
    dialogue: messages,
    platform: detectPlatform()?.name || 'Unknown',
  }).catch(err => {
    // 静默失败
  });
}

// ==================== 启动观察 ====================

console.log('[RelationWarn] Starting chat observer');

// 每 2 秒检查一次
setInterval(checkForNewMessages, 2000);

// 立即检查一次
setTimeout(checkForNewMessages, 1000);

// 监听 DOM 变化（SPA 导航）
const observer = new MutationObserver(() => {
  console.log('[RelationWarn] DOM changed, re-scanning');
  setTimeout(checkForNewMessages, 1000);
});

observer.observe(document.body, {
  childList: true,
  subtree: true
});

// 监听 URL 变化
let lastUrl = location.href;
setInterval(() => {
  if (location.href !== lastUrl) {
    lastUrl = location.href;
    console.log('[RelationWarn] URL changed, re-scanning');
    setTimeout(checkForNewMessages, 2000);
  }
}, 1000);

console.log('[RelationWarn] Ready. Run debugMessages() in console to debug.');
