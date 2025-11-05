import os
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from time import sleep

app = Flask(__name__)

# --- 🎯 您的固定名單 (MASTER ROSTER) ---
MASTER_ROSTER = {
    '1143042': '林訓平',  # 範例學生 A
    '1143043': '范姜群傑', # 範例學生 B
    # 請您在您的本地 app.py 中新增所有學生的學號和姓名
}


# 取得資料庫連線字串
DATABASE_URL = os.environ.get('DATABASE_URL')

# 允許您的前端 (https://new-5j38.onrender.com) 跨網域連線
CORS(app, resources={r"/api/*": {"origins": "https://new-5j38.onrender.com"}})

# --- 建立資料表的函數 ---
def create_table():
    # 保持不變
    # ... (您的 create_table 函數程式碼) ...

# --- 啟動時先執行建立資料表的函數 ---
# create_table() # 為了保持程式碼簡潔，我們假設這行您保留了

# 測試 API 是否運作
@app.route('/')
def home():
    return "後端 API 運作中 (Final Roster Check)！"

# --- 「登入」 API (修正邏輯) ---
@app.route('/api/login', methods=['POST'])
def handle_login():
    data = request.get_json()
    student_id = data.get('studentId')
    student_name = data.get('studentName')
    current_time = datetime.now()

    if not student_id or not student_name:
        return jsonify({"error": "學號和姓名不能為空"}), 400

    # *** 🚀 關鍵修正：在後端執行名單驗證 ***
    if student_id not in MASTER_ROSTER or MASTER_ROSTER[student_id] != student_name:
        # 如果學號不在名冊中，或者學號與姓名不匹配，則拒絕登入
        return jsonify({"error": "學號或姓名不符，請確認您的資料。"}), 401

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # 執行資料庫 UPSERT 操作 (保持不變)
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
        
        student_data = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
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

# ... (其餘 API 保持不變) ...