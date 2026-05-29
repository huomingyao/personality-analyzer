// Background script for Relation Warning extension
console.log('[RelationWarn] Extension loaded');

chrome.runtime.onInstalled.addListener(() => {
  console.log('[RelationWarn] Installed');
});

// Handle messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'analyze') {
    // Forward to API (in production, use actual API endpoint)
    fetch('http://localhost:5001/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request.data),
    })
      .then(res => res.json())
      .then(data => sendResponse({ success: true, data }))
      .catch(err => sendResponse({ success: false, error: err.message }));

    return true; // async response
  }

  if (request.type === 'ping') {
    sendResponse({ pong: true });
  }
});