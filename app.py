import os
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from time import sleep

app = Flask(__name__) # 🚀 修正：app 必須在所有路由之前定義！

# --- 🎯 您的固定名單 (MASTER ROSTER) ---
MASTER_ROSTER = {
    # ... (您的所有學生名單，這部分保持完整不變) ...
}

# 取得資料庫連線字串
DATABASE_URL = os.environ.get('DATABASE_URL')

# 🚀 CORS 配置，允許本地開發地址
CORS(app, resources={r"/api/v1/*": {
    "origins": [
        "https://new-5j38.onrender.com",
        "http://localhost:3000",
        "http://localhost:4200"
    ],
    "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"]
}})

# --- 建立資料表的函數 ---
def create_table():
# ... (create_table 函式內容保持不變) ...
    conn = None
    try:
        if not DATABASE_URL:
             print("錯誤：DATABASE_URL 環境變數未設定，無法連線資料庫。")
             return
             
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
    except Exception as e:
        print(f"Database table creation check failed: {e}")
    finally:
        if conn and not conn.closed:
            conn.close()

# 程式啟動時執行建立資料表檢查
create_table()


# 測試 API 是否運作
@app.route('/')
def home():
    return "後端 API 運作中 (Final Roster Check)！"

# --- 「登入」 API ---
@app.route('/api/v1/login', methods=['POST'])
def handle_login():
# ... (handle_login 函式內容保持不變) ...
    data = request.get_json()
    student_id = data.get('studentId')
    current_time = datetime.now()

    if not student_id:
        return jsonify({"error": {"error": "errors.emptyFields"}}), 400

    if student_id not in MASTER_ROSTER:
        return jsonify({"error": {"error": "errors.studentIdNotFound"}}), 401
    
    student_name = MASTER_ROSTER[student_id]

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

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
        return jsonify({"error": {"error": "errors.loginFailed"}}), 500
    finally:
        if conn and not conn.closed:
            conn.close()

# --- 「取得所有學生」、「請假」、「刪除學生」 API (保持不變) ---

# --- 「刪除學生」 API ---
@app.route('/api/v1/students/<string:student_id>', methods=['DELETE'])
def handle_delete_student(student_id):
# ... (handle_delete_student 函式內容保持不變) ...
    if not student_id:
        return jsonify({"error": "缺少學生ID"}), 400
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        cur.execute("DELETE FROM students WHERE id = %s;", (student_id,))
        
        rowcount = cur.rowcount
        conn.commit()
        cur.close()

        if rowcount == 0:
            return jsonify({"message": "學生不存在，無資料被刪除"}), 404
        else:
            return jsonify({"message": "學生已成功刪除"})

    except Exception as e:
        print(f"Database error during delete_student: {e}")
        return jsonify({"error": "伺服器內部錯誤"}), 500
    finally:
        if conn and not conn.closed:
            conn.close()

# 🚀 這是 Render 錯誤中提到的路由，它必須在 app = Flask() 之後
@app.route('/api/v1/admin/reset', methods=['POST']) 
def handle_admin_reset():
    data = request.get_json()
    password_attempt = data.get('password')
    
    # 1. 從「環境變數」讀取正確的變數名稱 (已修正為 ADMIN_RESET_PASSWORD)
    ADMIN_PASSWORD_VALUE = os.environ.get('ADMIN_RESET_PASSWORD') 

    # 2. 驗證密碼和服務設定
    if not ADMIN_PASSWORD_VALUE: 
        print("錯誤：ADMIN_RESET_PASSWORD 環境變數未設定，重置被拒絕。")
        return jsonify({"error": {"error": "errors.resetFailed"}}), 500
        
    if password_attempt != ADMIN_PASSWORD_VALUE: 
        return jsonify({"error": {"error": "errors.passwordIncorrect"}}), 403 

    # 3. 密碼正確！開始執行資料庫操作
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        current_time = datetime.now()
        
        cur.execute(
            """
            UPDATE students 
            SET status = '出席',
                last_updated_at = %s,
                leave_type = NULL,      
                leave_remarks = NULL    
            """,
            (current_time,)
        )
        
        conn.commit() 
        cur.close()
        
        return jsonify({"message": "成功：已將所有人員狀態重置為「出席」。"})

    except Exception as e:
        if conn:
            conn.rollback() 
        print(f"Database error during admin_reset: {e}")
        return jsonify({"error": {"error": "errors.resetFailed"}}), 500
    finally:
        if conn and not conn.closed:
            conn.close() 

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)