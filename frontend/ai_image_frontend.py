"""Standalone AI Image Studio frontend.

Run with: python ai_image_frontend.py --api-url http://BACKEND_IP:8000
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
    :root{color-scheme:light;--paper:#f4f2ed;--white:#fffefa;--ink:#252522;--muted:#777870;--line:#deddd5;--coral:#e8664f;--green:#418365}
    *{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.55 "Segoe UI",sans-serif}
    main{max-width:1100px;margin:auto;padding:30px 24px 22px}.top{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--line);padding-bottom:18px}
    .brand{font-weight:750;font-size:21px;letter-spacing:.2px}.brand b{color:var(--coral)}.ready{color:var(--green);font-size:13px}.ready:before{content:"";display:inline-block;width:7px;height:7px;margin-right:8px;border-radius:50%;background:#55a978}
    .intro{padding:58px 0 30px}.eyebrow{margin:0 0 7px;color:var(--coral);font-size:11px;font-weight:700;letter-spacing:1.2px}h1{margin:0;font-size:36px;line-height:1.2}.intro p:last-child{color:var(--muted);margin:10px 0 0}
    .studio{display:grid;grid-template-columns:minmax(300px,.85fr) minmax(360px,1.15fr);gap:44px}.label{display:block;margin:0 0 8px;color:#686a64;font-size:12px;font-weight:700;letter-spacing:.5px;text-transform:uppercase}
    textarea,select{width:100%;border:1px solid var(--line);border-radius:7px;background:var(--white);color:var(--ink);font:inherit}textarea{height:155px;padding:13px;resize:vertical}select{padding:10px}
    .count{display:flex;justify-content:space-between;color:var(--muted);font-size:12px;margin-top:6px}.tools{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:18px;align-items:end;margin:20px 0}.ratios{display:flex;gap:5px}.ratios button{min-width:48px;padding:9px 8px;border:1px solid var(--line);border-radius:6px;background:var(--white);color:var(--ink);cursor:pointer}.ratios button.selected{border-color:var(--coral);color:#b94b38;background:#fff2ed}
    .generate{width:100%;padding:12px;border:0;border-radius:7px;background:var(--coral);color:white;font:700 15px "Segoe UI",sans-serif;cursor:pointer}.generate:disabled{opacity:.65;cursor:wait}.note,.model-note{color:var(--muted);font-size:12px}.note{text-align:center;margin:9px 0 0}
    .preview-head{display:flex;justify-content:space-between;align-items:center}.preview-head .label{margin:0}.canvas{position:relative;display:grid;place-items:center;min-height:390px;margin-top:10px;overflow:hidden;border:1px solid var(--line);border-radius:8px;background:#e9e6df}.empty{text-align:center;color:var(--muted)}.empty strong{display:block;color:var(--coral);font-size:31px}.empty p{margin:5px 0}.result{display:none;width:100%;max-height:620px;object-fit:contain}.loading{display:none;width:min(320px,80%);text-align:center;color:var(--muted)}.loading.active{display:block}.track{height:6px;margin:14px 0 7px;border-radius:4px;background:#d5d2c9;overflow:hidden}.bar{height:100%;width:0;background:var(--coral);transition:width .3s}.download{display:none;margin-top:12px;color:#b94b38;font-weight:650;text-decoration:none}.error{color:#b5392b;font-size:13px;min-height:20px;margin-top:10px}
    footer{margin-top:35px;padding-top:16px;border-top:1px solid var(--line);color:var(--muted);font-size:12px}
    @media(max-width:760px){main{padding:20px 16px}.intro{padding:38px 0 24px}h1{font-size:30px}.studio{grid-template-columns:1fr;gap:30px}.canvas{min-height:300px}.tools{gap:10px}}
  </style>
</head>
<body>
<main>
  <header class="top"><div class="brand">image<b>.</b>studio</div><span class="ready">พร้อมใช้งาน</span></header>
  <section class="intro"><p class="eyebrow">IMAGE STUDIO</p><h1>สร้างภาพของคุณ</h1><p>เปลี่ยนไอเดียให้เป็นภาพด้วยโมเดลของคุณ</p></section>
  <section class="studio">
    <div>
      <label class="label" for="prompt">Prompt</label>
      <textarea id="prompt" maxlength="500" placeholder="อธิบายภาพที่ต้องการ...">A quiet Japanese tea house hidden in a misty forest, warm light, editorial photography</textarea>
      <div class="count"><span>สูงสุด 500 ตัวอักษร</span><span id="charCount"></span></div>
      <div class="tools">
        <div><label class="label" for="model">โมเดล</label><select id="model"><option value="meinamix_v12Final.safetensors">meinamix_v12Final.safetensors</option></select><div class="model-note" id="modelNote"></div></div>
        <div><span class="label">อัตราส่วน</span><div class="ratios" id="ratios"><button class="selected" data-ratio="1:1" type="button">1:1</button><button data-ratio="4:3" type="button">4:3</button><button data-ratio="16:9" type="button">16:9</button><button data-ratio="9:16" type="button">9:16</button></div></div>
      </div>
      <button class="generate" id="generate" type="button">✦ &nbsp;สร้างภาพ</button>
      <p class="note">ใช้เวลาสร้างภาพขึ้นอยู่กับ GPU และการตั้งค่า</p><div class="error" id="error"></div>
    </div>
    <div>
      <div class="preview-head"><span class="label">Preview</span><span id="status">ยังไม่มีภาพ</span></div>
      <div class="canvas"><div class="empty" id="empty"><strong>✦</strong><p>ภาพที่สร้างจะแสดงที่นี่</p></div><img class="result" id="result" alt="ภาพที่สร้าง"><div class="loading" id="loading"><div id="progressMessage">กำลังสร้างภาพ...</div><div class="track"><div class="bar" id="bar"></div></div><strong id="percent">0%</strong></div></div>
      <a class="download" id="download" download="generated-image.png">ดาวน์โหลดรูป</a>
    </div>
  </section>
  <footer>AI Image Studio</footer>
</main>
<script>
const configuredApiUrl = __API_BASE_URL__;
const apiBaseUrl = (configuredApiUrl || `${window.location.protocol}//${window.location.hostname}:8000`).replace(/\/$/, '');
const promptInput = document.querySelector('#prompt');
const modelSelect = document.querySelector('#model');
const generateButton = document.querySelector('#generate');
const errorBox = document.querySelector('#error');
let selectedRatio = '1:1';

function updateCount(){document.querySelector('#charCount').textContent=`${promptInput.value.length} / 500`;}
async function readResponse(response){const text=await response.text();let payload={};try{payload=text?JSON.parse(text):{};}catch{payload={detail:text};}if(!response.ok)throw new Error(payload.detail||`Backend ตอบกลับด้วย HTTP ${response.status}`);return payload;}
promptInput.addEventListener('input',updateCount);
document.querySelectorAll('#ratios button').forEach(button=>button.addEventListener('click',()=>{document.querySelectorAll('#ratios button').forEach(item=>item.classList.remove('selected'));button.classList.add('selected');selectedRatio=button.dataset.ratio;}));

async function loadModels(){try{const data=await readResponse(await fetch(`${apiBaseUrl}/api/models`));const models=data.models||[];if(models.length){modelSelect.replaceChildren(...models.map(item=>{const option=document.createElement('option');option.value=item.filename;option.textContent=item.filename;return option;}));}else{document.querySelector('#modelNote').textContent='ยังไม่มีไฟล์โมเดลใน backend/models';}}catch{document.querySelector('#modelNote').textContent='ใช้โมเดลเริ่มต้น; ตรวจสอบการเชื่อมต่อ backend';}}

generateButton.addEventListener('click',async()=>{
  const text=promptInput.value.trim();if(!text||generateButton.disabled)return;
  generateButton.disabled=true;errorBox.textContent='';document.querySelector('#empty').style.display='none';document.querySelector('#result').style.display='none';document.querySelector('#download').style.display='none';
  const loading=document.querySelector('#loading');loading.classList.add('active');document.querySelector('#bar').style.width='0%';document.querySelector('#percent').textContent='0%';document.querySelector('#status').textContent='กำลังสร้างภาพ';
  try{
    const started=await readResponse(await fetch(`${apiBaseUrl}/api/generate`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:text,model:modelSelect.value,model_file:modelSelect.value,ratio:selectedRatio,count:1,cfg_scale:7})}));
    let job=started;
    while(job.status!=='completed'&&job.status!=='failed'){
      await new Promise(resolve=>window.setTimeout(resolve,800));
      job=await readResponse(await fetch(`${apiBaseUrl}/api/generate/${started.job_id}`));
      const progress=Number(job.progress||0);document.querySelector('#bar').style.width=`${progress}%`;document.querySelector('#percent').textContent=`${progress}%`;document.querySelector('#progressMessage').textContent=job.message||'กำลังสร้างภาพ...';
    }
    if(job.status==='failed')throw new Error(job.message||'สร้างภาพไม่สำเร็จ');
    const imageUrl=job.images[0].url;const image=document.querySelector('#result');image.src=imageUrl;image.style.display='block';
    const download=document.querySelector('#download');download.href=imageUrl;download.style.display='inline-block';document.querySelector('#status').textContent='สร้างเสร็จแล้ว';
  }catch(error){document.querySelector('#empty').style.display='block';document.querySelector('#status').textContent='เกิดข้อผิดพลาด';errorBox.textContent=error instanceof TypeError?`เชื่อมต่อ Backend ไม่ได้ (${apiBaseUrl})`:error.message;}
  finally{loading.classList.remove('active');generateButton.disabled=false;}
});
updateCount();loadModels();
</script>
</body>
</html>'''


def make_handler(api_url: str | None):
    class FrontendHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path not in ("/", "/index.html"):
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
    parser.add_argument("--api-url", help="Backend base URL, e.g. http://192.168.1.20:8000")
    parser.add_argument("--host", default="127.0.0.1", help="Address to serve on (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5500, help="Frontend port (default: 5500)")
    args = parser.parse_args()

    if args.api_url:
        args.api_url = args.api_url.rstrip("/")
        if not args.api_url.startswith(("http://", "https://")):
            parser.error("--api-url must start with http:// or https://")

    server = ThreadingHTTPServer((args.host, args.port), make_handler(args.api_url))
    print(f"AI Image Studio frontend: http://127.0.0.1:{args.port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping frontend.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()