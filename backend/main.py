# main.py - النسخة المعدلة مع إصلاح البحث عن الطالب
import os
import sys
import traceback
from contextlib import asynccontextmanager
from typing import List, Optional, Dict

import pandas as pd
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# -------------------------------
# ====== 1. Configuration ======
# -------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 🔥 إيجاد المسار الصحيح للبيانات
possible_paths = [
    os.path.join(BASE_DIR, "..", "data"),      # ../data (من backend)
    os.path.join(BASE_DIR, "data"),            # ./data (من نفس المجلد)
    os.path.join(BASE_DIR, "..", "..", "data"), # ../../data
    os.path.abspath("data")                    # المسار المطلق
]

DATA_PATH = None
for path in possible_paths:
    test_file = os.path.join(path, "courses.csv")
    if os.path.exists(test_file):
        DATA_PATH = path
        print(f"✅ Found data folder at: {path}")
        break

if DATA_PATH is None:
    print("⚠️ Could not find data folder automatically, using default path")
    DATA_PATH = os.path.join(BASE_DIR, "..", "data")
    print(f"⚠️ Using default path: {DATA_PATH}")

TOP_K = 7

# Global DataFrames
courses_df: Optional[pd.DataFrame] = None
students_df: Optional[pd.DataFrame] = None
enrollments_df: Optional[pd.DataFrame] = None
academic_df: Optional[pd.DataFrame] = None

# Mappings
code_to_id_map: Dict[str, str] = {}

# -------------------------------
# ====== 2. Smart Fix Logic ======
# -------------------------------
def smart_fix_courses_df(df: pd.DataFrame) -> pd.DataFrame:
    """إصلاح ذكي لمشاكل ملف courses.csv"""
    if df.empty:
        return df
    
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()

    if 'location' in df.columns and 'instructor' in df.columns:
        split_mask = df['location'].str.startswith("N'") & df['instructor'].str.endswith("'")
        
        if split_mask.any():
            print(f"⚠️ Fixing Split Locations for {split_mask.sum()} courses...")
            
            df.loc[split_mask, 'location'] = df.loc[split_mask, 'location'] + "," + df.loc[split_mask, 'instructor']
            df['location'] = df['location'].str.replace(r"^N'", "", regex=True).str.replace(r"'$", "", regex=True)
            df.loc[split_mask, 'instructor'] = df.loc[split_mask, 'semester_offered']
            
            if 'course_description' in df.columns:
                df.loc[split_mask, 'semester_offered'] = df.loc[split_mask, 'course_description']

    is_numeric_name = pd.to_numeric(df['course_name'], errors='coerce').notna().sum()
    total_rows = len(df)
    
    if total_rows > 0 and (is_numeric_name / total_rows) > 0.5:
        print("⚠️ Fixing Column Shift & Regenerating IDs...")
        
        df['credits'] = df['course_name']
        df['course_name'] = df['course_code']
        df['course_code'] = df['course_id']
        df['course_id'] = range(1, len(df) + 1)
        df['course_id'] = df['course_id'].astype(str)

    return df

# -------------------------------
# ====== 3. App Lifecycle ======
# -------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global courses_df, students_df, enrollments_df, academic_df, code_to_id_map

    print("⏳ Loading Data...")
    try:
        print(f"📁 Data path: {DATA_PATH}")
        
        # تحقق من وجود الملفات أولاً
        required_files = ["courses.csv", "students.csv", "enrollments.csv"]
        for file in required_files:
            file_path = os.path.join(DATA_PATH, file)
            if os.path.exists(file_path):
                print(f"✅ Found: {file}")
            else:
                print(f"❌ Missing: {file} at {file_path}")
        
        # تحميل البيانات
        courses_df = pd.read_csv(os.path.join(DATA_PATH, "courses.csv"), dtype=str, skipinitialspace=True).fillna("")
        students_df = pd.read_csv(os.path.join(DATA_PATH, "students.csv"), dtype=str, skipinitialspace=True).fillna("")
        enrollments_df = pd.read_csv(os.path.join(DATA_PATH, "enrollments.csv"), dtype=str, skipinitialspace=True).fillna("")
        
        ac_path = os.path.join(DATA_PATH, "academic_records.csv")
        if os.path.exists(ac_path):
            academic_df = pd.read_csv(ac_path, dtype=str, skipinitialspace=True).fillna("")
        else:
            academic_df = pd.DataFrame()
            print("⚠️ academic_records.csv not found, using empty dataframe")

        courses_df = smart_fix_courses_df(courses_df)

        for df in [students_df, enrollments_df, academic_df]:
            if not df.empty:
                for col in ["student_id", "course_id", "course_code"]:
                    if col in df.columns:
                        df[col] = df[col].astype(str).str.strip()

        if not courses_df.empty:
             if "location" in courses_df.columns:
                 courses_df["location"] = courses_df["location"].str.replace(r"^N'", "", regex=True).str.replace(r"'$", "", regex=True)
             if "instructor" in courses_df.columns:
                 courses_df["instructor"] = courses_df["instructor"].str.replace("N'", "").str.replace("'", "")

        code_to_id_map = dict(zip(courses_df["course_code"], courses_df["course_id"]))
        print(f"✅ System Ready. Loaded {len(courses_df)} courses, {len(students_df)} students")

    except Exception as e:
        print(f"❌ Error loading data: {e}")
        print(f"📁 Current directory: {os.getcwd()}")
        print(f"📁 Script location: {BASE_DIR}")
        print(f"📁 Data path attempted: {DATA_PATH}")
        traceback.print_exc()
        sys.exit(1)

    yield

