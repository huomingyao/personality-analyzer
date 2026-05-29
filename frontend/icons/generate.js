// Simple icon generator (run in browser console)
// Paste this in browser console on any page to download icons

const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ff6b6b"/>
      <stop offset="100%" stop-color="#ffa500"/>
    </linearGradient>
  </defs>
  <rect width="128" height="128" rx="24" fill="url(#grad)"/>
  <path d="M64 24 L104 64 L64 104 L24 64 Z" fill="none" stroke="white" stroke-width="6" stroke-linejoin="round"/>
  <circle cx="64" cy="64" r="16" fill="white"/>
  <circle cx="44" cy="44" r="6" fill="white" opacity="0.8"/>
  <circle cx="84" cy="44" r="6" fill="white" opacity="0.8"/>
  <circle cx="44" cy="84" r="6" fill="white" opacity="0.8"/>
  <circle cx="84" cy="84" r="6" fill="white" opacity="0.8"/>
</svg>`;

// Download helper
async function downloadIcons() {
  const sizes = [16, 32, 48, 128];

  for (const size of sizes) {
    const canvas = document.createElement('canvas');
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext('2d');

    const img = new Image();
    const svgBlob = new Blob([svg], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(svgBlob);

    await new Promise(r => { img.onload = r; img.src = url; });

    // Draw white background
    ctx.fillStyle = '#ff6b6b';
    ctx.fillRect(0, 0, size, size);
    ctx.drawImage(img, 0, 0, size, size);

    // Download
    const link = document.createElement('a');
    link.download = `icon${size}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();

    URL.revokeObjectURL(url);
  }
}

// Only run if on local file system (not actual download)
console.log('Icon generator ready. Copy svg content to icon.svg and convert with online tool.');