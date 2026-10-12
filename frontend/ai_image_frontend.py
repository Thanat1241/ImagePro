"""Standalone AI Image Studio frontend.

Run with: python ai_image_frontend.py --api-url http://127.0.0.1:8000
"""

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


PAGE = r'''<!doctype html>
<html lang="th">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Image Studio</title>
  <style>
    :root {
      color-scheme: light;
      --paper: #f4f2ed;
      --white: #fffefa;
      --ink: #252522;
      --muted: #777870;
      --line: #deddd5;
      --coral: #e8664f;
      --coral-hover: #d3553f;
      --green: #418365;
      --red: #b5392b;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      font: 15px/1.55 "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif;
    }
    main {
      max-width: 1140px;
      margin: auto;
      padding: 30px 24px 28px;
    }
    .top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--line);
      padding-bottom: 18px;
    }
    .brand {
      font-weight: 750;
      font-size: 21px;
      letter-spacing: .2px;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .brand b { color: var(--coral); }
    .server-status {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;
      color: var(--muted);
    }
    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #aaa;
      display: inline-block;
      transition: background .3s;
    }
    .status-dot.connected { background: #55a978; }
    .status-dot.error { background: var(--red); }

    .intro { padding: 44px 0 26px; }
    .eyebrow {
      margin: 0 0 7px;
      color: var(--coral);
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 1.2px;
      text-transform: uppercase;
    }
    h1 {
      margin: 0;
      font-size: 36px;
      line-height: 1.2;
      letter-spacing: -.5px;
    }
    .intro p:last-child {
      color: var(--muted);
      margin: 8px 0 0;
    }

    .studio {
      display: grid;
      grid-template-columns: minmax(320px, .88fr) minmax(360px, 1.12fr);
      gap: 40px;
      align-items: start;
    }
    .label {
      display: block;
      margin: 0 0 8px;
      color: #686a64;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: .5px;
      text-transform: uppercase;
    }
    textarea, select, input[type="range"] {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 7px;
      background: var(--white);
      color: var(--ink);
      font: inherit;
    }
    textarea {
      height: 140px;
      padding: 13px;
      resize: vertical;
      line-height: 1.6;
    }
    select {
      padding: 10px;
      cursor: pointer;
    }

    .count-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      color: var(--muted);
      font-size: 12px;
      margin-top: 6px;
    }
    .btn-clear {
      background: none;
      border: none;
      color: var(--coral);
      cursor: pointer;
      font-size: 12px;
      padding: 0;
    }
    .btn-clear:hover { text-decoration: underline; }

    .tools-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin: 18px 0;
    }
    .tool-span-2 { grid-column: span 2; }
    .btn-group {
      display: flex;
      gap: 4px;
    }
    .btn-group button {
      flex: 1;
      padding: 8px 6px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--white);
      color: var(--ink);
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: all .15s;
    }
    .btn-group button.selected {
      border-color: var(--coral);
      color: #b94b38;
      background: #fff2ed;
    }
    .btn-group button:hover:not(.selected) { background: #eeebe3; }

    .cfg-wrap {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .cfg-wrap input {
      flex: 1;
      accent-color: var(--coral);
      cursor: pointer;
    }
    .cfg-val {
      font-size: 13px;
      font-weight: 700;
      color: var(--ink);
      min-width: 28px;
      text-align: right;
    }

    .generate {
      width: 100%;
      padding: 13px;
      border: 0;
      border-radius: 8px;
      background: var(--coral);
      color: white;
      font: 700 15px inherit;
      cursor: pointer;
      transition: background .15s, transform .1s;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }
    .generate:hover { background: var(--coral-hover); }
    .generate:active { transform: translateY(1px); }
    .generate:disabled {
      opacity: .65;
      cursor: wait;
      transform: none;
    }
    .note {
      color: var(--muted);
      font-size: 12px;
      text-align: center;
      margin: 9px 0 0;
    }
    .model-note {
      color: var(--muted);
      font-size: 11px;
      margin-top: 5px;
    }

    .preview-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }
    .preview-head .label { margin: 0; }
    .status-text {
      font-size: 13px;
      color: var(--muted);
      font-weight: 500;
    }

    .canvas {
      position: relative;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 420px;
      overflow: hidden;
      border: 1px solid var(--line);
      border-radius: 10px;
      background: #e9e6df;
      padding: 14px;
    }
    .empty {
      text-align: center;
      color: var(--muted);
    }
    .empty strong {
      display: block;
      color: var(--coral);
      font-size: 34px;
      margin-bottom: 6px;
    }
    .empty p {
      margin: 0;
      font-size: 14px;
    }

    .gallery {
      display: grid;
      gap: 14px;
      width: 100%;
    }
    .gallery.count-1 { grid-template-columns: 1fr; }
    .gallery.count-2 { grid-template-columns: 1fr 1fr; }
    .gallery.count-3, .gallery.count-4 { grid-template-columns: 1fr 1fr; }

    .gallery-item {
      position: relative;
      display: flex;
      flex-direction: column;
      align-items: center;
      background: #dedad0;
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid #d5d1c5;
    }
    .gallery-item img {
      width: 100%;
      max-height: 540px;
      object-fit: contain;
      display: block;
      background: #dedad0;
    }
    .gallery-item .actions {
      display: flex;
      justify-content: center;
      width: 100%;
      padding: 8px;
      background: rgba(255, 255, 255, 0.85);
      border-top: 1px solid var(--line);
    }
    .gallery-item .item-dl {
      padding: 6px 14px;
      background: var(--white);
      border: 1px solid var(--line);
      border-radius: 6px;
      color: var(--ink);
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all .15s;
    }
    .gallery-item .item-dl:hover {
      background: #fff2ed;
      border-color: var(--coral);
      color: #b94b38;
    }

    .loading {
      display: none;
      width: min(340px, 85%);
      text-align: center;
      color: var(--muted);
      z-index: 2;
    }
    .loading.active { display: block; }
    .spinner {
      width: 28px;
      height: 28px;
      margin: 0 auto 12px;
      border: 3px solid #ccc7bc;
      border-top-color: var(--coral);
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .track {
      height: 6px;
      margin: 12px 0 6px;
      border-radius: 4px;
      background: #d5d2c9;
      overflow: hidden;
    }
    .bar {
      height: 100%;
      width: 0;
      background: var(--coral);
      transition: width .25s ease;
    }
    .percent-val {
      font-size: 13px;
      font-weight: 700;
      color: var(--ink);
    }

    .error {
      color: var(--red);
      font-size: 13px;
      margin-top: 10px;
      background: #fae8e6;
      padding: 10px 14px;
      border-radius: 7px;
      border: 1px solid #f2c7c2;
      display: none;
      line-height: 1.5;
    }
    .error.active { display: block; }

    footer {
      margin-top: 40px;
      padding-top: 16px;
      border-top: 1px solid var(--line);
      color: var(--muted);
      font-size: 12px;
      display: flex;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 8px;
    }

    @media (max-width: 768px) {
      main { padding: 20px 16px; }
      .intro { padding: 30px 0 20px; }
      h1 { font-size: 28px; }
      .studio { grid-template-columns: 1fr; gap: 28px; }
      .tools-grid { grid-template-columns: 1fr; }
      .tool-span-2 { grid-column: span 1; }
      .canvas { min-height: 320px; }
    }
  </style>
</head>
<body>
<main>
  <header class="top">
    <div class="brand">image<b>.</b>studio</div>
    <div class="server-status">
      <span class="status-dot" id="statusDot"></span>
      <span id="statusLabel">กำลังตรวจสอบระบบ...</span>
    </div>
  </header>

  <section class="intro">
    <p class="eyebrow">IMAGE STUDIO</p>
    <h1>สร้างภาพของคุณ</h1>
    <p>เปลี่ยนไอเดียให้เป็นภาพคุณภาพสูงด้วยโมเดลของคุณ</p>
  </section>

  <section class="studio">
    <div>
      <label class="label" for="prompt">Prompt (คำอธิบายภาพ)</label>
      <textarea id="prompt" maxlength="500" placeholder="อธิบายภาพที่ต้องการ...">A young anime girl with long pink-purple hair, bright crimson eyes, playful smile, gothic school uniform, soft dramatic lighting, elegant pose, detailed portrait, character inspired by Himiko Toga from My Hero Academia, high detail, cinematic composition</textarea>
      <div class="count-bar">
        <span>สูงสุด 500 ตัวอักษร</span>
        <div>
          <button class="btn-clear" id="clearPrompt" type="button">ล้างข้อความ</button>
          &nbsp;|&nbsp;
          <span id="charCount"></span>
        </div>
      </div>

      <div class="tools-grid">
        <div class="tool-span-2">
          <label class="label" for="model">โมเดล</label>
          <select id="model">
            <option value="meinamix_v12Final.safetensors">meinamix_v12Final.safetensors</option>
          </select>
          <div class="model-note" id="modelNote">กำลังโหลดโมเดล...</div>
        </div>

        <div>
          <span class="label">อัตราส่วนภาพ</span>
          <div class="btn-group" id="ratios">
            <button class="selected" data-ratio="1:1" type="button">1:1</button>
            <button data-ratio="4:3" type="button">4:3</button>
            <button data-ratio="16:9" type="button">16:9</button>
            <button data-ratio="9:16" type="button">9:16</button>
          </div>
        </div>

        <div>
          <span class="label">จำนวนภาพ</span>
          <div class="btn-group" id="counts">
            <button class="selected" data-count="1" type="button">1</button>
            <button data-count="2" type="button">2</button>
            <button data-count="4" type="button">4</button>
          </div>
        </div>

        <div class="tool-span-2">
          <label class="label" for="cfgScale">ความอิสระของ AI (CFG Scale)</label>
          <div class="cfg-wrap">
            <input id="cfgScale" type="range" min="1" max="20" step="0.5" value="7">
            <span class="cfg-val" id="cfgVal">7.0</span>
          </div>
        </div>
      </div>

      <button class="generate" id="generate" type="button">✦ &nbsp;สร้างภาพ</button>
      <p class="note">เวลาประมวลผลขึ้นอยู่กับ GPU และการตั้งค่าของเครื่อง</p>
      <div class="error" id="error"></div>
    </div>

    <div>
      <div class="preview-head">
        <span class="label">Preview</span>
        <span class="status-text" id="status">ยังไม่มีภาพ</span>
      </div>
      <div class="canvas">
        <div class="empty" id="empty">
          <strong>✦</strong>
          <p>ภาพที่สร้างจะแสดงที่นี่</p>
        </div>

        <div class="gallery" id="gallery" style="display:none;"></div>

        <div class="loading" id="loading">
          <div class="spinner"></div>
          <div id="progressMessage">กำลังสร้างภาพ...</div>
          <div class="track"><div class="bar" id="bar"></div></div>
          <span class="percent-val" id="percent">0%</span>
        </div>
      </div>
    </div>
  </section>

  <footer>
    <span>AI Image Studio — ขับเคลื่อนด้วย Stable Diffusion &amp; Diffusers</span>
    <span id="backendInfo"></span>
  </footer>
</main>

<script>
const configuredApiUrl = __API_BASE_URL__;
const apiBaseUrl = (configuredApiUrl || `${window.location.protocol}//${window.location.hostname}:8001`).replace(/\/$/, '');

const promptInput = document.querySelector('#prompt');
const modelSelect = document.querySelector('#model');
const generateButton = document.querySelector('#generate');
const errorBox = document.querySelector('#error');
const emptyBox = document.querySelector('#empty');
const galleryBox = document.querySelector('#gallery');
const loadingBox = document.querySelector('#loading');
const barEl = document.querySelector('#bar');
const percentEl = document.querySelector('#percent');
const progressMsgEl = document.querySelector('#progressMessage');
const statusEl = document.querySelector('#status');
const cfgInput = document.querySelector('#cfgScale');
const cfgVal = document.querySelector('#cfgVal');
const statusDot = document.querySelector('#statusDot');
const statusLabel = document.querySelector('#statusLabel');
const backendInfo = document.querySelector('#backendInfo');

let selectedRatio = '1:1';
let selectedCount = 1;

if (backendInfo) {
  backendInfo.textContent = `Backend API: ${apiBaseUrl}`;
}

function updateCount() {
  if (promptInput) {
    const charCount = document.querySelector('#charCount');
    if (charCount) charCount.textContent = `${promptInput.value.length} / 500`;
  }
}

function showError(msg) {
  if (errorBox) {
    errorBox.textContent = msg;
    errorBox.classList.add('active');
  }
}

function hideError() {
  if (errorBox) {
    errorBox.textContent = '';
    errorBox.classList.remove('active');
  }
}

async function readResponse(response) {
  const text = await response.text();
  let payload = {};
  try {
    payload = text ? JSON.parse(text) : {};
  } catch {
    payload = { detail: text };
  }
  if (!response.ok) {
    throw new Error(payload.detail || `Backend ตอบกลับด้วย HTTP ${response.status}`);
  }
  return payload;
}

if (promptInput) {
  promptInput.addEventListener('input', updateCount);
}

const clearBtn = document.querySelector('#clearPrompt');
if (clearBtn && promptInput) {
  clearBtn.addEventListener('click', () => {
    promptInput.value = '';
    updateCount();
    promptInput.focus();
  });
}

document.querySelectorAll('#ratios button').forEach(button => {
  button.addEventListener('click', () => {
    document.querySelectorAll('#ratios button').forEach(item => item.classList.remove('selected'));
    button.classList.add('selected');
    selectedRatio = button.dataset.ratio;
  });
});

document.querySelectorAll('#counts button').forEach(button => {
  button.addEventListener('click', () => {
    document.querySelectorAll('#counts button').forEach(item => item.classList.remove('selected'));
    button.classList.add('selected');
    selectedCount = Number(button.dataset.count) || 1;
  });
});

if (cfgInput && cfgVal) {
  cfgInput.addEventListener('input', () => {
    cfgVal.textContent = Number(cfgInput.value).toFixed(1);
  });
}

async function downloadImage(url, filename = 'generated-image.png', button = null) {
  const originalText = button ? button.innerHTML : '';
  if (button) {
    button.textContent = 'กำลังโหลด...';
    button.style.pointerEvents = 'none';
  }
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const blob = await res.blob();
    const blobUrl = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
  } catch (err) {
    console.warn('Direct blob download failed, opening directly:', err);
    window.open(url, '_blank');
  } finally {
    if (button) {
      button.innerHTML = originalText;
      button.style.pointerEvents = '';
    }
  }
}

function renderImages(images) {
  if (!galleryBox || !emptyBox) return;
  galleryBox.innerHTML = '';
  if (!images || !images.length) {
    emptyBox.style.display = 'block';
    galleryBox.style.display = 'none';
    return;
  }

  galleryBox.className = `gallery count-${Math.min(images.length, 4)}`;
  galleryBox.style.display = 'grid';

  images.forEach((imgData, idx) => {
    const item = document.createElement('div');
    item.className = 'gallery-item';

    const img = document.createElement('img');
    img.src = imgData.url;
    img.alt = `ภาพที่สร้าง ${idx + 1}`;

    const actions = document.createElement('div');
    actions.className = 'actions';

    const dlBtn = document.createElement('button');
    dlBtn.className = 'item-dl';
    dlBtn.type = 'button';
    dlBtn.innerHTML = '⬇ ดาวน์โหลดภาพ';
    dlBtn.addEventListener('click', () => {
      const filename = `generated-${Date.now()}-${idx + 1}.png`;
      downloadImage(imgData.url, filename, dlBtn);
    });

    actions.appendChild(dlBtn);
    item.appendChild(img);
    item.appendChild(actions);
    galleryBox.appendChild(item);
  });
}

async function checkBackend() {
  if (!statusDot || !statusLabel) return false;
  try {
    const res = await fetch(`${apiBaseUrl}/api/health`, { cache: 'no-store' });
    if (res.ok) {
      statusDot.className = 'status-dot connected';
      statusLabel.textContent = 'Backend พร้อมใช้งาน';
      return true;
    }
  } catch {
    // network failure
  }
  statusDot.className = 'status-dot error';
  statusLabel.textContent = 'ไม่สามารถเชื่อมต่อ Backend ได้';
  return false;
}

async function loadModels() {
  const modelNote = document.querySelector('#modelNote');
  if (!modelSelect) return;
  try {
    const data = await readResponse(await fetch(`${apiBaseUrl}/api/models`));
    const models = data.models || [];
    if (models.length) {
      modelSelect.replaceChildren(...models.map(item => {
        const option = document.createElement('option');
        option.value = item.filename;
        option.textContent = item.filename;
        return option;
      }));
      if (modelNote) modelNote.textContent = `พบ ${models.length} โมเดลใน backend/models`;
    } else {
      if (modelNote) modelNote.textContent = 'ยังไม่มีไฟล์โมเดลใน backend/models';
    }
  } catch {
    if (modelNote) modelNote.textContent = 'ใช้โมเดลเริ่มต้น (ตรวจสอบ uvicorn)';
  }
}

if (generateButton) {
  generateButton.addEventListener('click', async () => {
    const text = promptInput ? promptInput.value.trim() : '';
    if (!text || generateButton.disabled) return;

    hideError();
    generateButton.disabled = true;
    generateButton.innerHTML = '✦ &nbsp;กำลังสร้างภาพ...';

    if (emptyBox) emptyBox.style.display = 'none';
    if (galleryBox) {
      galleryBox.innerHTML = '';
      galleryBox.style.display = 'none';
    }

    if (loadingBox) loadingBox.classList.add('active');
    if (barEl) barEl.style.width = '0%';
    if (percentEl) percentEl.textContent = '0%';
    if (progressMsgEl) progressMsgEl.textContent = 'ส่งคำขอสร้างภาพ...';
    if (statusEl) statusEl.textContent = 'กำลังสร้างภาพ';

    try {
      const cfgValue = cfgInput ? Number(cfgInput.value) : 7;
      const started = await readResponse(await fetch(`${apiBaseUrl}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: text,
          model: modelSelect ? modelSelect.value : 'meinamix_v12Final.safetensors',
          model_file: modelSelect ? modelSelect.value : 'meinamix_v12Final.safetensors',
          ratio: selectedRatio,
          count: selectedCount,
          cfg_scale: cfgValue || 7
        })
      }));

      let job = started;
      let attempts = 0;
      const maxAttempts = 300; // timeout ~ 5 นาที
      let consecutiveFails = 0;

      while (job.status !== 'completed' && job.status !== 'failed') {
        if (attempts++ >= maxAttempts) {
          throw new Error('ใช้เวลานานเกินกำหนด (Timeout 5 นาที) กรุณาตรวจสอบสถานะ AI Worker');
        }
        await new Promise(r => window.setTimeout(r, 1000));

        try {
          const pollRes = await fetch(`${apiBaseUrl}/api/generate/${started.job_id}`);
          job = await readResponse(pollRes);
          consecutiveFails = 0;
        } catch (pollErr) {
          consecutiveFails++;
          if (consecutiveFails >= 5) {
            throw new Error(`การเชื่อมต่อไปยัง Backend ขาดหาย: ${pollErr.message}`);
          }
          continue;
        }

        const progress = Number(job.progress || 0);
        if (barEl) barEl.style.width = `${progress}%`;
        if (percentEl) percentEl.textContent = `${progress}%`;
        if (progressMsgEl) progressMsgEl.textContent = job.message || 'กำลังสร้างภาพ...';
      }

      if (job.status === 'failed') {
        throw new Error(job.message || 'การสร้างภาพล้มเหลว');
      }

      renderImages(job.images || []);
      if (statusEl) statusEl.textContent = `สร้างเสร็จแล้ว (${(job.images || []).length} ภาพ)`;

    } catch (error) {
      if (emptyBox) emptyBox.style.display = 'block';
      if (statusEl) statusEl.textContent = 'เกิดข้อผิดพลาด';
      const detail = error instanceof TypeError
        ? `เชื่อมต่อ Backend ไม่ได้ (${apiBaseUrl}) ตรวจสอบว่า uvicorn กำลังทำงานอยู่`
        : error.message;
      showError(detail);
    } finally {
      if (loadingBox) loadingBox.classList.remove('active');
      generateButton.disabled = false;
      generateButton.innerHTML = '✦ &nbsp;สร้างภาพ';
    }
  });
}

updateCount();
checkBackend();
loadModels();
</script>
</body>
</html>'''


