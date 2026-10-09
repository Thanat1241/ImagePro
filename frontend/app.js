const apiBaseUrl = (() => {
  const configured = window.__API_BASE_URL__ || '';
  if (configured) return configured.replace(/\/$/, '');

  const host = window.location.hostname;
  return `http://${host}:8000`;
})();
const prompt = document.querySelector('#prompt');
const charCount = document.querySelector('#charCount');
const imageCount = 1;
const model = document.querySelector('#model');
const generateButton = document.querySelector('#generate');
const generateLabel = document.querySelector('#generateLabel');
const emptyState = document.querySelector('#emptyState');
const loadingState = document.querySelector('#loadingState');
const canvasImage = document.querySelector('#canvasImage');
const imageStatus = document.querySelector('#imageStatus');
const progressBar = document.querySelector('#progressBar');
const progressPercent = document.querySelector('#progressPercent');
const progressMessage = document.querySelector('#progressMessage');
const downloadLink = document.querySelector('#downloadLink');

function removeGeneratedImage() {
  const generatedImage = canvasImage.querySelector('.generated-image');
  if (generatedImage) generatedImage.remove();
}

function updateCharCount() { charCount.textContent = `${prompt.value.length} / 500`; }

async function readApiResponse(response) {
  const text = await response.text();
  let payload = {};
  try {
    payload = text ? JSON.parse(text) : {};
  } catch {
    payload = { detail: text };
  }
  if (!response.ok) throw new Error(payload.detail || `Backend ตอบกลับด้วย HTTP ${response.status}`);
  return payload;
}

prompt.addEventListener('input', updateCharCount);
document.querySelector('#clearPrompt').addEventListener('click', () => { prompt.value = ''; updateCharCount(); prompt.focus(); });
document.querySelectorAll('#ratioGroup button').forEach((button) => button.addEventListener('click', () => { document.querySelectorAll('#ratioGroup button').forEach((item) => item.classList.remove('selected')); button.classList.add('selected'); }));

generateButton.addEventListener('click', async () => {
  if (!prompt.value.trim() || generateButton.disabled) return;
  generateButton.disabled = true;
  generateLabel.textContent = 'กำลังสร้าง...';
  emptyState.style.display = 'none';
  downloadLink.style.display = 'none';
  removeGeneratedImage();
  canvasImage.classList.remove('visible');
  loadingState.classList.add('active');
  progressBar.style.width = '0%';
  progressPercent.textContent = '0%';
  const ratio = document.querySelector('#ratioGroup .selected').dataset.ratio;
  try {
    const response = await fetch(`${apiBaseUrl}/api/generate`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ prompt: prompt.value.trim(), model: model.value, model_file: model.value, ratio, count: imageCount, cfg_scale: 7 }) });
    const result = await readApiResponse(response);
    let job = result;
    while (job.status !== 'completed' && job.status !== 'failed') {
      await new Promise((resolve) => window.setTimeout(resolve, 800));
      const statusResponse = await fetch(`${apiBaseUrl}/api/generate/${result.job_id}`);
      job = await readApiResponse(statusResponse);
      const progress = Number(job.progress || 0);
      progressBar.style.width = `${progress}%`;
      progressPercent.textContent = `${progress}%`;
      progressMessage.textContent = job.message || 'กำลังสร้างภาพ...';
    }
    if (job.status === 'failed') throw new Error(job.message || 'สร้างภาพไม่สำเร็จ');
    const imageUrl = job.images[0].url;
    const generatedImage = document.createElement('img');
    generatedImage.className = 'generated-image';
    generatedImage.src = imageUrl;
    generatedImage.alt = 'Generated result';
    canvasImage.appendChild(generatedImage);
    canvasImage.classList.add('visible');
    downloadLink.href = imageUrl;
    downloadLink.download = 'generated-image.png';
    downloadLink.style.display = 'inline-flex';
    imageStatus.textContent = 'สร้างเสร็จแล้ว';
  } catch (error) {
    removeGeneratedImage();
    emptyState.style.display = 'flex';
    imageStatus.textContent = 'เกิดข้อผิดพลาด';
    downloadLink.style.display = 'none';
    const detail = error instanceof TypeError
      ? `เชื่อมต่อ Backend ไม่ได้ (${apiBaseUrl}) ตรวจสอบว่าเปิด uvicorn และพอร์ต 8000 แล้ว`
      : error.message;
    window.alert(detail);
  } finally {
    loadingState.classList.remove('active');
    generateLabel.textContent = 'สร้างภาพ';
    generateButton.disabled = false;
  }
});

updateCharCount();
