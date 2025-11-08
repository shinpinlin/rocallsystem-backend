# 這是 app.py 中 handle_admin_reset 路由的正確版本

@app.route('/api/v1/admin/reset', methods=['POST'])
def handle_admin_reset():
    data = request.get_json()
    password_attempt = data.get('password')
    
    # 1. 從「環境變數」讀取正確的變數名稱
    ADMIN_PASSWORD_VALUE = os.environ.get('ADMIN_RESET_PASSWORD') 

    # 2. 驗證密碼和服務設定
    if not ADMIN_PASSWORD_VALUE: # 🚀 修正 1: 檢查 ADMIN_PASSWORD_VALUE
        print("錯誤：ADMIN_RESET_PASSWORD 環境變數未設定，重置被拒絕。")
        return jsonify({"error": {"error": "errors.resetFailed"}}), 500
        
    if password_attempt != ADMIN_PASSWORD_VALUE: # 🚀 修正 2: 使用 ADMIN_PASSWORD_VALUE 進行比較
        return jsonify({"error": {"error": "errors.passwordIncorrect"}}), 403 

    # 3. 密碼正確！開始執行資料庫操作
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        current_time = datetime.now()
        
        # 執行狀態重置的關鍵指令 (狀態為 '出席')
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