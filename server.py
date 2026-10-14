import os
import subprocess
import hashlib
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# 🔐 商业私钥（核心加密盐，用来和设备特征码共同计算激活码）
SECRET_SALT = "LingJing_GuangSuo_2026_Master_Key"

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# 🔑 客户端激活校验接口
@app.route('/api/verify', methods=['POST'])
def verify_code():
    data = request.json
    code = data.get('code', '').strip().upper()
    device_id = data.get('deviceId', '').strip()
    
    if not device_id:
        return jsonify({"success": False, "message": "获取设备特征码失败！"})
    
    raw_data = device_id + SECRET_SALT
    full_hash = hashlib.sha256(raw_data.encode('utf-8')).hexdigest().upper()
    correct_code = f"LJ-{full_hash[0:4]}-{full_hash[4:8]}-{full_hash[8:12]}-{full_hash[12:16]}"
    
    if code == correct_code:
        return jsonify({"success": True, "message": "激活成功！欢迎使用灵境光梭正版系统。"})
    else:
        return jsonify({"success": False, "message": "激活码错误，该激活码与您的手机设备不匹配！"})

# 🛠️ 网页端站长算号后台接口
@app.route('/api/admin/keygen', methods=['POST'])
def admin_keygen():
    data = request.json
    device_id = data.get('deviceId', '').strip()
    admin_pwd = data.get('password', '').strip()
    
    if admin_pwd != "8888":
        return jsonify({"success": False, "message": "站长管理密码错误！"})
    
    if not device_id:
        return jsonify({"success": False, "message": "请输入客户的设备特征码！"})
        
    raw_data = device_id + SECRET_SALT
    full_hash = hashlib.sha256(raw_data.encode('utf-8')).hexdigest().upper()
    license_code = f"LJ-{full_hash[0:4]}-{full_hash[4:8]}-{full_hash[8:12]}-{full_hash[12:16]}"
    
    return jsonify({"success": True, "license": license_code})

@app.route('/api/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    if file:
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        return jsonify({"success": True, "filename": file.filename})
    return jsonify({"success": False})

@app.route('/api/parse', methods=['POST'])
def parse():
    data = request.json
    script = data.get('script', '')
    clips = data.get('clips', [])
    
    lines = [l.strip() for l in script.split('\n') if l.strip()]
    if not lines:
        lines = [f"剧情镜头 {i+1}" for i in range(max(len(clips), 1))]

    total_clips = len(clips)
    total_lines = len(lines)

    matched_clips = []
    for i in range(total_lines):
        if total_clips > 0:
            chosen_clip = clips[i % total_clips]
            matched_clips.append(chosen_clip)
        else:
            matched_clips.append("placeholder.mp4")

    episodes = [{
        "episode_id": 1,
        "title": f"灵境光梭自适应大片（共 {total_lines} 个镜头无缝对齐）",
        "scenes": lines,
        "clips": matched_clips
    }]

    return jsonify({"success": True, "episodes": episodes})

@app.route('/api/stitch', methods=['POST'])
def stitch():
    data = request.json
    episodes = data.get('episodes', [])
    results = []
    try:
        for ep in episodes:
            eid = ep['episode_id']
            clips = ep['clips']
            out_name = f"lingjing_master_movie.mp4"
            out_path = os.path.join(OUTPUT_FOLDER, out_name)
            list_path = os.path.join(UPLOAD_FOLDER, f"list_lingjing.txt")

            with open(list_path, 'w', encoding='utf-8') as f:
                for c in clips:
                    cp = os.path.abspath(os.path.join(UPLOAD_FOLDER, c))
                    f.write(f"file '{cp}'\n")

            cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', list_path, '-c', 'copy', out_path]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode != 0:
                cmd_fb = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', list_path, '-c:v', 'libx264', '-crf', '23', '-c:a', 'aac', out_path]
                subprocess.run(cmd_fb, check=True)

            results.append({"name": "灵境光梭完美正片", "url": f"/outputs/{out_name}"})
        return jsonify({"success": True, "results": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/outputs/<name>')
def get_out(name):
    return send_from_directory(OUTPUT_FOLDER, name, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
