/// ==============================================================================
/// FILE: lib/models/chat_message_model.dart
/// PURPOSE: Data models for AI Assistant conversation messages and RAG source citations.
/// ==============================================================================

class SourceCitationModel {
  final int? documentId;
  final String documentTitle;
  final String snippet;

  SourceCitationModel({
    this.documentId,
    required this.documentTitle,
    required this.snippet,
  });

  factory SourceCitationModel.fromJson(Map<String, dynamic> json) {
    return SourceCitationModel(
      documentId: json['document_id'],
      documentTitle: json['document_title'] ?? 'College Document',
      snippet: json['snippet'] ?? '',
    );
  }
}

class ChatMessageModel {
  final String text;
  final bool isUser;
  final DateTime timestamp;
  final List<SourceCitationModel> sources;
  final bool isLoading;

  ChatMessageModel({
    required this.text,
    required this.isUser,
    required this.timestamp,
    this.sources = const [],
    this.isLoading = false,
  });
}
