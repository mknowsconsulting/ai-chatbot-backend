"""
Student Data Service
Query LMS database for student academic information
READ-ONLY access to LMS PostgreSQL database
"""

from typing import Optional, Dict, Any, List
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session
import logging

from app.core.database import lms_db
from app.db.lms_models import Student, Grade, Schedule, Assignment, Attendance

logger = logging.getLogger(__name__)


class StudentDataService:
    """
    Service to fetch student academic data from LMS database
    All queries are READ-ONLY
    """
    
    def __init__(self):
        self.lms = lms_db
    
    def _check_connection(self) -> bool:
        """Check if LMS database is connected"""
        if not self.lms.is_connected():
            logger.warning("LMS Database not connected")
            return False
        return True
    
    def get_student_by_nim(self, nim: str) -> Optional[Dict[str, Any]]:
        """
        Get student profile by NIM
        
        Args:
            nim: Student NIM
            
        Returns:
            Student profile dictionary or None
        """
        if not self._check_connection():
            return None
        
        try:
            db: Session = self.lms.get_session()
            
            student = db.query(Student).filter(Student.nim == nim).first()
            
            if not student:
                return None
            
            return {
                "id": student.id,
                "nim": student.nim,
                "full_name": student.full_name,
                "jurusan": student.jurusan,
                "angkatan": student.angkatan,
                "semester": student.semester,
                "email": student.email,
                "phone": student.phone,
                "status": student.status
            }
            
        except Exception as e:
            logger.error(f"Error fetching student by NIM: {e}")
            return None
        finally:
            db.close()
    
    def get_student_grades(
        self,
        nim: str,
        semester: Optional[int] = None,
        kategori: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get student grades
        
        Args:
            nim: Student NIM
            semester: Optional filter by semester
            kategori: Optional filter by category (UTS, UAS, Quiz, Tugas)
            
        Returns:
            List of grades
            
        Example:
            grades = service.get_student_grades("12345", semester=3, kategori="UTS")
        """
        if not self._check_connection():
            return []
        
        try:
            db: Session = self.lms.get_session()
            
            # Get student
            student = db.query(Student).filter(Student.nim == nim).first()
            if not student:
                return []
            
            # Build query
            query = db.query(Grade).filter(Grade.student_id == student.id)
            
            if semester:
                query = query.filter(Grade.semester == semester)
            
            if kategori:
                query = query.filter(Grade.kategori == kategori)
            
            # Order by semester and course
            query = query.order_by(Grade.semester, Grade.mata_kuliah)
            
            grades = query.all()
            
            return [
                {
                    "mata_kuliah": g.mata_kuliah,
                    "semester": g.semester,
                    "sks": g.sks,
                    "nilai_angka": float(g.nilai_angka) if g.nilai_angka else None,
                    "nilai_huruf": g.nilai_huruf,
                    "kategori": g.kategori
                }
                for g in grades
            ]
            
        except Exception as e:
            logger.error(f"Error fetching grades: {e}")
            return []
        finally:
            db.close()
    
    def get_student_gpa(self, nim: str, semester: Optional[int] = None) -> Optional[float]:
        """
        Calculate student GPA
        
        Args:
            nim: Student NIM
            semester: Optional specific semester (if None, calculate overall GPA)
            
        Returns:
            GPA value or None
        """
        if not self._check_connection():
            return None
        
        try:
            db: Session = self.lms.get_session()
            
            # Get student
            student = db.query(Student).filter(Student.nim == nim).first()
            if not student:
                return None
            
            # Get grades
            query = db.query(Grade).filter(
                and_(
                    Grade.student_id == student.id,
                    Grade.nilai_angka.isnot(None)
                )
            )
            
            if semester:
                query = query.filter(Grade.semester == semester)
            
            grades = query.all()
            
            if not grades:
                return None
            
            # Calculate weighted average
            total_points = sum(float(g.nilai_angka) * g.sks for g in grades)
            total_sks = sum(g.sks for g in grades)
            
            if total_sks == 0:
                return None
            
            gpa = total_points / total_sks
            return round(gpa / 25, 2)  # Convert to 4.0 scale
            
        except Exception as e:
            logger.error(f"Error calculating GPA: {e}")
            return None
        finally:
            db.close()
    
    def get_student_schedule(
        self,
        nim: str,
        hari: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get student class schedule
        
        Args:
            nim: Student NIM
            hari: Optional filter by day (Senin, Selasa, etc.)
            
        Returns:
            List of schedules
        """
        if not self._check_connection():
            return []
        
        try:
            db: Session = self.lms.get_session()
            
            # Get student
            student = db.query(Student).filter(Student.nim == nim).first()
            if not student:
                return []
            
            # Build query
            query = db.query(Schedule).filter(Schedule.student_id == student.id)
            
            if hari:
                query = query.filter(Schedule.hari == hari)
            
            # Order by day and time
            query = query.order_by(Schedule.hari, Schedule.jam_mulai)
            
            schedules = query.all()
            
            return [
                {
                    "mata_kuliah": s.mata_kuliah,
                    "hari": s.hari,
                    "jam_mulai": str(s.jam_mulai),
                    "jam_selesai": str(s.jam_selesai),
                    "ruang": s.ruang,
                    "dosen": s.dosen
                }
                for s in schedules
            ]
            
        except Exception as e:
            logger.error(f"Error fetching schedule: {e}")
            return []
        finally:
            db.close()
    
    def get_student_assignments(
        self,
        nim: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get student assignments
        
        Args:
            nim: Student NIM
            status: Optional filter by status (pending, submitted, graded)
            
        Returns:
            List of assignments
        """
        if not self._check_connection():
            return []
        
        try:
            db: Session = self.lms.get_session()
            
            # Get student
            student = db.query(Student).filter(Student.nim == nim).first()
            if not student:
                return []
            
            # Build query
            query = db.query(Assignment).filter(Assignment.student_id == student.id)
            
            if status:
                query = query.filter(Assignment.status == status)
            
            # Order by deadline
            query = query.order_by(Assignment.deadline)
            
            assignments = query.all()
            
            return [
                {
                    "mata_kuliah": a.mata_kuliah,
                    "judul": a.judul,
                    "deskripsi": a.deskripsi,
                    "deadline": str(a.deadline),
                    "status": a.status,
                    "nilai": float(a.nilai) if a.nilai else None,
                    "feedback": a.feedback
                }
                for a in assignments
            ]
            
        except Exception as e:
            logger.error(f"Error fetching assignments: {e}")
            return []
        finally:
            db.close()
    
    def get_student_attendance(
        self,
        nim: str,
        mata_kuliah: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get student attendance records
        
        Args:
            nim: Student NIM
            mata_kuliah: Optional filter by course
            
        Returns:
            List of attendance records
        """
        if not self._check_connection():
            return []
        
        try:
            db: Session = self.lms.get_session()
            
            # Get student
            student = db.query(Student).filter(Student.nim == nim).first()
            if not student:
                return []
            
            # Build query
            query = db.query(Attendance).filter(Attendance.student_id == student.id)
            
            if mata_kuliah:
                query = query.filter(Attendance.mata_kuliah == mata_kuliah)
            
            # Order by date descending
            query = query.order_by(Attendance.tanggal.desc())
            
            attendance = query.all()
            
            return [
                {
                    "mata_kuliah": a.mata_kuliah,
                    "tanggal": str(a.tanggal),
                    "status": a.status,
                    "keterangan": a.keterangan
                }
                for a in attendance
            ]
            
        except Exception as e:
            logger.error(f"Error fetching attendance: {e}")
            return []
        finally:
            db.close()
    
    def get_student_summary(self, nim: str) -> Dict[str, Any]:
        """
        Get comprehensive student data summary
        
        Args:
            nim: Student NIM
            
        Returns:
            Dictionary with all student data
            
        This is used to build context for AI chatbot
        """
        if not self._check_connection():
            return {
                "available": False,
                "message": "LMS database not connected"
            }
        
        try:
            # Get student profile
            profile = self.get_student_by_nim(nim)
            if not profile:
                return {
                    "available": False,
                    "message": f"Student with NIM {nim} not found"
                }
            
            # Get current semester
            current_semester = profile.get("semester", 1)
            
            # Get data
            grades = self.get_student_grades(nim, semester=current_semester)
            gpa = self.get_student_gpa(nim, semester=current_semester)
            overall_gpa = self.get_student_gpa(nim)
            schedule = self.get_student_schedule(nim)
            pending_assignments = self.get_student_assignments(nim, status="pending")
            
            return {
                "available": True,
                "profile": profile,
                "academic": {
                    "current_semester": current_semester,
                    "semester_gpa": gpa,
                    "overall_gpa": overall_gpa,
                    "current_grades": grades,
                    "schedule": schedule,
                    "pending_assignments": pending_assignments
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting student summary: {e}")
            return {
                "available": False,
                "message": f"Error fetching data: {str(e)}"
            }
    
    def format_student_context_for_ai(self, nim: str) -> str:
        """
        Format student data as context string for AI
        
        Args:
            nim: Student NIM
            
        Returns:
            Formatted context string
            
        Example output:
            "Nama: Budi Santoso
             NIM: 12345
             Semester: 3
             IPK: 3.5
             
             Nilai Semester 3:
             - Algoritma: 85 (A)
             - Database: 78 (B+)"
        """
        summary = self.get_student_summary(nim)
        
        if not summary.get("available"):
            return summary.get("message", "Data tidak tersedia")
        
        profile = summary["profile"]
        academic = summary["academic"]
        
        # Build context
        context_parts = []
        
        # Profile
        context_parts.append(f"Nama: {profile['full_name']}")
        context_parts.append(f"NIM: {profile['nim']}")
        context_parts.append(f"Jurusan: {profile['jurusan']}")
        context_parts.append(f"Semester: {academic['current_semester']}")
        
        # GPA
        if academic.get("overall_gpa"):
            context_parts.append(f"IPK: {academic['overall_gpa']}")
        if academic.get("semester_gpa"):
            context_parts.append(f"IP Semester ini: {academic['semester_gpa']}")
        
        # Current grades
        if academic.get("current_grades"):
            context_parts.append(f"\nNilai Semester {academic['current_semester']}:")
            for grade in academic["current_grades"]:
                context_parts.append(
                    f"- {grade['mata_kuliah']}: {grade['nilai_angka']} ({grade['nilai_huruf']})"
                )
        
        # Schedule (limit to 5)
        if academic.get("schedule"):
            context_parts.append("\nJadwal Kuliah:")
            for sched in academic["schedule"][:5]:
                context_parts.append(
                    f"- {sched['hari']}: {sched['mata_kuliah']} "
                    f"({sched['jam_mulai']}-{sched['jam_selesai']}) "
                    f"di {sched['ruang']}"
                )
        
        # Pending assignments (limit to 3)
        if academic.get("pending_assignments"):
            context_parts.append("\nTugas Pending:")
            for assignment in academic["pending_assignments"][:3]:
                context_parts.append(
                    f"- {assignment['mata_kuliah']}: {assignment['judul']} "
                    f"(deadline: {assignment['deadline']})"
                )
        
        return "\n".join(context_parts)


# ============================================
# Global Student Data Service Instance
# ============================================

student_data_service = StudentDataService()
