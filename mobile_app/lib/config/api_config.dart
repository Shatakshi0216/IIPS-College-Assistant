/// ==============================================================================
/// FILE: lib/config/api_config.dart
/// PURPOSE: Central API configuration for connecting the Flutter app to FastAPI.
/// ==============================================================================
class ApiConfig {
  /// Base URL of the FastAPI backend.
  /// - For Android Emulator use: http://10.0.2.2:8000
  /// - For iOS Simulator or Chrome Web use: http://localhost:8000
  /// - For Physical Android/iOS Device use your machine's Wi-Fi IP: http://192.168.x.x:8000
  static const String baseUrl = "http://10.0.2.2:8000";

  /// API V1 prefix
  static const String apiPrefix = "$baseUrl/api/v1";

  // Auth Endpoints
  static const String loginUrl = "$apiPrefix/auth/login-json";
  static const String registerUrl = "$apiPrefix/auth/register";
  static const String meUrl = "$apiPrefix/auth/me";

  // Document Endpoints
  static const String documentsUrl = "$apiPrefix/documents";
  static const String uploadUrl = "$apiPrefix/documents/upload";
  static String documentFileUrl(int id) => "$apiPrefix/documents/$id/file";

  // Notice & Feed Endpoints
  static const String noticeFeedUrl = "$apiPrefix/notices/feed";
  static const String notificationsUrl = "$apiPrefix/notices/notifications";
  static String markNotificationReadUrl(int id) => "$apiPrefix/notices/notifications/$id/read";

  // Academic Resources Endpoints
  static const String resourcesUrl = "$apiPrefix/resources";
  static const String subjectsUrl = "$apiPrefix/resources/subjects";

  // AI Chat & RAG Endpoints
  static const String chatAskUrl = "$apiPrefix/chat/ask";
  static String summarizeDocUrl(int id) => "$apiPrefix/chat/summarize/$id";
}
