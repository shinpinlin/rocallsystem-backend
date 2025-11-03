import os
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS
from time import sleep

app = Flask(__name__)

# 取得資料庫連線字串
DATABASE_URL = os.environ.get('DATABASE_URL')

# 允許您的前端 (new-5j38.onrender.com) 跨網域連線
# !!! 確保 "new-5j38" 是您前端服務的正確名稱 !!!
CORS(app, resources={r"/api/*": {"origins": "https://new-5j38.onrender.com"}})

# --- 建立資料表的函數 ---
def create_table():
    conn = None
    try:
        print("Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # 建立 'logins' 資料表 (如果它不存在的話)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS logins (
            id SERIAL PRIMARY KEY,
            student_id VARCHAR(50) NOT NULL,
            student_name VARCHAR(100) NOT NULL,
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()
        print("Table 'logins' checked/created successfully.")
        
        cur.close()
        conn.close()
    
    except Exception as e:
        print(f"Database table creation failed: {e}")
        # 如果連線失敗，稍後重試
        if conn:
            conn.close()
        sleep(5) # 等待 5 秒
        create_table() # 遞迴重試 (Render 啟動時可能資料庫還沒準備好)

# --- 啟動時先執行建立資料表的函數 ---
create_table()


# 測試 API 是否運作
@app.route('/')
def home():
    return "後端 API 運作中！"

# 處理登入請求的 API
@app.route('/api/login', methods=['POST'])
def handle_login():
    data = request.get_json()
    student_id = data.get('studentId')
    student_name = data.get('studentName')

    if not student_id or not student_name:
        return jsonify({"error": "學號和姓名不能為空"}), 400

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        cur.execute(
            "INSERT INTO logins (student_id, student_name) VALUES (%s, %s)",
            (student_id, student_name)
        )
        conn.commit()
        
        cur.close()
        conn.close()
        
        return jsonify({
            "id": student_id,
            "name": student_name,
            "message": "登入資料已記錄"
        })

    except Exception as e:
        print(f"Database error during login: {e}")
        return jsonify({"error": "伺服器內部錯誤"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)