"""
LMS Database Models (Read-Only)
SQLAlchemy ORM models for querying LMS PostgreSQL database
These models are READ-ONLY - no INSERT/UPDATE/DELETE operations
"""

from sqlalchemy import Column, Integer, String, Text, Date, Time, DECIMAL, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    """LMS Users table"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # admin, student, teacher
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationship
    student = relationship("Student", back_populates="user", uselist=False)


class Student(Base):
    """LMS Students table"""
    __tablename__ = 'students'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    nim = Column(String(20), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    jurusan = Column(String(100), nullable=False)
    angkatan = Column(Integer, nullable=False)
    semester = Column(Integer, default=1)
    email = Column(String(100))
    phone = Column(String(20))
    address = Column(Text)
    status = Column(String(20), default='active')
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="student")
    grades = relationship("Grade", back_populates="student")
    schedules = relationship("Schedule", back_populates="student")
    assignments = relationship("Assignment", back_populates="student")
    attendance = relationship("Attendance", back_populates="student")


class Grade(Base):
    """LMS Grades table"""
    __tablename__ = 'grades'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'))
    mata_kuliah = Column(String(100), nullable=False)
    semester = Column(Integer, nullable=False)
    sks = Column(Integer, nullable=False)
    nilai_angka = Column(DECIMAL(4, 2))
    nilai_huruf = Column(String(2))
    kategori = Column(String(20))  # UTS, UAS, Quiz, Tugas
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationship
    student = relationship("Student", back_populates="grades")


class Schedule(Base):
    """LMS Schedules table"""
    __tablename__ = 'schedules'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'))
    mata_kuliah = Column(String(100), nullable=False)
    hari = Column(String(10), nullable=False)  # Senin, Selasa, etc.
    jam_mulai = Column(Time, nullable=False)
    jam_selesai = Column(Time, nullable=False)
    ruang = Column(String(20))
    dosen = Column(String(100))
    semester = Column(Integer, nullable=False)
    tahun_ajaran = Column(String(10))
    
    # Relationship
    student = relationship("Student", back_populates="schedules")


class Assignment(Base):
    """LMS Assignments table"""
    __tablename__ = 'assignments'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'))
    mata_kuliah = Column(String(100), nullable=False)
    judul = Column(String(200), nullable=False)
    deskripsi = Column(Text)
    deadline = Column(TIMESTAMP, nullable=False)
    status = Column(String(20), default='pending')  # pending, submitted, graded
    submitted_at = Column(TIMESTAMP)
    nilai = Column(DECIMAL(4, 2))
    feedback = Column(Text)
    
    # Relationship
    student = relationship("Student", back_populates="assignments")


class Attendance(Base):
    """LMS Attendance table"""
    __tablename__ = 'attendance'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'))
    mata_kuliah = Column(String(100), nullable=False)
    tanggal = Column(Date, nullable=False)
    status = Column(String(10), nullable=False)  # hadir, izin, sakit, alpha
    keterangan = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationship
    student = relationship("Student", back_populates="attendance")