def make_handler(api_url: str | None):
    class FrontendHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith("/api/"):
                self.send_error(404)
                return

            parsed_path = self.path.split("?", 1)[0]
            if parsed_path == "/favicon.ico":
                self.send_response(204)
                self.end_headers()
                return

            if parsed_path not in ("/", "/index.html"):
                self.send_error(404)
                return

            configured_url = "null" if api_url is None else json.dumps(api_url)
            page = PAGE.replace("__API_BASE_URL__", configured_url).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(page)

        def log_message(self, format, *args):
            print(f"[{self.log_date_time_string()}] {format % args}")

    return FrontendHandler


def main():
    parser = argparse.ArgumentParser(description="Run the standalone AI Image Studio frontend.")
    parser.add_argument("--api-url", help="Backend base URL, e.g. http://127.0.0.1:8000")
    parser.add_argument("--host", default="127.0.0.1", help="Address to serve on (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5500, help="Frontend port (default: 5500)")
    args = parser.parse_args()

    if args.api_url:
        args.api_url = args.api_url.rstrip("/")
        if not args.api_url.startswith(("http://", "https://")):
            parser.error("--api-url must start with http:// or https://")

    server = ThreadingHTTPServer((args.host, args.port), make_handler(args.api_url))
    display_host = "127.0.0.1" if args.host == "0.0.0.0" else args.host
    print(f"AI Image Studio frontend running at: http://{display_host}:{args.port}")
    if args.host == "0.0.0.0":
        print(f"LAN network access available via: http://<YOUR_LOCAL_IP>:{args.port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping frontend.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()