import os
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timezone, timedelta

TST = timezone(timedelta(hours=8))  # 台灣時區

app = Flask(__name__)

MASTER_ROSTER = {
    '1123003': '謝昀臻', 
    '1123025': '陳靖',
    '1123047': '吳昀軒',
    '1123065': '吳玟璇',
    '1123066': '黃建岷',
    '1123090': '歐陽佑昌',
    '1123098': '簡聖修',
    '1123113': '林彥君',
    '1133080': '蘇筠媗',
    '1133081': '廖曉慧',
    '1133082': '黃子銘',
    '1133084': '張仕學',
    '1133085': '黃奕誠',
    '1133086': '林冠宏',
    '1133091': '曾映竹',
    '1133092': '陳俊宇',
    '1133093': '劉兆軒',
    '1133094': '黃威程',
    '1133095': '李潛昕',
    '1133101': '薩滿',
    '1133102': '張昕程',
    '1133103': '王瑞亞',
    '1133104': '毛仁笛',
    '1133105': '雷漢森',
    '1133106': '哈志豪',
    '1133107': '凃明',
    '1133108': '高以理',
    '1133001': '陳儒頡',
    '1133002': '邱浴鈞',
    '1133003': '張羨茿',
    '1133013': '許淞棓',
    '1133014': '張晴媗',
    '1133026': '安祐萱',
    '1133027': '潘玟菱',
    '1133032': '施韋吉',
    '1133033': '葉冠愷',
    '1133035': '李柏諠',
    '1133036': '翁達翰',
    '1133037': '高爾義',
    '1133038': '高睿宏',
    '1133044': '吳育鑫',
    '1133048': '鄭偉民',
    '1133057': '李旻晃',
    '1133058': '潘啟文',
    '1133064': '林書瑋',
    '1133065': '林子琦',
    '1133068': '曾資淵',
    '1133069': '黃宇賢',
    '1133071': '林士欽',
    '1133072': '張家瑋',
    '1133073': '陳志豪',
    '1143001': '楊梓邑',
    '1143002': '楊仁瑋',
    '1143003': '黃映潔',
    '1143021': '張雅珺',
    '1143022': '曹孝弘',
    '1143023': '呂欣澤',
    '1143035': '李思賢',
    '1143036': '張家銓',
    '1143037': '陳嘉瑜',
    '1143042': '林訓平',
    '1143043': '范姜群傑',
    '1143044': '陳梅齡',
    '1143045': '劉宇傑',
    '1143046': '黃冠博',
    '1143048': '張育梓',
    '1143049': '林文澤',
    '1143050': '唐晏鐸',
    '1143051': '柯宜欣',
    '1143055': '陳毅言',
    '1143056': '鄭睦羽',
    '1143057': '彭軒',
    '1143063': '李柏亨',
    '1143064': '歐宜勛',
    '1143065': '林冠甫',
    '1143066': '楊子嫻',
    '1143077': '蔡承恩',
    '1143078': '廖右安',
    '1143085': '王冠中',
    '1143089': '朱婉容',
    '1143090': '張郁閔',
    '1143091': '廖正豪',
    '1143096': '洪德諭',
    '1143097': '王寅兒',
    '1143098': '林品瑜',
    '1143102': '黃端陽',
    '1143103': '朱曜東',
    '1143104': '魏茂屹',
    '1143114': '謝豐安',
    '1143115': '吳東翰',
    '1143119': '張雅筑',
    '1143125': '卜謙學',
    '1143126': '利輝煌',
    '1143127': '涂俊偉',
    '1143128': '李童發',
    '1143129': '洪明翰',
    '1143130': '羅文傑',
    '1143131': '吳曉天',
    '1143132': '楊佳玲',
    '1143133': '李珮安',
}
DATABASE_URL = os.environ.get('DATABASE_URL')

CORS(app, resources={r"/api/v1/*": {
    "origins": [
        "https://new-5j38.onrender.com",
        "http://localhost:3000",
        "http://localhost:4200"
    ],
    "supports_credentials": True
}})

