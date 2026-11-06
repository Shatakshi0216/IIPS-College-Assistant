/// ==============================================================================
/// FILE: lib/screens/academic_resources_screen.dart
/// PURPOSE: Academic Resources catalog (Syllabus & Previous-Year Question Papers)
///          with Branch, Semester, and Resource Type filtering.
/// ==============================================================================

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../config/api_config.dart';
import '../models/user_model.dart';
import '../models/document_model.dart';
import '../services/document_service.dart';
import '../services/chat_service.dart';

class AcademicResourcesScreen extends StatefulWidget {
  final UserModel user;

  const AcademicResourcesScreen({super.key, required this.user});

  @override
  State<AcademicResourcesScreen> createState() => _AcademicResourcesScreenState();
}

class _AcademicResourcesScreenState extends State<AcademicResourcesScreen> {
  final DocumentService _docService = DocumentService();
  final ChatService _chatService = ChatService();

  List<DocumentModel> _resources = [];
  bool _isLoading = true;

  String _selectedBranch = 'ALL';
  int _selectedSemester = 0; // 0 = ALL
  String _selectedType = 'ALL'; // ALL, syllabus, question_paper, notes

  final List<String> _branches = ['ALL', 'CSE', 'IT', 'ECE', 'ME', 'CE', 'EE'];
  final List<int> _semesters = [0, 1, 2, 3, 4, 5, 6, 7, 8];

  @override
  void initState() {
    super.initState();
    // Default to student's branch and semester if student
    if (widget.user.isStudent && widget.user.studentProfile != null) {
      _selectedBranch = widget.user.studentProfile!.branch;
      _selectedSemester = widget.user.studentProfile!.semester;
    }
    _loadResources();
  }

  Future<void> _loadResources() async {
    setState(() => _isLoading = true);

    final list = await _docService.getAcademicResources(
      branch: _selectedBranch,
      semester: _selectedSemester,
      resourceType: _selectedType,
    );

    setState(() {
      _resources = list;
      _isLoading = false;
    });
  }

  void _showAiSummary(DocumentModel doc) async {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (_) => const Center(child: CircularProgressIndicator()),
    );

    final result = await _chatService.summarizeDocument(doc.id);
    if (!mounted) return;
    Navigator.of(context).pop(); // dismiss loader

