/// ==============================================================================
/// FILE: lib/services/auth_service.dart
/// PURPOSE: Authentication service handling Login, Registration, Session persistence,
///          and JWT token storage using SharedPreferences.
/// ==============================================================================

import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../config/api_config.dart';
import '../models/user_model.dart';

class AuthService {
  static const String _tokenKey = 'jwt_token';
  static const String _userKey = 'user_data';

  /// Performs user login via JSON payload
  Future<Map<String, dynamic>> login(String email, String password) async {
    try {
      final response = await http.post(
        Uri.parse(ApiConfig.loginUrl),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': email.trim(),
          'password': password,
        }),
      );

      final data = jsonDecode(response.body);

      if (response.statusCode == 200) {
        final token = data['access_token'];
        await saveToken(token);

        // Fetch full user profile
        final user = await fetchCurrentUser();
        return {'success': true, 'token': token, 'user': user};
      } else {
        return {
          'success': false,
          'message': data['detail'] ?? 'Login failed. Please check your credentials.'
        };
      }
    } catch (e) {
      return {'success': false, 'message': 'Network error: $e'};
    }
  }

  /// Registers a new student or faculty account
  Future<Map<String, dynamic>> register({
    required String email,
    required String password,
    required String fullName,
    required String role,
    Map<String, dynamic>? studentProfile,
    Map<String, dynamic>? facultyProfile,
  }) async {
    try {
      final payload = {
        'email': email.trim(),
        'password': password,
        'full_name': fullName.trim(),
        'role': role.toLowerCase(),
        'student_profile': studentProfile,
        'faculty_profile': facultyProfile,
      };

      final response = await http.post(
        Uri.parse(ApiConfig.registerUrl),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      );

      final data = jsonDecode(response.body);

      if (response.statusCode == 201) {
        // Automatically login the user after registration
        return await login(email, password);
      } else {
        return {
          'success': false,
          'message': data['detail'] ?? 'Registration failed.'
        };
      }
    } catch (e) {
      return {'success': false, 'message': 'Network error: $e'};
    }
  }

  /// Fetches authenticated user's profile details from /api/v1/auth/me
  Future<UserModel?> fetchCurrentUser() async {
    final token = await getToken();
    if (token == null) return null;

    try {
      final response = await http.get(
        Uri.parse(ApiConfig.meUrl),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final user = UserModel.fromJson(data);
        await saveUser(user);
        return user;
      }
    } catch (e) {
      // Return cached user if network fails
      return getCachedUser();
    }
    return null;
  }

  /// Token & User Persistence
  Future<void> saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, token);
  }

  Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_tokenKey);
  }

  Future<void> saveUser(UserModel user) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_userKey, jsonEncode(user.toJson()));
  }

  Future<UserModel?> getCachedUser() async {
    final prefs = await SharedPreferences.getInstance();
    final userStr = prefs.getString(_userKey);
    if (userStr != null) {
      try {
        return UserModel.fromJson(jsonDecode(userStr));
      } catch (_) {}
    }
    return null;
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
    await prefs.remove(_userKey);
  }

  Future<bool> isLoggedIn() async {
    final token = await getToken();
    return token != null && token.isNotEmpty;
  }
}
