# backend/run.py - النسخة النهائية المعدلة
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import pandas as pd
import bcrypt
import os

app = FastAPI(title="Course Recommender")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================
# 1. تحميل البيانات
# ======================
def load_csv(file_name):
    """تحميل أي ملف CSV"""
    try:
        path = f"../data/{file_name}"
        if not os.path.exists(path):
            return None
        return pd.read_csv(path)
    except:
        return None

# ======================
# 2. التحقق من كلمة المرور
# ======================
def check_password(input_pass, hashed_pass):
    """التحقق من كلمة المرور المشفرة"""
    if not hashed_pass or str(hashed_pass).lower() == 'nan':
        return False
    
    try:
        return bcrypt.checkpw(
            input_pass.encode('utf-8'),
            str(hashed_pass).encode('utf-8')
        )
    except:
        return False

# ======================
# 3. نقاط النهاية
# ======================
@app.get("/")
def home():
    return {
        "message": "✅ Course Recommender API is running",
        "note": "Use university_id and password from user.csv"
    }

@app.get("/api/login")
def login(university_id: str, password: str):
    """تسجيل دخول حقيقي - معدل لأعمدة students.csv"""
    
    # 1. قراءة ملف user.csv
    users_df = load_csv("user.csv")
    if users_df is None:
        return {"success": False, "message": "❌ User database not found"}
    
    # 2. تنظيف البيانات
    users_df['university_id'] = users_df['university_id'].astype(str).str.strip()
    university_id = str(university_id).strip()
    password = str(password).strip()
    
    # 3. البحث عن المستخدم
    user = users_df[users_df['university_id'] == university_id]
    
    if user.empty:
        return {"success": False, "message": "❌ University ID not found"}
    
    user_data = user.iloc[0]
    stored_hash = str(user_data.get('password_hash', ''))
    
    # 4. التحقق من كلمة المرور
    if check_password(password, stored_hash):
        # 5. جلب بيانات الطالب من students.csv
        students_df = load_csv("students.csv")
        student_info = None
        
        if students_df is not None:
            # البحث باستخدام university_id فقط (مطابقة مع user.csv)
            students_df['university_id'] = students_df['university_id'].astype(str).str.strip()
            student = students_df[students_df['university_id'] == university_id]
            
            if not student.empty:
                student_info = student.iloc[0]
        
        if student_info is not None:
            # ✅ استخدام الأعمدة الصحيحة من students.csv
            return {
                "success": True,
                "message": "✅ Login successful",
                "student": {
                    "id": university_id,
                    "name": str(student_info.get('student_name', 'Student')),
                    "major": str(student_info.get('department_id', 'Computer Science')),
                    "level": int(student_info.get('level', 3)),
                    "gpa": float(student_info.get('current_gpa', 3.5))
                },
                "redirect": "Academic.html"
            }
        else:
            return {
                "success": True,
                "message": "✅ Login successful (No academic profile)",
                "student": {
                    "id": university_id,
                    "name": "Student",
                    "major": "Computer Science",
                    "level": 3,
                    "gpa": 3.5
                },
                "redirect": "Academic.html"
            }
    else:
        return {"success": False, "message": "❌ Invalid password"}

@app.get("/api/test-users")
def test_users():
    """عرض بيانات المستخدمين للتجربة"""
    users_df = load_csv("user.csv")
    
    if users_df is None:
        return {"error": "user.csv not found"}
    
    result = []
    for _, row in users_df.iterrows():
        result.append({
            "university_id": row['university_id'],
            "email": row.get('email', ''),
            "password_hash_preview": str(row.get('password_hash', ''))[:50] + "..."
        })
    
    return {
        "total_users": len(users_df),
        "users": result,
        "test_note": "All passwords are 'test123'"
    }

# ======================
# تشغيل السيرفر
# ======================
if __name__ == "__main__":
    print("=" * 70)
    print("🎓 COURSE RECOMMENDER - SIMPLE VERSION")
    print("=" * 70)
    
    # اختبار تحميل الملفات
    test_files = ["user.csv", "students.csv", "courses.csv"]
    for file in test_files:
        df = load_csv(file)
        if df is not None:
            print(f"✅ {file}: {len(df)} records")
        else:
            print(f"⚠️ {file}: Not found")
    
    print("\n🌐 Server: http://localhost:8000")
    print("🔗 Test: http://localhost:8000/api/test-users")
    print("🔑 Test Login: http://localhost:8000/api/login?university_id=CS2024001&password=test123")
    print("=" * 70)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)