    if (result['success'] == true) {
      final data = result['data'];
      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          title: Row(
            children: [
              const Icon(Icons.auto_awesome, color: Colors.purple),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  doc.title,
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
          content: SingleChildScrollView(
            child: Text(
              data['summary'] ?? 'Summary not available.',
              style: const TextStyle(height: 1.4),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(),
              child: const Text('Close'),
            ),
          ],
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Failed to generate summary.')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade100,
      appBar: AppBar(
        title: const Text(
          'Academic Resources',
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
        ),
        backgroundColor: Colors.white,
        elevation: 0,
      ),
      body: Column(
        children: [
          // Filter Section
          Container(
            color: Colors.white,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Column(
              children: [
                Row(
                  children: [
                    // Branch Dropdown
                    Expanded(
                      child: DropdownButtonFormField<String>(
                        value: _selectedBranch,
                        decoration: InputDecoration(
                          labelText: 'Branch',
                          contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                        items: _branches
                            .map((b) => DropdownMenuItem(value: b, child: Text(b)))
                            .toList(),
                        onChanged: (val) {
                          setState(() => _selectedBranch = val!);
                          _loadResources();
                        },
                      ),
                    ),
                    const SizedBox(width: 10),

                    // Semester Dropdown
                    Expanded(
                      child: DropdownButtonFormField<int>(
                        value: _selectedSemester,
                        decoration: InputDecoration(
                          labelText: 'Semester',
                          contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                        items: _semesters
                            .map((s) => DropdownMenuItem(
                                  value: s,
                                  child: Text(s == 0 ? 'All Sem' : 'Sem $s'),
                                ))
                            .toList(),
                        onChanged: (val) {
                          setState(() => _selectedSemester = val!);
                          _loadResources();
                        },
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),

                // Resource Type Pills
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: [
                      _buildTypeFilterChip('ALL', 'All Resources'),
                      const SizedBox(width: 8),
                      _buildTypeFilterChip('syllabus', 'Syllabus'),
                      const SizedBox(width: 8),
                      _buildTypeFilterChip('question_paper', 'Past Papers'),
                      const SizedBox(width: 8),
                      _buildTypeFilterChip('notes', 'Notes'),
                    ],
                  ),
                ),
              ],
            ),
          ),

          // Resource List
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _resources.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.library_books_outlined, size: 54, color: Colors.grey.shade400),
                            const SizedBox(height: 12),
                            Text(
                              'No academic resources found',
                              style: TextStyle(color: Colors.grey.shade600, fontSize: 16),
                            ),
                          ],
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: _loadResources,
                        child: ListView.builder(
                          padding: const EdgeInsets.all(12),
                          itemCount: _resources.length,
                          itemBuilder: (context, idx) {
                            final doc = _resources[idx];
                            final res = doc.academicResource;

                            final isSyllabus = doc.category == 'syllabus';

                            return Card(
                              margin: const EdgeInsets.only(bottom: 12),
                              elevation: 0,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(14),
                                side: BorderSide(color: Colors.grey.shade200),
                              ),
                              child: Padding(
                                padding: const EdgeInsets.all(16),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                      children: [
                                        Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                          decoration: BoxDecoration(
                                            color: isSyllabus ? Colors.indigo.shade50 : Colors.teal.shade50,
                                            borderRadius: BorderRadius.circular(6),
                                          ),
                                          child: Text(
                                            doc.category.toUpperCase().replaceAll('_', ' '),
                                            style: TextStyle(
                                              color: isSyllabus ? Colors.indigo.shade800 : Colors.teal.shade800,
                                              fontSize: 11,
                                              fontWeight: FontWeight.bold,
                                            ),
                                          ),
                                        ),
                                        if (res?.examYear != null)
                                          Text(
                                            'Exam Year: ${res!.examYear}',
                                            style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
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

                                    if (res != null)
                                      Text(
                                        '${res.branch} • Sem ${res.semester}${res.subjectCode != null ? " • ${res.subjectCode}" : ""}',
                                        style: TextStyle(color: Colors.grey.shade600, fontSize: 13),
                                      ),
                                    const SizedBox(height: 14),

                                    // Action Buttons
                                    Row(
                                      children: [
                                        Expanded(
                                          child: OutlinedButton.icon(
                                            onPressed: () async {
                                              final url = Uri.parse(ApiConfig.documentFileUrl(doc.id));
                                              if (await canLaunchUrl(url)) {
                                                await launchUrl(url, mode: LaunchMode.externalApplication);
                                              }
                                            },
                                            icon: const Icon(Icons.picture_as_pdf, size: 18),
                                            label: const Text('Open PDF'),
                                            style: OutlinedButton.styleFrom(
                                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                                            ),
                                          ),
                                        ),
                                        const SizedBox(width: 8),
                                        Expanded(
                                          child: ElevatedButton.icon(
                                            onPressed: () => _showAiSummary(doc),
                                            icon: const Icon(Icons.auto_awesome, size: 18),
                                            label: const Text('AI Summary'),
                                            style: ElevatedButton.styleFrom(
                                              backgroundColor: Colors.purple.shade50,
                                              foregroundColor: Colors.purple.shade900,
                                              elevation: 0,
                                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                                            ),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ],
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

  Widget _buildTypeFilterChip(String typeKey, String label) {
    final isSelected = _selectedType == typeKey;
    return ChoiceChip(
      label: Text(label),
      selected: isSelected,
      selectedColor: Colors.blueAccent.withOpacity(0.18),
      labelStyle: TextStyle(
        color: isSelected ? Colors.blueAccent : Colors.grey.shade700,
        fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
        fontSize: 12,
      ),
      onSelected: (val) {
        if (val) {
          setState(() => _selectedType = typeKey);
          _loadResources();
        }
      },
    );
  }
}