def create_table():
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
                status VARCHAR(50) NOT NULL DEFAULT '未簽到',
                leave_type VARCHAR(50) NULL,
                leave_remarks TEXT NULL,
                last_updated_at TIMESTAMPTZ
            );
        """)
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"Database table creation check failed: {e}")
    finally:
        if conn and not conn.closed:
            conn.close()

create_table()

@app.route('/')
def home():
    return jsonify({"message": "點名系統後端服務正在運行"})

@app.route('/api/v1/login', methods=['POST'])
def handle_login():
    data = request.get_json()
    student_id = data.get('studentId')
    current_time = datetime.now(TST)
    if not student_id or student_id not in MASTER_ROSTER:
        return jsonify({"error": {"error": "errors.studentIdNotFound"}}), 404

    student_name = MASTER_ROSTER[student_id]
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        cur.execute("SELECT status, leave_type, leave_remarks, last_updated_at FROM students WHERE id = %s;", (student_id,))
        record = cur.fetchone()

        is_current_status_leave = record and record[0] == '請假'

        if record:
            status, leave_type, leave_remarks, last_updated_at = record

            # 每次登入即時刷新時間
            cur.execute("UPDATE students SET last_updated_at = %s WHERE id = %s;", (current_time, student_id))
            conn.commit()

            if not is_current_status_leave:
                cur.execute(
                    "UPDATE students SET status = '出席', last_updated_at = %s, leave_type = NULL, leave_remarks = NULL WHERE id = %s;",
                    (current_time, student_id)
                )
                conn.commit()
                status = '出席'
                leave_type = None
                leave_remarks = None

            leave_type = leave_type if leave_type else None
            leave_remarks = leave_remarks if leave_remarks else None

            return jsonify({
                "id": student_id,
                "name": student_name,
                "status": status,
                "leaveType": leave_type,
                "leaveRemarks": leave_remarks,
                "lastUpdatedAt": current_time.isoformat()
            })

        else:
            cur.execute(
                """
                INSERT INTO students (id, name, status, last_updated_at)
                VALUES (%s, %s, '出席', %s);
                """,
                (student_id, student_name, current_time)
            )
            conn.commit()
            return jsonify({
                "id": student_id,
                "name": student_name,
                "status": '出席',
                "leaveType": None,
                "leaveRemarks": None,
                "lastUpdatedAt": current_time.isoformat()
            })

    except Exception as e:
        print(f"Database error during login: {e}")
        return jsonify({"error": {"error": "errors.loginFailed"}}), 500
    finally:
        if conn and not conn.closed:
            conn.close()

@app.route('/api/v1/students', methods=['GET'])
def get_all_students():
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        cur.execute("SELECT id, name, status, leave_type, leave_remarks, last_updated_at FROM students;")
        all_students_data = cur.fetchall()
        cur.close()

        students_list = []
        for student_data in all_students_data:
            last_updated_at_str = student_data[5].isoformat() if student_data[5] else None
            students_list.append({
                "id": student_data[0],
                "name": student_data[1],
                "status": student_data[2],
                "leaveType": student_data[3],
                "leaveRemarks": student_data[4],
                "lastUpdatedAt": last_updated_at_str
            })
        return jsonify(students_list)

    except Exception as e:
        print(f"Database error during get_all_students: {e}")
        return jsonify({"error": "伺服器內部錯誤"}), 500
    finally:
        if conn and not conn.closed:
            conn.close()

@app.route('/api/v1/leave', methods=['POST'])
def handle_leave_application():
    data = request.get_json()
    student_id = data.get('studentId')
    leave_type = data.get('leaveType')
    remarks = data.get('remarks')
    current_time = datetime.now(TST)

    if not student_id or not leave_type:
        return jsonify({"error": {"error": "errors.emptyFields"}}), 400

    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

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

        if cur.rowcount == 0:
            if student_id in MASTER_ROSTER:
                student_name = MASTER_ROSTER[student_id]
                cur.execute(
                    """
                    INSERT INTO students (id, name, status, leave_type, leave_remarks, last_updated_at)
                    VALUES (%s, %s, '請假', %s, %s, %s);
                    """,
                    (student_id, student_name, leave_type, remarks, current_time)
                )
            else:
                conn.rollback()
                return jsonify({"error": {"error": "errors.studentIdNotFound"}}), 404

        conn.commit()
        cur.close()

        return jsonify({"message": "請假申請已提交"})

    except Exception as e:
        print(f"Database error during leave_application: {e}")
        return jsonify({"error": {"error": "errors.leaveFailed"}}), 500
    finally:
        if conn and not conn.closed:
            conn.close()

@app.route('/api/v1/students/<string:student_id>', methods=['DELETE'])
def handle_delete_student(student_id):
    if not student_id:
        return jsonify({"error": "缺少學生ID"}), 400

    conn = None
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

@app.route('/api/v1/admin/reset', methods=['POST'])
def handle_admin_reset():
    data = request.get_json()
    password_attempt = data.get('password')
    ADMIN_PASSWORD_VALUE = os.environ.get('ADMIN_RESET_PASSWORD')

    if not ADMIN_PASSWORD_VALUE:
        print("錯誤：ADMIN_RESET_PASSWORD 環境變數未設定，重置被拒絕。")
        return jsonify({"error": {"error": "errors.resetFailed"}}), 500

    if password_attempt != ADMIN_PASSWORD_VALUE:
        return jsonify({"error": {"error": "errors.passwordIncorrect"}}), 403

    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        current_time = datetime.now(TST)
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