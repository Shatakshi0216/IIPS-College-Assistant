/// ==============================================================================
/// FILE: lib/screens/notice_feed_screen.dart
/// PURPOSE: Personalized Notice Feed screen with AI summary & eligibility badges.
/// ==============================================================================

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../config/api_config.dart';
import '../models/user_model.dart';
import '../models/document_model.dart';
import '../services/document_service.dart';
import '../services/chat_service.dart';

class NoticeFeedScreen extends StatefulWidget {
  final UserModel user;

  const NoticeFeedScreen({super.key, required this.user});

  @override
  State<NoticeFeedScreen> createState() => _NoticeFeedScreenState();
}

class _NoticeFeedScreenState extends State<NoticeFeedScreen> {
  final DocumentService _docService = DocumentService();
  final ChatService _chatService = ChatService();

  List<DocumentModel> _notices = [];
  bool _isLoading = true;
  String _searchQuery = '';

  @override
  void initState() {
    super.initState();
    _loadFeed();
  }

  Future<void> _loadFeed() async {
    setState(() => _isLoading = true);
    final list = await _docService.getPersonalizedFeed();
    setState(() {
      _notices = list;
      _isLoading = false;
    });
  }

  List<DocumentModel> get _filteredNotices {
    if (_searchQuery.trim().isEmpty) return _notices;
    final q = _searchQuery.toLowerCase();
    return _notices.where((doc) {
      final titleMatch = doc.title.toLowerCase().contains(q);
      final summaryMatch = doc.noticeMetadata?.summary?.toLowerCase().contains(q) ?? false;
      return titleMatch || summaryMatch;
    }).toList();
  }

