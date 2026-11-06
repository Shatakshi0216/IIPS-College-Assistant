/// ==============================================================================
/// FILE: lib/models/user_model.dart
/// PURPOSE: Data models for User, StudentProfile, and FacultyProfile.
/// ==============================================================================

class StudentProfile {
  final int id;
  final String? rollNumber;
  final String branch;
  final int year;
  final int semester;
  final String? section;
  final double cgpa;

  StudentProfile({
    required this.id,
    this.rollNumber,
    required this.branch,
    required this.year,
    required this.semester,
    this.section,
    required this.cgpa,
  });

  factory StudentProfile.fromJson(Map<String, dynamic> json) {
    return StudentProfile(
      id: json['id'] ?? 0,
      rollNumber: json['roll_number'],
      branch: json['branch'] ?? '',
      year: json['year'] ?? 1,
      semester: json['semester'] ?? 1,
      section: json['section'],
      cgpa: (json['cgpa'] is num) ? (json['cgpa'] as num).toDouble() : 0.0,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'roll_number': rollNumber,
    'branch': branch,
    'year': year,
    'semester': semester,
    'section': section,
    'cgpa': cgpa,
  };
}

class FacultyProfile {
  final int id;
  final String? employeeId;
  final String department;
  final String? designation;

  FacultyProfile({
    required this.id,
    this.employeeId,
    required this.department,
    this.designation,
  });

  factory FacultyProfile.fromJson(Map<String, dynamic> json) {
    return FacultyProfile(
      id: json['id'] ?? 0,
      employeeId: json['employee_id'],
      department: json['department'] ?? '',
      designation: json['designation'],
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'employee_id': employeeId,
    'department': department,
    'designation': designation,
  };
}

class UserModel {
  final int id;
  final String email;
  final String fullName;
  final String role; // "student", "faculty", "admin"
  final bool isActive;
  final DateTime? createdAt;
  final StudentProfile? studentProfile;
  final FacultyProfile? facultyProfile;

  UserModel({
    required this.id,
    required this.email,
    required this.fullName,
    required this.role,
    this.isActive = true,
    this.createdAt,
    this.studentProfile,
    this.facultyProfile,
  });

  bool get isFaculty => role.toLowerCase() == 'faculty' || role.toLowerCase() == 'admin';
  bool get isStudent => role.toLowerCase() == 'student';

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id'] ?? 0,
      email: json['email'] ?? '',
      fullName: json['full_name'] ?? '',
      role: json['role'] ?? 'student',
      isActive: json['is_active'] ?? true,
      createdAt: json['created_at'] != null ? DateTime.tryParse(json['created_at']) : null,
      studentProfile: json['student_profile'] != null
          ? StudentProfile.fromJson(json['student_profile'])
          : null,
      facultyProfile: json['faculty_profile'] != null
          ? FacultyProfile.fromJson(json['faculty_profile'])
          : null,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'email': email,
    'full_name': fullName,
    'role': role,
    'is_active': isActive,
    'student_profile': studentProfile?.toJson(),
    'faculty_profile': facultyProfile?.toJson(),
  };
}
