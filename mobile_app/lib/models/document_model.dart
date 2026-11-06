/// ==============================================================================
/// FILE: lib/models/document_model.dart
/// PURPOSE: Data models for Document, NoticeMetadata, and AcademicResource.
/// ==============================================================================

class NoticeMetadataModel {
  final int id;
  final String title;
  final String? summary;
  final String? actionRequired;
  final String? deadline;
  final List<String> eligibleBranches;
  final List<int> eligibleYears;
  final double minCgpa;
  final String? contactInfo;
  final bool isUrgent;

  NoticeMetadataModel({
    required this.id,
    required this.title,
    this.summary,
    this.actionRequired,
    this.deadline,
    required this.eligibleBranches,
    required this.eligibleYears,
    required this.minCgpa,
    this.contactInfo,
    this.isUrgent = false,
  });

  factory NoticeMetadataModel.fromJson(Map<String, dynamic> json) {
    return NoticeMetadataModel(
      id: json['id'] ?? 0,
      title: json['title'] ?? '',
      summary: json['summary'],
      actionRequired: json['action_required'],
      deadline: json['deadline'],
      eligibleBranches: (json['eligible_branches'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      eligibleYears: (json['eligible_years'] as List<dynamic>?)
              ?.map((e) => int.tryParse(e.toString()) ?? 1)
              .toList() ??
          [],
      minCgpa: (json['min_cgpa'] is num) ? (json['min_cgpa'] as num).toDouble() : 0.0,
      contactInfo: json['contact_info'],
      isUrgent: json['is_urgent'] ?? false,
    );
  }
}

class AcademicResourceModel {
  final int id;
  final String branch;
  final int year;
  final int semester;
  final String subjectName;
  final String? subjectCode;
  final String resourceType; // "syllabus", "question_paper", "notes"
  final int? examYear;

  AcademicResourceModel({
    required this.id,
    required this.branch,
    required this.year,
    required this.semester,
    required this.subjectName,
    this.subjectCode,
    required this.resourceType,
    this.examYear,
  });

  factory AcademicResourceModel.fromJson(Map<String, dynamic> json) {
    return AcademicResourceModel(
      id: json['id'] ?? 0,
      branch: json['branch'] ?? '',
      year: json['year'] ?? 1,
      semester: json['semester'] ?? 1,
      subjectName: json['subject_name'] ?? '',
      subjectCode: json['subject_code'],
      resourceType: json['resource_type'] ?? 'syllabus',
      examYear: json['exam_year'],
    );
  }
}

class DocumentModel {
  final int id;
  final String title;
  final String fileName;
  final String filePath;
  final int fileSizeBytes;
  final String category; // "notice", "syllabus", "question_paper", "circular", "rule"
  final bool isProcessed;
  final int? uploadedById;
  final DateTime? createdAt;
  final NoticeMetadataModel? noticeMetadata;
  final AcademicResourceModel? academicResource;

  DocumentModel({
    required this.id,
    required this.title,
    required this.fileName,
    required this.filePath,
    required this.fileSizeBytes,
    required this.category,
    required this.isProcessed,
    this.uploadedById,
    this.createdAt,
    this.noticeMetadata,
    this.academicResource,
  });

  factory DocumentModel.fromJson(Map<String, dynamic> json) {
    return DocumentModel(
      id: json['id'] ?? 0,
      title: json['title'] ?? '',
      fileName: json['file_name'] ?? '',
      filePath: json['file_path'] ?? '',
      fileSizeBytes: json['file_size_bytes'] ?? 0,
      category: json['category'] ?? 'notice',
      isProcessed: json['is_processed'] ?? false,
      uploadedById: json['uploaded_by_id'],
      createdAt: json['created_at'] != null ? DateTime.tryParse(json['created_at']) : null,
      noticeMetadata: json['notice_metadata'] != null
          ? NoticeMetadataModel.fromJson(json['notice_metadata'])
          : null,
      academicResource: json['academic_resource'] != null
          ? AcademicResourceModel.fromJson(json['academic_resource'])
          : null,
    );
  }
}
