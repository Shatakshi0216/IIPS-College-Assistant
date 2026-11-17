/// ==============================================================================
/// FILE: lib/screens/upload_screen.dart
/// PURPOSE: Official College PDF Document Upload interface (Faculty/Admin only).
///          Includes Upload tab and Manage Documents tab with delete capability.
/// ==============================================================================

import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import '../constants/academic_programs.dart';
import '../models/user_model.dart';
import '../models/document_model.dart';
import '../services/document_service.dart';

class UploadScreen extends StatefulWidget {
  final UserModel user;
  final VoidCallback? onUploadSuccess;

  const UploadScreen({
    super.key,
    required this.user,
    this.onUploadSuccess,
  });

  @override
  State<UploadScreen> createState() => _UploadScreenState();
}

class _UploadScreenState extends State<UploadScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final _formKey = GlobalKey<FormState>();
  final DocumentService _docService = DocumentService();

  final _titleController = TextEditingController();
  String _category = 'notice';
  String? _selectedFilePath;
  String? _selectedFileName;

  // Academic resource fields
  String _branch = 'ALL';
  int _year = 1;
  int _semester = 1;
  final _subjectNameController = TextEditingController();
  final _subjectCodeController = TextEditingController();
  final _examYearController = TextEditingController(text: "2024");

  bool _isUploading = false;
  String? _statusMessage;
  bool _isSuccess = false;

  // Manage tab state
  List<DocumentModel> _allDocuments = [];
  bool _isLoadingDocs = false;
  bool _manageLoaded = false;

  final List<String> _categories = [
    'notice',
    'circular',
    'rule',
    'syllabus',
    'question_paper',
  ];

  final List<String> _branches = uploadPrograms;
  final List<int> _semesters = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _tabController.addListener(() {
      if (_tabController.index == 1 && !_manageLoaded) {
        _loadAllDocuments();
      }
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    _titleController.dispose();
    _subjectNameController.dispose();
    _subjectCodeController.dispose();
    _examYearController.dispose();
    super.dispose();
  }

  Future<void> _loadAllDocuments() async {
    setState(() => _isLoadingDocs = true);
    final docs = await _docService.getAllDocuments();
    setState(() {
      _allDocuments = docs;
      _isLoadingDocs = false;
      _manageLoaded = true;
    });
  }

  Future<void> _pickFile() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf'],
    );
    if (!mounted) return;
    if (result != null && result.files.single.path != null) {
      setState(() {
        _selectedFilePath = result.files.single.path!;
        _selectedFileName = result.files.single.name;
        if (_titleController.text.trim().isEmpty) {
          _titleController.text =
              _selectedFileName!.replaceAll('.pdf', '').replaceAll('_', ' ');
        }
      });
    }
  }

  bool get _isAcademic =>
      _category == 'syllabus' || _category == 'question_paper';

  Future<void> _handleUpload() async {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedFilePath == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select a PDF document first!')),
      );
      return;
    }

    setState(() {
      _isUploading = true;
      _statusMessage = 'Uploading PDF & processing with Gemini AI…';
      _isSuccess = false;
    });

    final examYr = int.tryParse(_examYearController.text.trim());

    final res = await _docService.uploadDocument(
      filePath: _selectedFilePath!,
      title: _titleController.text.trim(),
      category: _category,
      branch: _isAcademic ? _branch : (_category == 'notice' ? _branch : 'ALL'),
      year: _isAcademic ? _year : null,
      semester: _isAcademic ? _semester : null,
      subjectName: _isAcademic ? _subjectNameController.text.trim() : null,
      subjectCode: _isAcademic ? _subjectCodeController.text.trim() : null,
      examYear: _category == 'question_paper' ? examYr : null,
    );

    if (!mounted) return;
    setState(() => _isUploading = false);

    if (res['success'] == true) {
      setState(() {
        _isSuccess = true;
        _statusMessage =
            '✅ Document uploaded and AI-indexed successfully!';
        _selectedFilePath = null;
        _selectedFileName = null;
        _titleController.clear();
        _subjectNameController.clear();
        _subjectCodeController.clear();
        _manageLoaded = false; // force reload on next manage tab visit
      });
      widget.onUploadSuccess?.call();
    } else {
      setState(() {
        _isSuccess = false;
        _statusMessage = '❌ Upload failed: ${res['message']}';
      });
    }
  }

  Future<void> _confirmAndDelete(DocumentModel doc) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.warning_amber_rounded, color: Colors.red),
            SizedBox(width: 8),
            Text('Delete Document'),
          ],
        ),
        content: Text(
          'Permanently delete:\n\n"${doc.title}"\n\nThis cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            style:
                ElevatedButton.styleFrom(backgroundColor: Colors.red, foregroundColor: Colors.white),
            child: const Text('Delete'),
          ),
        ],
      ),
    );

    if (confirmed != true || !mounted) return;

    final result = await _docService.deleteDocument(doc.id);
    if (!mounted) return;

    if (result['success'] == true) {
      setState(() => _allDocuments.removeWhere((d) => d.id == doc.id));
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('✅ "${doc.title}" deleted.'),
          backgroundColor: Colors.green.shade700,
        ),
      );
      widget.onUploadSuccess?.call();
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('❌ Delete failed: ${result['message']}'),
          backgroundColor: Colors.red.shade700,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade50,
      appBar: AppBar(
        title: const Text(
          'Document Management',
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
        ),
        backgroundColor: Colors.white,
        elevation: 0,
        bottom: TabBar(
          controller: _tabController,
          labelColor: Colors.blueAccent,
          unselectedLabelColor: Colors.grey,
          indicatorColor: Colors.blueAccent,
          tabs: const [
            Tab(icon: Icon(Icons.upload_file), text: 'Upload'),
            Tab(icon: Icon(Icons.list_alt_outlined), text: 'Manage'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [_buildUploadTab(), _buildManageTab()],
      ),
    );
  }

  // ── Upload Tab ─────────────────────────────────────────────────────────────
  Widget _buildUploadTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // PDF picker
            GestureDetector(
              onTap: _isUploading ? null : _pickFile,
              child: Container(
                padding: const EdgeInsets.all(28),
                decoration: BoxDecoration(
                  color: _selectedFilePath != null
                      ? Colors.blue.shade50
                      : Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: _selectedFilePath != null
                        ? Colors.blueAccent
                        : Colors.grey.shade300,
                    width: 1.5,
                  ),
                ),
                child: Column(
                  children: [
                    Icon(
                      _selectedFilePath != null
                          ? Icons.picture_as_pdf
                          : Icons.cloud_upload_outlined,
                      size: 48,
                      color: _selectedFilePath != null
                          ? Colors.redAccent
                          : Colors.blueAccent,
                    ),
                    const SizedBox(height: 12),
                    Text(
                      _selectedFileName ?? 'Tap to select a PDF document',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.bold,
                        color: _selectedFilePath != null
                            ? Colors.black87
                            : Colors.grey.shade700,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      _selectedFilePath != null
                          ? 'PDF selected'
                          : 'Only .pdf files are supported',
                      style: TextStyle(fontSize: 12, color: Colors.grey.shade500),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),

            // Status banner
            if (_statusMessage != null)
              Container(
                padding: const EdgeInsets.all(12),
                margin: const EdgeInsets.only(bottom: 16),
                decoration: BoxDecoration(
                  color: _isSuccess
                      ? Colors.green.shade50
                      : Colors.red.shade50,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(
                    color: _isSuccess
                        ? Colors.green.shade200
                        : Colors.red.shade200,
                  ),
                ),
                child: Text(
                  _statusMessage!,
                  style: TextStyle(
                    color: _isSuccess
                        ? Colors.green.shade800
                        : Colors.red.shade800,
                    fontSize: 13,
                  ),
                ),
              ),

            // Category
            DropdownButtonFormField<String>(
              value: _category,
              decoration: InputDecoration(
                labelText: 'Document Category',
                border:
                    OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                filled: true,
                fillColor: Colors.white,
              ),
              items: _categories
                  .map((c) => DropdownMenuItem(
                        value: c,
                        child: Text(c.toUpperCase().replaceAll('_', ' ')),
                      ))
                  .toList(),
              onChanged: _isUploading
                  ? null
                  : (val) {
                      if (val != null) setState(() => _category = val);
                    },
            ),
            const SizedBox(height: 16),

            // Title
            TextFormField(
              controller: _titleController,
              decoration: InputDecoration(
                labelText: 'Document Title',
                hintText: 'e.g. ATKT Examination Form Nov 2026',
                prefixIcon: const Icon(Icons.title),
                border:
                    OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                filled: true,
                fillColor: Colors.white,
              ),
              validator: (v) =>
                  (v == null || v.trim().isEmpty) ? 'Please enter a title' : null,
            ),
            const SizedBox(height: 16),

            // Notice target programme field
            if (_category == 'notice') ...[
              const Divider(),
              const Text(
                'TARGET AUDIENCE',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1,
                  color: Colors.grey,
                ),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                value: _branch,
                decoration: InputDecoration(
                  labelText: 'Target Programme',
                  helperText: 'Select ALL to publish to every student in IIPS DAVV',
                  border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12)),
                  filled: true,
                  fillColor: Colors.white,
                ),
                items: _branches
                    .map((b) => DropdownMenuItem(
                          value: b,
                          child: Text(b == 'ALL' ? 'ALL Programmes (Whole College)' : b),
                        ))
                    .toList(),
                onChanged: _isUploading
                    ? null
                    : (v) {
                        if (v != null) setState(() => _branch = v);
                      },
              ),
              const SizedBox(height: 16),
            ],

            // Rules & Circulars announcement notice
            if (_category == 'rule' || _category == 'circular') ...[
              Container(
                padding: const EdgeInsets.all(12),
                margin: const EdgeInsets.only(bottom: 16),
                decoration: BoxDecoration(
                  color: Colors.blue.shade50,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: Colors.blue.shade200),
                ),
                child: Row(
                  children: [
                    Icon(Icons.info_outline, color: Colors.blue.shade700, size: 20),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Rules & Circulars are official college policies visible to all students across all programmes.',
                        style: TextStyle(fontSize: 12, color: Colors.blue.shade900),
                      ),
                    ),
                  ],
                ),
              ),
            ],

            // Academic resource fields (syllabus / question_paper only)
            if (_isAcademic) ...[
              const Divider(),
              const Text(
                'ACADEMIC CLASSIFICATION',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1,
                  color: Colors.grey,
                ),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      value: _branch,
                      decoration: InputDecoration(
                        labelText: 'Programme',
                        border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12)),
                        filled: true,
                        fillColor: Colors.white,
                      ),
                      items: _branches
                          .map((b) =>
                              DropdownMenuItem(value: b, child: Text(b)))
                          .toList(),
                      onChanged: _isUploading
                          ? null
                          : (v) {
                              if (v != null) setState(() => _branch = v);
                            },
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: DropdownButtonFormField<int>(
                      value: _semester,
                      decoration: InputDecoration(
                        labelText: 'Semester',
                        border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12)),
                        filled: true,
                        fillColor: Colors.white,
                      ),
                      items: _semesters
                          .map((s) => DropdownMenuItem(
                              value: s, child: Text('Sem $s')))
                          .toList(),
                      onChanged: _isUploading
                          ? null
                          : (v) {
                              if (v != null) setState(() => _semester = v);
                            },
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 14),
              // Year dropdown
              DropdownButtonFormField<int>(
                value: _year,
                decoration: InputDecoration(
                  labelText: 'Year',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  filled: true,
                  fillColor: Colors.white,
                ),
                items: [1, 2, 3, 4, 5]
                    .map((y) => DropdownMenuItem(value: y, child: Text('Year $y')))
                    .toList(),
                onChanged: _isUploading
                    ? null
                    : (v) {
                        if (v != null) setState(() => _year = v);
                      },
              ),
              const SizedBox(height: 14),
              TextFormField(
                controller: _subjectNameController,
                decoration: InputDecoration(
                  labelText: 'Subject Name',
                  hintText: 'e.g. Operating Systems',
                  border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12)),
                  filled: true,
                  fillColor: Colors.white,
                ),
                validator: (v) => (_isAcademic && (v == null || v.trim().isEmpty))
                    ? 'Enter subject name'
                    : null,
              ),
              const SizedBox(height: 14),
              if (_category == 'question_paper')
                TextFormField(
                  controller: _examYearController,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(
                    labelText: 'Examination Year',
                    hintText: 'e.g. 2024',
                    border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12)),
                    filled: true,
                    fillColor: Colors.white,
                  ),
                ),
              const SizedBox(height: 16),
            ],

            // Upload button
            ElevatedButton.icon(
              onPressed: _isUploading ? null : _handleUpload,
              icon: _isUploading
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                          color: Colors.white, strokeWidth: 2),
                    )
                  : const Icon(Icons.upload_file),
              label: Text(
                _isUploading ? 'Processing with AI…' : 'Upload & Process with AI',
                style:
                    const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.blueAccent,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12)),
                elevation: 0,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── Manage Tab ─────────────────────────────────────────────────────────────
  Widget _buildManageTab() {
    return Column(
      children: [
        Container(
          color: Colors.white,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '${_allDocuments.length} document(s) uploaded',
                style: TextStyle(color: Colors.grey.shade600, fontSize: 14),
              ),
              TextButton.icon(
                onPressed: _loadAllDocuments,
                icon: const Icon(Icons.refresh, size: 18),
                label: const Text('Refresh'),
              ),
            ],
          ),
        ),
        Expanded(
          child: _isLoadingDocs
              ? const Center(child: CircularProgressIndicator())
              : _allDocuments.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.folder_open_outlined,
                              size: 54, color: Colors.grey.shade400),
                          const SizedBox(height: 12),
                          Text(
                            'No documents yet',
                            style: TextStyle(
                                color: Colors.grey.shade600, fontSize: 16),
                          ),
                          const SizedBox(height: 8),
                          TextButton(
                            onPressed: _loadAllDocuments,
                            child: const Text('Load Documents'),
                          ),
                        ],
                      ),
                    )
                  : RefreshIndicator(
                      onRefresh: _loadAllDocuments,
                      child: ListView.builder(
                        padding: const EdgeInsets.all(12),
                        itemCount: _allDocuments.length,
                        itemBuilder: (context, idx) {
                          final doc = _allDocuments[idx];
                          return Card(
                            margin: const EdgeInsets.only(bottom: 10),
                            elevation: 0,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                              side: BorderSide(color: Colors.grey.shade200),
                            ),
                            child: ListTile(
                              contentPadding: const EdgeInsets.symmetric(
                                  horizontal: 16, vertical: 8),
                              leading: CircleAvatar(
                                backgroundColor: Colors.blue.shade50,
                                child: Icon(
                                  _categoryIcon(doc.category),
                                  color: Colors.blueAccent,
                                  size: 20,
                                ),
                              ),
                              title: Text(
                                doc.title,
                                style: const TextStyle(
                                    fontWeight: FontWeight.bold, fontSize: 14),
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                              ),
                              subtitle: Padding(
                                padding: const EdgeInsets.only(top: 4),
                                child: Wrap(
                                  spacing: 6,
                                  children: [
                                    _badge(
                                      doc.category
                                          .toUpperCase()
                                          .replaceAll('_', ' '),
                                      Colors.blue,
                                    ),
                                    if (doc.isProcessed)
                                      _badge('AI INDEXED', Colors.green),
                                  ],
                                ),
                              ),
                              trailing: IconButton(
                                icon: const Icon(Icons.delete_outline,
                                    color: Colors.red),
                                onPressed: () => _confirmAndDelete(doc),
                                tooltip: 'Delete',
                              ),
                            ),
                          );
                        },
                      ),
                    ),
        ),
      ],
    );
  }

  IconData _categoryIcon(String cat) {
    switch (cat) {
      case 'notice':
        return Icons.campaign_outlined;
      case 'circular':
        return Icons.info_outline;
      case 'rule':
        return Icons.gavel_outlined;
      case 'syllabus':
        return Icons.menu_book_outlined;
      case 'question_paper':
        return Icons.quiz_outlined;
      default:
        return Icons.description_outlined;
    }
  }

  Widget _badge(String label, MaterialColor color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: color.shade50,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        label,
        style: TextStyle(
            fontSize: 10, color: color.shade800, fontWeight: FontWeight.bold),
      ),
    );
  }
}
