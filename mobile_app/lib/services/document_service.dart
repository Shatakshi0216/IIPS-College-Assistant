/// ==============================================================================
/// FILE: lib/services/document_service.dart
/// PURPOSE: Handles notice feeds, academic resources, multipart PDF file uploads,
///          and targeted notifications.
/// ==============================================================================

import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import '../models/document_model.dart';
import '../models/notification_model.dart';
import 'auth_service.dart';

class DocumentService {
  final AuthService _authService = AuthService();

  /// Helper to get authorization headers
  Future<Map<String, String>> _getHeaders() async {
    final token = await _authService.getToken();
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  /// Fetches personalized notice feed for the logged-in student
  Future<List<DocumentModel>> getPersonalizedFeed() async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(Uri.parse(ApiConfig.noticeFeedUrl), headers: headers);

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data.map((json) => DocumentModel.fromJson(json)).toList();
      }
    } catch (e) {
      print('Error fetching notice feed: $e');
    }
    return [];
  }

  /// Fetches filtered academic resources (syllabus & question papers)
  Future<List<DocumentModel>> getAcademicResources({
    String? branch,
    int? year,
    int? semester,
    String? subjectName,
    String? resourceType,
  }) async {
    try {
      final queryParams = <String, String>{};
      if (branch != null && branch.isNotEmpty && branch != 'ALL') {
        queryParams['branch'] = branch;
      }
      if (year != null && year > 0) {
        queryParams['year'] = year.toString();
      }
      if (semester != null && semester > 0) {
        queryParams['semester'] = semester.toString();
      }
      if (subjectName != null && subjectName.isNotEmpty) {
        queryParams['subject_name'] = subjectName;
      }
      if (resourceType != null && resourceType.isNotEmpty && resourceType != 'ALL') {
        queryParams['resource_type'] = resourceType.toLowerCase();
      }

      final uri = Uri.parse(ApiConfig.resourcesUrl).replace(queryParameters: queryParams);
      final headers = await _getHeaders();
      final response = await http.get(uri, headers: headers);

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data.map((json) => DocumentModel.fromJson(json)).toList();
      }
    } catch (e) {
      print('Error fetching academic resources: $e');
    }
    return [];
  }

  /// Uploads a PDF document via multipart request (Faculty/Admin only)
  Future<Map<String, dynamic>> uploadDocument({
    required String filePath,
    required String title,
    required String category,
    String? branch,
    int? year,
    int? semester,
    String? subjectName,
    String? subjectCode,
    int? examYear,
  }) async {
    try {
      final token = await _authService.getToken();
      final uri = Uri.parse(ApiConfig.uploadUrl);

      final request = http.MultipartRequest('POST', uri);
      if (token != null) {
        request.headers['Authorization'] = 'Bearer $token';
      }

      // Add text form fields
      request.fields['title'] = title;
      request.fields['category'] = category.toLowerCase();
      if (branch != null) request.fields['branch'] = branch;
      if (year != null) request.fields['year'] = year.toString();
      if (semester != null) request.fields['semester'] = semester.toString();
      if (subjectName != null) request.fields['subject_name'] = subjectName;
      if (subjectCode != null) request.fields['subject_code'] = subjectCode;
      if (examYear != null) request.fields['exam_year'] = examYear.toString();

      // Add PDF file
      request.files.add(await http.MultipartFile.fromPath('file', filePath));

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);
      final data = jsonDecode(response.body);

      if (response.statusCode == 201) {
        return {'success': true, 'data': DocumentModel.fromJson(data)};
      } else {
        return {'success': false, 'message': data['detail'] ?? 'Upload failed'};
      }
    } catch (e) {
      return {'success': false, 'message': 'Upload error: $e'};
    }
  }

  /// Fetches targeted notifications dispatched for the student
  Future<List<NotificationModel>> getNotifications() async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(Uri.parse(ApiConfig.notificationsUrl), headers: headers);

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data.map((json) => NotificationModel.fromJson(json)).toList();
      }
    } catch (e) {
      print('Error fetching notifications: $e');
    }
    return [];
  }

  /// Marks a notification as read
  Future<bool> markNotificationAsRead(int notificationId) async {
    try {
      final headers = await _getHeaders();
      final response = await http.post(
        Uri.parse(ApiConfig.markNotificationReadUrl(notificationId)),
        headers: headers,
      );
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }
}
