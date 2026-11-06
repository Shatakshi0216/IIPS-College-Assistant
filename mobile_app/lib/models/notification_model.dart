/// ==============================================================================
/// FILE: lib/models/notification_model.dart
/// PURPOSE: Data model for Targeted Student Push Notifications & Alerts.
/// ==============================================================================

class NotificationModel {
  final int id;
  final String title;
  final String message;
  final int? documentId;
  final bool isRead;
  final DateTime? createdAt;

  NotificationModel({
    required this.id,
    required this.title,
    required this.message,
    this.documentId,
    required this.isRead,
    this.createdAt,
  });

  factory NotificationModel.fromJson(Map<String, dynamic> json) {
    return NotificationModel(
      id: json['id'] ?? 0,
      title: json['title'] ?? '',
      message: json['message'] ?? '',
      documentId: json['document_id'],
      isRead: json['is_read'] ?? false,
      createdAt: json['created_at'] != null ? DateTime.tryParse(json['created_at']) : null,
    );
  }
}
