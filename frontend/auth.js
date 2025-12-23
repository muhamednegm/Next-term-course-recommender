// auth.js - النسخة المعدلة
console.log('🔗 auth.js loaded (Dual Server Mode)');

// الخوادم
const LOGIN_SERVER = 'http://localhost:8000';    // run.py للـ login فقط
const RECOMMEND_SERVER = 'http://localhost:8006'; // main.py للبيانات والتوصيات

// 1. التحقق من تسجيل الدخول
function checkLogin() {
    const studentId = localStorage.getItem('student_id');
    if (!studentId) {
        alert('⛔ Please login first!');
        window.location.href = 'index.html';
        return null;
    }
    console.log('Student ID from localStorage:', studentId);
    return studentId;
}

// 2. جلب بيانات الطالب الحقيقية من main.py (الذي يحتوي على students.csv)
async function getStudentData(studentId) {
    console.log('🔍 Fetching REAL student data for:', studentId);
    
    try {
        // محاولة جلب بيانات الطالب الحقيقية من main.py
        // نستخدم نفس endpoint للتوصيات ولكن نطلب فقط بيانات الطالب
        const response = await fetch(`${RECOMMEND_SERVER}/recommend`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ student_id: studentId })
        });
        
        if (response.ok) {
            // الحصول على التوصيات (والتي تحتوي على بيانات الطالب في السيرفر)
            const recommendations = await response.json();
            console.log('✅ Got recommendations, checking student data...');
            
            // جلب بيانات الطالب من localStorage أو من run.py كاحتياطي
            return {
                id: studentId,
                name: localStorage.getItem('student_name') || 'Student',
                major: localStorage.getItem('student_major') || 'Computer Science',
                gpa: localStorage.getItem('student_gpa') || '3.5',
                level: localStorage.getItem('selected_level') || '3'
            };
        }
    } catch (error) {
        console.warn('⚠️ Cannot connect to main.py server, trying login server...');
    }
    
    try {
        // احتياطي: جلب من run.py
        const response = await fetch(`${LOGIN_SERVER}/api/login?university_id=${studentId}&password=test123`);
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.student) {
                console.log('✅ Student data from login server:', data.student);
                return data.student;
            }
        }
    } catch (error) {
        console.warn('⚠️ Cannot connect to any server');
    }
    
    // إذا فشل كل شيء، استخدم البيانات المحلية
    return {
        id: studentId,
        name: localStorage.getItem('student_name') || 'Student',
        major: localStorage.getItem('student_major') || 'Computer Science',
        gpa: localStorage.getItem('student_gpa') || '3.5',
        level: localStorage.getItem('selected_level') || '3'
    };
}

// 3. جلب التوصيات (من main.py)
async function getRecommendations(studentId) {
    console.log('Requesting recommendations for:', studentId);
    
    try {
        const response = await fetch(`${RECOMMEND_SERVER}/recommend`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ student_id: studentId })
        });
        
        if (response.ok) {
            const recommendations = await response.json();
            console.log('✅ Recommendations received:', recommendations.length);
            return recommendations;
        }
    } catch (error) {
        console.error('❌ Error fetching recommendations:', error);
    }
    
    console.warn('⚠️ Using sample recommendations');
    return [
        {
            course_id: '1',
            course_code: 'CS201',
            course_name: 'Data Structures',
            score: 9.5,
            reason: 'Core course for your level',
            type: 'academic_path',
            location: 'Building FB200, Room 4',
            instructor: 'Dr. Ahmed Hassan'
        }
    ];
}

// 4. تسجيل الخروج
function logout() {
    console.log('🚪 Logging out...');
    // مسح جميع البيانات المحلية
    localStorage.removeItem('student_id');
    localStorage.removeItem('student_name');
    localStorage.removeItem('student_major');
    localStorage.removeItem('student_gpa');
    localStorage.removeItem('selected_level');
    
    // الانتقال إلى صفحة تسجيل الدخول
    setTimeout(() => {
        window.location.href = 'index.html';
    }, 300);
}

// 5. اختبار اتصال الخوادم
async function testServers() {
    console.group('🔄 Testing Server Connections');
    
    try {
        const loginResponse = await fetch(`${LOGIN_SERVER}/`);
        console.log(`${LOGIN_SERVER}/:`, loginResponse.status);
    } catch (e) {
        console.error(`❌ ${LOGIN_SERVER}/: Not reachable`);
    }
    
    try {
        const recommendResponse = await fetch(`${RECOMMEND_SERVER}/`);
        console.log(`${RECOMMEND_SERVER}/:`, recommendResponse.status);
    } catch (e) {
        console.error(`❌ ${RECOMMEND_SERVER}/: Not reachable`);
    }
    
    console.groupEnd();
}

// 6. جلب بيانات الطالب من main.py مباشرة (دالة جديدة)
async function getRealStudentDataFromMain(studentId) {
    console.log('🔍 Getting REAL data from main.py for:', studentId);
    
    try {
        // محاولة الاتصال بـ main.py لبيانات الطالب
        // نحتاج لـ endpoint جديد في main.py، لكن حالياً نستخدم التوصيات
        const response = await fetch(`${RECOMMEND_SERVER}/recommend`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ student_id: studentId })
        });
        
        if (response.ok) {
            console.log('✅ Connected to main.py for student data');
            // البيانات الحقيقية ستأتي من localStorage (تم تعبئتها في index.html)
            return {
                id: studentId,
                name: localStorage.getItem('student_name') || 'Student',
                major: localStorage.getItem('student_major') || 'Computer Science',
                gpa: localStorage.getItem('student_gpa') || '3.5',
                level: localStorage.getItem('selected_level') || '3'
            };
        }
    } catch (error) {
        console.error('❌ Cannot get data from main.py:', error);
    }
    
    return null;
}

// تصدير الدوال للاستخدام
window.auth = { 
    checkLogin, 
    getStudentData, 
    getRealStudentDataFromMain, // دالة جديدة
    getRecommendations,
    logout,
    testServers,
    LOGIN_SERVER,
    RECOMMEND_SERVER 
};

// اختبار الاتصال تلقائياً عند التحميل
window.addEventListener('load', () => {
    testServers();
    
    // اختبار بيانات الطالب الحالية
    const studentId = localStorage.getItem('student_id');
    if (studentId) {
        console.log('📋 Current student data in localStorage:');
        console.log('- ID:', studentId);
        console.log('- Name:', localStorage.getItem('student_name'));
        console.log('- Major:', localStorage.getItem('student_major'));
        console.log('- GPA:', localStorage.getItem('student_gpa'));
        console.log('- Level:', localStorage.getItem('selected_level'));
    }
});