# إنشاء التطبيق
app = FastAPI(title="Course Recommender", lifespan=lifespan)

# إضافة CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# ====== 4. Models & Logic ======
# -------------------------------
class RecommendationRequest(BaseModel):
    student_id: str

class CourseRecommendation(BaseModel):
    course_id: str
    course_code: str
    course_name: str
    score: float
    reason: str
    type: str
    location: str
    instructor: str

def get_completed_course_ids(student_id: str) -> List[str]:
    completed = set()
    if not academic_df.empty:
        recs = academic_df[academic_df["student_id"] == student_id]
        passed = recs[~recs["grade"].str.upper().eq("F")]
        completed.update(passed["course_id"].tolist())

    if not enrollments_df.empty:
        enr = enrollments_df[enrollments_df["student_id"] == student_id]
        status_col = "enrollment_status" if "enrollment_status" in enr.columns else "status"
        if status_col in enr.columns:
            valid = enr[
                (enr[status_col].str.lower() == "completed") & 
                (~enr.get("final_grade", "").str.upper().eq("F"))
            ]
            completed.update(valid["course_id"].tolist())
    return list(completed)

def check_prerequisites(course_row: dict, completed_ids: List[str]):
    prereq_str = course_row.get("prerequisites", "")
    if not prereq_str or prereq_str.lower() in ["nan", "none", ""]:
        return True, "No prerequisites"

    req_codes = [p.strip() for p in prereq_str.replace(";", ",").split(",") if p.strip()]
    missing = []
    for code in req_codes:
        req_id = code_to_id_map.get(code)
        if req_id and req_id not in completed_ids:
            missing.append(code)
    
    if missing:
        return False, f"Missing: {', '.join(missing)}"
    return True, "Prerequisites met"

def calculate_priority_score(course_row, student_sem, student_gpa, completed_ids):
    score = 10.0
    reasons = []

    try:
        c_sem = int(course_row.get("semester_offered", 99))
    except:
        c_sem = 99
    
    try:
        credits = float(course_row.get("credits", 3))
    except:
        credits = 3.0
    
    c_type = str(course_row.get("course_type", "elective")).lower()

    if c_sem < student_sem:
        score += 20.0
        reasons.append("Backlog/Previous Semester")
    elif c_sem == student_sem:
        score += 10.0
        reasons.append("Current Semester Path")
    elif c_sem == student_sem + 1:
        score += 5.0
        reasons.append("Next Semester Headstart")
    else:
        score -= 5.0 
    
    if "core" in c_type:
        score += 5.0
        reasons.append("Core Course")
    
    if student_gpa > 0 and student_gpa < 2.0:
        if credits > 3:
            score -= 3.0
            reasons.append("High Load (GPA Risk)")
        else:
            score += 2.0
            reasons.append("GPA Recovery")
            
    score += np.random.uniform(0, 0.1)
    return score, ", ".join(reasons)

@app.post("/recommend", response_model=List[CourseRecommendation])
async def recommend(req: RecommendationRequest):
    sid = str(req.student_id).strip()
    completed_ids = get_completed_course_ids(sid)
    
    # 🔧 البحث الذكي عن الطالب في أعمدة متعددة
    s_row = None
    
    # 1. أولاً جرب البحث بـ university_id (الذي من run.py)
    if "university_id" in students_df.columns:
        students_df["university_id"] = students_df["university_id"].astype(str).str.strip()
        s_row = students_df[students_df["university_id"] == sid]
        if not s_row.empty:
            print(f"✅ Found student by university_id: {sid}")
    
    # 2. إذا لم يجد، جرب بـ student_id
    if (s_row is None or s_row.empty) and "student_id" in students_df.columns:
        students_df["student_id"] = students_df["student_id"].astype(str).str.strip()
        s_row = students_df[students_df["student_id"] == sid]
        if not s_row.empty:
            print(f"✅ Found student by student_id: {sid}")
    
    # 3. إذا لم يجد أبداً
    if s_row is None or s_row.empty:
        print(f"⚠️ Student {sid} not found in students.csv, using defaults")
        s_sem = 1
        s_gpa = 0.0
    else:
        try:
            s_sem = int(s_row.iloc[0]["semester"])
            s_gpa = float(s_row.iloc[0]["current_gpa"])
            student_name = s_row.iloc[0].get("student_name", "Unknown")
            print(f"👤 Student: {student_name}, Semester: {s_sem}, GPA: {s_gpa}")
        except:
            s_sem = 1
            s_gpa = 0.0

    print(f"📥 Req: Student {sid} | Sem {s_sem}")
    
    recommendations = []
    for _, row in courses_df.iterrows():
        c_id = row["course_id"]
        if c_id in completed_ids: continue
        if str(row.get("is_active", "1")) == "0": continue

        allowed, prereq_msg = check_prerequisites(row.to_dict(), completed_ids)
        if not allowed: continue

        score, reason_detail = calculate_priority_score(row, s_sem, s_gpa, completed_ids)
        final_reason = f"{prereq_msg}"
        if reason_detail: final_reason += f" | {reason_detail}"

        recommendations.append(CourseRecommendation(
            course_id=c_id,
            course_code=row["course_code"],
            course_name=row["course_name"],
            score=round(score, 2),
            reason=final_reason,
            type="academic_path",
            location=str(row.get("location", "TBA")),
            instructor=str(row.get("instructor", "TBA"))
        ))

    recommendations.sort(key=lambda x: x.score, reverse=True)
    return recommendations[:TOP_K]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)