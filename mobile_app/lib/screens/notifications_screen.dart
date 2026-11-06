/// ==============================================================================
/// FILE: lib/screens/notifications_screen.dart
/// PURPOSE: Student Notifications & Targeted Alerts Center.
/// ==============================================================================

import 'package:flutter/material.dart';
import '../models/user_model.dart';
import '../models/notification_model.dart';
import '../services/document_service.dart';

class NotificationsScreen extends StatefulWidget {
  final UserModel user;

  const NotificationsScreen({super.key, required this.user});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  final DocumentService _docService = DocumentService();
  List<NotificationModel> _notifications = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadNotifications();
  }

  Future<void> _loadNotifications() async {
    setState(() => _isLoading = true);
    final list = await _docService.getNotifications();
    setState(() {
      _notifications = list;
      _isLoading = false;
    });
  }

  Future<void> _markRead(NotificationModel notif) async {
    if (notif.isRead) return;
    await _docService.markNotificationAsRead(notif.id);
    _loadNotifications();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade100,
      appBar: AppBar(
        title: const Text(
          'Targeted Alerts',
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
        ),
        backgroundColor: Colors.white,
        elevation: 0,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _notifications.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.notifications_off_outlined, size: 54, color: Colors.grey.shade400),
                      const SizedBox(height: 12),
                      Text(
                        'No notifications yet',
                        style: TextStyle(color: Colors.grey.shade600, fontSize: 16),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'You will receive alerts when notices match your branch & CGPA.',
                        textAlign: TextAlign.center,
                        style: TextStyle(color: Colors.grey.shade500, fontSize: 12),
                      ),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _loadNotifications,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: _notifications.length,
                    itemBuilder: (context, idx) {
                      final n = _notifications[idx];

                      return Card(
                        margin: const EdgeInsets.only(bottom: 10),
                        elevation: 0,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                          side: BorderSide(
                            color: n.isRead ? Colors.grey.shade200 : Colors.blueAccent.withOpacity(0.4),
                          ),
                        ),
                        child: ListTile(
                          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                          leading: Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: n.isRead ? Colors.grey.shade100 : Colors.blue.shade50,
                              shape: BoxShape.circle,
                            ),
                            child: Icon(
                              Icons.notifications_active,
                              size: 20,
                              color: n.isRead ? Colors.grey : Colors.blueAccent,
                            ),
                          ),
                          title: Text(
                            n.title,
                            style: TextStyle(
                              fontWeight: n.isRead ? FontWeight.normal : FontWeight.bold,
                              fontSize: 14,
                            ),
                          ),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const SizedBox(height: 4),
                              Text(n.message, style: const TextStyle(fontSize: 13)),
                              if (n.createdAt != null) ...[
                                const SizedBox(height: 4),
                                Text(
                                  '${n.createdAt!.day}/${n.createdAt!.month}/${n.createdAt!.year}',
                                  style: TextStyle(color: Colors.grey.shade500, fontSize: 11),
                                ),
                              ],
                            ],
                          ),
                          trailing: n.isRead
                              ? null
                              : IconButton(
                                  icon: const Icon(Icons.check_circle_outline, color: Colors.blueAccent),
                                  tooltip: 'Mark as read',
                                  onPressed: () => _markRead(n),
                                ),
                        ),
                      );
                    },
                  ),
                ),
    );
  }
}
