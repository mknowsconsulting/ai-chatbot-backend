"""
Mock Student Data Service
For testing without actual LMS database connection
"""

from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class MockStudentDataService:
    """Mock student data for testing"""
    
    # Mock data
    MOCK_STUDENTS = {
        "12345": {
            "id": 1,
            "nim": "12345",
            "full_name": "Budi Santoso",
            "jurusan": "Teknik Informatika",
            "angkatan": 2022,
            "semester": 3,
            "email": "budi@student.kampusgratis.com",
            "phone": "081234567890",
            "status": "active"
        },
        "67890": {
            "id": 2,
            "nim": "67890",
            "full_name": "Siti Aminah",
            "jurusan": "Sistem Informasi",
            "angkatan": 2023,
            "semester": 1,
            "email": "siti@student.kampusgratis.com",
            "phone": "081234567891",
            "status": "active"
        }
    }
    
    MOCK_GRADES = {
        "12345": [
            {"mata_kuliah": "Algoritma", "semester": 3, "sks": 3, "nilai_angka": 85, "nilai_huruf": "A", "kategori": "UTS"},
            {"mata_kuliah": "Database", "semester": 3, "sks": 3, "nilai_angka": 78, "nilai_huruf": "B+", "kategori": "UTS"},
            {"mata_kuliah": "Kalkulus", "semester": 3, "sks": 4, "nilai_angka": 90, "nilai_huruf": "A", "kategori": "UTS"},
        ]
    }
    
    MOCK_SCHEDULES = {
        "12345": [
            {"mata_kuliah": "Algoritma", "hari": "Senin", "jam_mulai": "08:00", "jam_selesai": "10:00", "ruang": "Lab 1", "dosen": "Dr. Ahmad"},
            {"mata_kuliah": "Database", "hari": "Rabu", "jam_mulai": "10:00", "jam_selesai": "12:00", "ruang": "Lab 2", "dosen": "Dr. Siti"},
            {"mata_kuliah": "Kalkulus", "hari": "Jumat", "jam_mulai": "08:00", "jam_selesai": "10:00", "ruang": "Kelas A", "dosen": "Prof. Budi"},
        ]
    }
    
    def get_student_by_nim(self, nim: str) -> Optional[Dict[str, Any]]:
        return self.MOCK_STUDENTS.get(nim)
    
    def get_student_grades(self, nim: str, semester: Optional[int] = None, kategori: Optional[str] = None) -> List[Dict[str, Any]]:
        grades = self.MOCK_GRADES.get(nim, [])
        if semester:
            grades = [g for g in grades if g["semester"] == semester]
        if kategori:
            grades = [g for g in grades if g["kategori"] == kategori]
        return grades
    
    def get_student_gpa(self, nim: str, semester: Optional[int] = None) -> Optional[float]:
        grades = self.get_student_grades(nim, semester)
        if not grades:
            return None
        total = sum(g["nilai_angka"] * g["sks"] for g in grades)
        total_sks = sum(g["sks"] for g in grades)
        return round((total / total_sks) / 25, 2)
    
    def get_student_schedule(self, nim: str, hari: Optional[str] = None) -> List[Dict[str, Any]]:
        schedules = self.MOCK_SCHEDULES.get(nim, [])
        if hari:
            schedules = [s for s in schedules if s["hari"] == hari]
        return schedules
    
    def get_student_assignments(self, nim: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        return []
    
    def get_student_attendance(self, nim: str, mata_kuliah: Optional[str] = None) -> List[Dict[str, Any]]:
        return []
    
    def get_student_summary(self, nim: str) -> Dict[str, Any]:
        profile = self.get_student_by_nim(nim)
        if not profile:
            return {"available": False, "message": f"Student {nim} not found"}
        
        return {
            "available": True,
            "profile": profile,
            "academic": {
                "current_semester": profile["semester"],
                "semester_gpa": self.get_student_gpa(nim, profile["semester"]),
                "overall_gpa": self.get_student_gpa(nim),
                "current_grades": self.get_student_grades(nim, profile["semester"]),
                "schedule": self.get_student_schedule(nim),
                "pending_assignments": []
            }
        }
    
    def format_student_context_for_ai(self, nim: str) -> str:
        summary = self.get_student_summary(nim)
        if not summary.get("available"):
            return "Data tidak tersedia"
        
        profile = summary["profile"]
        academic = summary["academic"]
        
        context = f"""Nama: {profile['full_name']}
NIM: {profile['nim']}
Jurusan: {profile['jurusan']}
Semester: {academic['current_semester']}
IPK: {academic.get('overall_gpa', 'N/A')}

Nilai Semester {academic['current_semester']}:
"""
        for grade in academic.get("current_grades", []):
            context += f"- {grade['mata_kuliah']}: {grade['nilai_angka']} ({grade['nilai_huruf']})\n"
        
        context += "\nJadwal Kuliah:\n"
        for sched in academic.get("schedule", []):
            context += f"- {sched['hari']}: {sched['mata_kuliah']} ({sched['jam_mulai']}-{sched['jam_selesai']}) di {sched['ruang']}\n"
        
        return context
