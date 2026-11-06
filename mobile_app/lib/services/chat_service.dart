/// ==============================================================================
/// FILE: lib/services/chat_service.dart
/// PURPOSE: Powers RAG queries and Document Summaries using Gemini AI.
/// ==============================================================================

import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import '../models/chat_message_model.dart';
import 'auth_service.dart';

class ChatService {
  final AuthService _authService = AuthService();

  /// Asks the AI College Assistant a question grounded in official documents
  Future<Map<String, dynamic>> askQuestion(String query, {int? documentId}) async {
    try {
      final token = await _authService.getToken();
      final headers = {
        'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      };

      final payload = {
        'query': query.trim(),
        if (documentId != null) 'document_id': documentId,
      };

      final response = await http.post(
        Uri.parse(ApiConfig.chatAskUrl),
        headers: headers,
        body: jsonEncode(payload),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final List<dynamic> rawSources = data['sources'] ?? [];
        final sources = rawSources.map((s) => SourceCitationModel.fromJson(s)).toList();

        return {
          'success': true,
          'answer': data['answer'] ?? 'No answer provided.',
          'sources': sources,
        };
      } else {
        return {
          'success': false,
          'answer': 'Sorry, I encountered an error retrieving college records.',
          'sources': <SourceCitationModel>[],
        };
      }
    } catch (e) {
      return {
        'success': false,
        'answer': 'Unable to connect to college server: $e',
        'sources': <SourceCitationModel>[],
      };
    }
  }

  /// Requests an AI-generated concise summary of a specific document
  Future<Map<String, dynamic>> summarizeDocument(int documentId) async {
    try {
      final token = await _authService.getToken();
      final headers = {
        'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      };

      final response = await http.get(
        Uri.parse(ApiConfig.summarizeDocUrl(documentId)),
        headers: headers,
      );

      if (response.statusCode == 200) {
        return {'success': true, 'data': jsonDecode(response.body)};
      } else {
        return {'success': false, 'message': 'Failed to generate document summary'};
      }
    } catch (e) {
      return {'success': false, 'message': 'Network error: $e'};
    }
  }
}