  void _showNoticeDetails(DocumentModel doc) {
    final meta = doc.noticeMetadata;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) {
        return DraggableScrollableSheet(
          initialChildSize: 0.75,
          minChildSize: 0.4,
          maxChildSize: 0.95,
          expand: false,
          builder: (_, scrollController) {
            return SingleChildScrollView(
              controller: scrollController,
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Center(
                    child: Container(
                      width: 40,
                      height: 4,
                      margin: const EdgeInsets.only(bottom: 20),
                      decoration: BoxDecoration(
                        color: Colors.grey.shade300,
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                  ),

                  // Category & Urgent Badges
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.blue.shade50,
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          doc.category.toUpperCase(),
                          style: TextStyle(
                            color: Colors.blue.shade800,
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      if (meta?.isUrgent == true) ...[
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: Colors.red.shade50,
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: const Row(
                            children: [
                              Icon(Icons.bolt, color: Colors.red, size: 14),
                              SizedBox(width: 2),
                              Text(
                                'URGENT',
                                style: TextStyle(
                                  color: Colors.red,
                                  fontSize: 12,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ],
                  ),
                  const SizedBox(height: 12),

                  // Title
                  Text(
                    doc.title,
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF1E293B),
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Summary Section
                  if (meta?.summary != null) ...[
                    const Text(
                      'AI SUMMARY',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 1,
                        color: Colors.grey,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.grey.shade100,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Text(
                        meta!.summary!,
                        style: const TextStyle(fontSize: 14, height: 1.4),
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],

                  // Action Required
                  if (meta?.actionRequired != null) ...[
                    const Text(
                      'ACTION REQUIRED',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 1,
                        color: Colors.grey,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.amber.shade50,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: Colors.amber.shade200),
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Icon(Icons.assignment_turned_in_outlined, color: Colors.orange, size: 20),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              meta!.actionRequired!,
                              style: TextStyle(color: Colors.brown.shade800, fontSize: 14),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],

                  // Criteria Grid
                  const Text(
                    'ELIGIBILITY & DEADLINE',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1,
                      color: Colors.grey,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      if (meta?.deadline != null)
                        Chip(
                          avatar: const Icon(Icons.calendar_today, size: 16, color: Colors.redAccent),
                          label: Text('Deadline: ${meta!.deadline}'),
                          backgroundColor: Colors.red.shade50,
                        ),
                      if (meta?.eligibleBranches.isNotEmpty == true)
                        Chip(
                          avatar: const Icon(Icons.apartment, size: 16, color: Colors.blueAccent),
                          label: Text('Branches: ${meta!.eligibleBranches.join(", ")}'),
                          backgroundColor: Colors.blue.shade50,
                        ),
                      if (meta != null && meta.minCgpa > 0)
                        Chip(
                          avatar: const Icon(Icons.grade, size: 16, color: Colors.purple),
                          label: Text('Min CGPA: ${meta.minCgpa}'),
                          backgroundColor: Colors.purple.shade50,
                        ),
                    ],
                  ),
                  const SizedBox(height: 24),

                  // Open PDF Button
                  ElevatedButton.icon(
                    onPressed: () async {
                      final url = Uri.parse(ApiConfig.documentFileUrl(doc.id));
                      if (await canLaunchUrl(url)) {
                        await launchUrl(url, mode: LaunchMode.externalApplication);
                      }
                    },
                    icon: const Icon(Icons.picture_as_pdf),
                    label: const Text('View Original PDF'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blueAccent,
                      foregroundColor: Colors.white,
                      minimumSize: const Size.fromHeight(48),
                      shape: RoundedRectangle.circular(10),
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade100,
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'College Notices',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
            ),
            if (widget.user.isStudent && widget.user.studentProfile != null)
              Text(
                'Personalized for ${widget.user.studentProfile!.branch} • Year ${widget.user.studentProfile!.year}',
                style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
              ),
          ],
        ),
        backgroundColor: Colors.white,
        elevation: 0,
      ),
      body: Column(
        children: [
          // Search Bar
          Container(
            color: Colors.white,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: TextField(
              onChanged: (val) => setState(() => _searchQuery = val),
              decoration: InputDecoration(
                hintText: 'Search notices by title, criteria...',
                prefixIcon: const Icon(Icons.search, size: 20),
                contentPadding: const EdgeInsets.symmetric(vertical: 10),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide.none,
                ),
                filled: true,
                fillColor: Colors.grey.shade100,
              ),
            ),
          ),

          // Notice Feed List
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _filteredNotices.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.inbox_outlined, size: 54, color: Colors.grey.shade400),
                            const SizedBox(height: 12),
                            Text(
                              'No notices found',
                              style: TextStyle(color: Colors.grey.shade600, fontSize: 16),
                            ),
                          ],
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: _loadFeed,
                        child: ListView.builder(
                          padding: const EdgeInsets.all(12),
                          itemCount: _filteredNotices.length,
                          itemBuilder: (context, idx) {
                            final doc = _filteredNotices[idx];
                            final meta = doc.noticeMetadata;

                            return Card(
                              margin: const EdgeInsets.only(bottom: 12),
                              elevation: 0,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(14),
                                side: BorderSide(color: Colors.grey.shade200),
                              ),
                              child: InkWell(
                                borderRadius: BorderRadius.circular(14),
                                onTap: () => _showNoticeDetails(doc),
                                child: Padding(
                                  padding: const EdgeInsets.all(16),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      // Top Badges
                                      Row(
                                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                        children: [
                                          Container(
                                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                            decoration: BoxDecoration(
                                              color: Colors.blue.shade50,
                                              borderRadius: BorderRadius.circular(6),
                                            ),
                                            child: Text(
                                              doc.category.toUpperCase(),
                                              style: TextStyle(
                                                color: Colors.blue.shade800,
                                                fontSize: 11,
                                                fontWeight: FontWeight.bold,
                                              ),
                                            ),
                                          ),
                                          if (meta?.deadline != null)
                                            Row(
                                              children: [
                                                const Icon(Icons.timer_outlined, size: 14, color: Colors.redAccent),
                                                const SizedBox(width: 4),
                                                Text(
                                                  meta!.deadline!,
                                                  style: const TextStyle(
                                                    color: Colors.redAccent,
                                                    fontSize: 12,
                                                    fontWeight: FontWeight.bold,
                                                  ),
                                                ),
                                              ],
                                            ),
                                        ],
                                      ),
                                      const SizedBox(height: 10),

                                      // Title
                                      Text(
                                        doc.title,
                                        style: const TextStyle(
                                          fontSize: 16,
                                          fontWeight: FontWeight.bold,
                                          color: Color(0xFF1E293B),
                                        ),
                                      ),
                                      const SizedBox(height: 6),

                                      // Summary Preview
                                      if (meta?.summary != null)
                                        Text(
                                          meta!.summary!,
                                          maxLines: 2,
                                          overflow: TextOverflow.ellipsis,
                                          style: TextStyle(color: Colors.grey.shade700, fontSize: 13),
                                        ),
                                      const SizedBox(height: 12),

                                      // Eligibility Tags
                                      Wrap(
                                        spacing: 6,
                                        runSpacing: 4,
                                        children: [
                                          if (meta?.eligibleBranches.isNotEmpty == true)
                                            Container(
                                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                              decoration: BoxDecoration(
                                                color: Colors.grey.shade100,
                                                borderRadius: BorderRadius.circular(4),
                                              ),
                                              child: Text(
                                                'Branch: ${meta!.eligibleBranches.join(", ")}',
                                                style: const TextStyle(fontSize: 11, color: Colors.black87),
                                              ),
                                            ),
                                          if (meta != null && meta.minCgpa > 0)
                                            Container(
                                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                              decoration: BoxDecoration(
                                                color: Colors.purple.shade50,
                                                borderRadius: BorderRadius.circular(4),
                                              ),
                                              child: Text(
                                                'Min CGPA: ${meta.minCgpa}',
                                                style: TextStyle(fontSize: 11, color: Colors.purple.shade700),
                                              ),
                                            ),
                                        ],
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            );
                          },
                        ),
                      ),
          ),
        ],
      ),
    );
  }
}
