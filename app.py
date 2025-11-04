import os
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime # 匯入 datetime 模組

app = Flask(__name__)

# 取得資料庫連線字串
DATABASE_URL = os.environ.get('DATABASE_URL')

# 允許您的前端 (new-5j38.onrender.com) 跨網域連線
CORS(app, resources={r"/api/*": {"origins": "https://new-5j38.onrender.com"}})

# --- 建立資料表的函數 ---
# (這段程式碼保持不變，作為安全檢查)
def create_table():
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            status VARCHAR(20) DEFAULT '出席',
            leave_type VARCHAR(20),
            leave_remarks TEXT,
            last_updated_at TIMESTAMP
        );
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Database table creation check failed: {e}")
        if conn:
            conn.close()

create_table()

# 測試 API 是否運作
@app.route('/')
def home():
    return "後端 API 運作中 (V2)！"

# --- 修正後的「登入」 API ---
# (現在會檢查學生是否存在，並更新狀態)
@app.route('/api/login', methods=['POST'])
def handle_login():
    data = request.get_json()
    student_id = data.get('studentId')
    student_name = data.get('studentName')
    current_time = datetime.now() # 取得目前時間

    if not student_id or not student_name:
        return jsonify({"error": "學號和姓名不能為空"}), 400

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # 檢查學生是否已存在 (UPSERT 語法)
        # 如果學生 (id) 已存在，就更新他的姓名、狀態和時間
        # 如果不存在，就插入新學生
        cur.execute(
            """
            INSERT INTO students (id, name, status, last_updated_at)
            VALUES (%s, %s, '出席', %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                status = '出席',
                leave_type = NULL,
                leave_remarks = NULL,
                last_updated_at = EXCLUDED.last_updated_at
            RETURNING *; 
            """,
            (student_id, student_name, current_time)
        )
        
        # 取得被更新或插入的學生資料
        student_data = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        # 將資料庫回傳的資料格式化
        student = {
            "id": student_data[0],
            "name": student_data[1],
            "status": student_data[2],
            "leaveType": student_data[3],
            "leaveRemarks": student_data[4],
            "lastUpdatedAt": student_data[5]
        }
        
        return jsonify(student)

    except Exception as e:
        print(f"Database error during login: {e}")
        return jsonify({"error": "伺服器內部錯誤"}), 500

# --- 新增的「請假」 API ---
@app.route('/api/leave', methods=['POST'])
def handle_leave():
    data = request.get_json()
    student_id = data.get('studentId')
    leave_type = data.get('leaveType')
    remarks = data.get('remarks')
    current_time = datetime.now()

    if not student_id or not leave_type:
        return jsonify({"error": "學生ID和請假類別不能為空"}), 400

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # 更新指定學生的狀態為「請假」
        cur.execute(
            """
            UPDATE students 
            SET status = '請假', 
                leave_type = %s, 
                leave_remarks = %s, 
                last_updated_at = %s
            WHERE id = %s;
            """,
            (leave_type, remarks, current_time, student_id)
        )
        conn.commit()
        
        cur.close()
        conn.close()
        
        return jsonify({"message": "請假申請已記錄"})

    except Exception as e:
        print(f"Database error during leave: {e}")
        return jsonify({"error": "伺服器內部錯誤"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)