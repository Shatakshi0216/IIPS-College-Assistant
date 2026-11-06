/// ==============================================================================
/// FILE: lib/screens/main_navigation_screen.dart
/// PURPOSE: Main shell navigation with responsive bottom navigation bar.
/// ==============================================================================

import 'package:flutter/material.dart';
import '../models/user_model.dart';
import 'notice_feed_screen.dart';
import 'academic_resources_screen.dart';
import 'ai_chat_screen.dart';
import 'upload_screen.dart';
import 'notifications_screen.dart';
import 'profile_screen.dart';

class MainNavigationScreen extends StatefulWidget {
  final UserModel user;

  const MainNavigationScreen({super.key, required this.user});

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _currentIndex = 0;
  late final List<Widget> _screens;

  @override
  void initState() {
    super.initState();
    final isFaculty = widget.user.isFaculty;

    if (isFaculty) {
      // Faculty navigation: Notices, Upload, AI Chat, Profile
      _screens = [
        NoticeFeedScreen(user: widget.user),
        UploadScreen(user: widget.user),
        AiChatScreen(user: widget.user),
        ProfileScreen(user: widget.user),
      ];
    } else {
      // Student navigation: Notices, Resources, AI Chat, Alerts, Profile
      _screens = [
        NoticeFeedScreen(user: widget.user),
        AcademicResourcesScreen(user: widget.user),
        AiChatScreen(user: widget.user),
        NotificationsScreen(user: widget.user),
        ProfileScreen(user: widget.user),
      ];
    }
  }

  @override
  Widget build(BuildContext context) {
    final isFaculty = widget.user.isFaculty;

    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (idx) => setState(() => _currentIndex = idx),
        indicatorColor: Colors.blueAccent.withOpacity(0.18),
        destinations: isFaculty
            ? const [
                NavigationDestination(
                  icon: Icon(Icons.feed_outlined),
                  selectedIcon: Icon(Icons.feed, color: Colors.blueAccent),
                  label: 'Notices',
                ),
                NavigationDestination(
                  icon: Icon(Icons.cloud_upload_outlined),
                  selectedIcon: Icon(Icons.cloud_upload, color: Colors.blueAccent),
                  label: 'Upload',
                ),
                NavigationDestination(
                  icon: Icon(Icons.smart_toy_outlined),
                  selectedIcon: Icon(Icons.smart_toy, color: Colors.blueAccent),
                  label: 'AI Chat',
                ),
                NavigationDestination(
                  icon: Icon(Icons.person_outline),
                  selectedIcon: Icon(Icons.person, color: Colors.blueAccent),
                  label: 'Profile',
                ),
              ]
            : const [
                NavigationDestination(
                  icon: Icon(Icons.feed_outlined),
                  selectedIcon: Icon(Icons.feed, color: Colors.blueAccent),
                  label: 'Notices',
                ),
                NavigationDestination(
                  icon: Icon(Icons.menu_book_outlined),
                  selectedIcon: Icon(Icons.menu_book, color: Colors.blueAccent),
                  label: 'Resources',
                ),
                NavigationDestination(
                  icon: Icon(Icons.smart_toy_outlined),
                  selectedIcon: Icon(Icons.smart_toy, color: Colors.blueAccent),
                  label: 'AI Chat',
                ),
                NavigationDestination(
                  icon: Icon(Icons.notifications_outlined),
                  selectedIcon: Icon(Icons.notifications, color: Colors.blueAccent),
                  label: 'Alerts',
                ),
                NavigationDestination(
                  icon: Icon(Icons.person_outline),
                  selectedIcon: Icon(Icons.person, color: Colors.blueAccent),
                  label: 'Profile',
                ),
              ],
      ),
    );
  }
}
