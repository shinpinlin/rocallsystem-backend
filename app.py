import os
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

# 取得資料庫連線字串 (我們等一下會在 Render 上設定)
DATABASE_URL = os.environ.get('DATABASE_URL')

# 允許您的前端 (new-5j38.onrender.com) 跨網域連線
# !!! 請注意，您前端的網址 "new-5j38" 可能會變，如果變了要回來修改這裡 !!!
CORS(app, resources={r"/api/*": {"origins": "https://new-5j38.onrender.com"}})

# 測試 API 是否運作
@app.route('/')
def home():
    return "後端 API 運作中！"

# 處理登入請求的 API
@app.route('/api/login', methods=['POST'])
def handle_login():
    data = request.get_json() # 取得前端送來的 JSON 資料
    student_id = data.get('studentId')
    student_name = data.get('studentName')

    if not student_id or not student_name:
        return jsonify({"error": "學號和姓名不能為空"}), 400

    try:
        # 連線到 PostgreSQL 資料庫
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # 將資料寫入 'logins' 資料表 (我們稍後會建立)
        cur.execute(
            "INSERT INTO logins (student_id, student_name) VALUES (%s, %s)",
            (student_id, student_name)
        )
        conn.commit()
        
        cur.close()
        conn.close()
        
        # 為了模擬登入成功，我們直接回傳學生資料
        return jsonify({
            "id": student_id,
            "name": student_name,
            "message": "登入資料已記錄"
        })

    except Exception as e:
        print(f"資料庫錯誤: {e}")
        return jsonify({"error": "伺服器內部錯誤"}), 500

if __name__ == '__main__':
    # Render 會自動指定 PORT
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)