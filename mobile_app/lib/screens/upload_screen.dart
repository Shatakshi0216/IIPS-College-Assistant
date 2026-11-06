/// ==============================================================================
/// FILE: lib/screens/upload_screen.dart
/// PURPOSE: Official College PDF Document Upload interface (Faculty/Admin only).
///          Triggers Gemini text understanding and RAG vector indexing.
/// ==============================================================================

import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import '../models/user_model.dart';
import '../services/document_service.dart';

class UploadScreen extends StatefulWidget {
  final UserModel user;

  const UploadScreen({super.key, required this.user});

  @override
  State<UploadScreen> createState() => _UploadScreenState();
}

class _UploadScreenState extends State<UploadScreen> {
  final _formKey = GlobalKey<FormState>();
  final DocumentService _docService = DocumentService();

  final _titleController = TextEditingController();
  String _category = 'notice'; // notice, syllabus, question_paper, circular, rule
  String? _selectedFilePath;
  String? _selectedFileName;

  // Optional Academic Fields
  String _branch = 'CSE';
  int _year = 3;
  int _semester = 5;
  final _subjectNameController = TextEditingController();
  final _subjectCodeController = TextEditingController();
  final _examYearController = TextEditingController(text: "2024");

  bool _isUploading = false;
  String? _statusMessage;
  bool _isSuccess = false;

  final List<String> _categories = [
    'notice',
    'syllabus',
    'question_paper',
    'circular',
    'rule',
  ];

  final List<String> _branches = ['CSE', 'IT', 'ECE', 'ME', 'CE', 'EE', 'ALL'];
  final List<int> _years = [1, 2, 3, 4];
  final List<int> _semesters = [1, 2, 3, 4, 5, 6, 7, 8];

  @override
  void dispose() {
    _titleController.dispose();
    _subjectNameController.dispose();
    _subjectCodeController.dispose();
    _examYearController.dispose();
    super.dispose();
  }

  Future<void> _pickFile() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf'],
    );

    if (result != null && result.files.single.path != null) {
      setState(() {
        _selectedFilePath = result.files.single.path!;
        _selectedFileName = result.files.single.name;
        // Default title to filename if title is blank
        if (_titleController.text.trim().isEmpty) {
          _titleController.text = _selectedFileName!.replaceAll('.pdf', '').replaceAll('_', ' ');
        }
      });
    }
  }

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
      _statusMessage = "Uploading PDF & processing with Gemini AI...";
      _isSuccess = false;
    });

    final examYr = int.tryParse(_examYearController.text.trim());

    final res = await _docService.uploadDocument(
      filePath: _selectedFilePath!,
      title: _titleController.text.trim(),
      category: _category,
      branch: _category != 'notice' ? _branch : null,
      year: _category != 'notice' ? _year : null,
      semester: _category != 'notice' ? _semester : null,
      subjectName: _category != 'notice' ? _subjectNameController.text.trim() : null,
      subjectCode: _category != 'notice' ? _subjectCodeController.text.trim() : null,
      examYear: _category == 'question_paper' ? examYr : null,
    );

    setState(() => _isUploading = false);

    if (!mounted) return;

    if (res['success'] == true) {
      setState(() {
        _isSuccess = true;
        _statusMessage = " Document successfully uploaded, parsed by Gemini & indexed into RAG!";
        _selectedFilePath = null;
        _selectedFileName = null;
        _titleController.clear();
        _subjectNameController.clear();
      });
    } else {
      setState(() {
        _isSuccess = false;
        _statusMessage = "❌ Upload failed: ${res['message']}";
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final isAcademic = _category == 'syllabus' || _category == 'question_paper';

    return Scaffold(
      backgroundColor: Colors.grey.shade50,
      appBar: AppBar(
        title: const Text(
          'Upload Official Document',
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
        ),
        backgroundColor: Colors.white,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // PDF Picker Area
              GestureDetector(
                onTap: _isUploading ? null : _pickFile,
                child: Container(
                  padding: const EdgeInsets.all(28),
                  decoration: BoxDecoration(
                    color: _selectedFilePath != null ? Colors.blue.shade50 : Colors.white,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: _selectedFilePath != null ? Colors.blueAccent : Colors.grey.shade300,
                      width: 1.5,
                      style: BorderStyle.solid,
                    ),
                  ),
                  child: Column(
                    children: [
                      Icon(
                        _selectedFilePath != null ? Icons.picture_as_pdf : Icons.cloud_upload_outlined,
                        size: 48,
                        color: _selectedFilePath != null ? Colors.redAccent : Colors.blueAccent,
                      ),
                      const SizedBox(height: 12),
                      Text(
                        _selectedFileName ?? 'Tap to select College PDF document',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.bold,
                          color: _selectedFilePath != null ? Colors.black87 : Colors.grey.shade700,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        _selectedFilePath != null ? 'PDF Selected' : 'Supported format: .pdf only',
                        style: TextStyle(fontSize: 12, color: Colors.grey.shade500),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 20),

              // Status Banner
              if (_statusMessage != null)
                Container(
                  padding: const EdgeInsets.all(12),
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: _isSuccess ? Colors.green.shade50 : Colors.red.shade50,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(
                      color: _isSuccess ? Colors.green.shade200 : Colors.red.shade200,
                    ),
                  ),
                  child: Text(
                    _statusMessage!,
                    style: TextStyle(
                      color: _isSuccess ? Colors.green.shade800 : Colors.red.shade800,
                      fontSize: 13,
                    ),
                  ),
                ),

              // Category Selector
              DropdownButtonFormField<String>(
                value: _category,
                decoration: InputDecoration(
                  labelText: 'Document Category',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  filled: true,
                  fillColor: Colors.white,
                ),
                items: _categories.map((c) {
                  return DropdownMenuItem(
                    value: c,
                    child: Text(c.toUpperCase().replaceAll('_', ' ')),
                  );
                }).toList(),
                onChanged: (val) => setState(() => _category = val!),
              ),
              const SizedBox(height: 16),

              // Document Title
              TextFormField(
                controller: _titleController,
                decoration: InputDecoration(
                  labelText: 'Document Title',
                  hintText: 'e.g. TCS Campus Recruitment Drive 2026',
                  prefixIcon: const Icon(Icons.title),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  filled: true,
                  fillColor: Colors.white,
                ),
                validator: (v) => (v == null || v.trim().isEmpty) ? 'Please enter a title' : null,
              ),
              const SizedBox(height: 16),

              // ACADEMIC FIELDS (If Syllabus or Past Paper)
              if (isAcademic) ...[
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
                          labelText: 'Branch',
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                          filled: true,
                          fillColor: Colors.white,
                        ),
                        items: _branches
                            .map((b) => DropdownMenuItem(value: b, child: Text(b)))
                            .toList(),
                        onChanged: (v) => setState(() => _branch = v!),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: DropdownButtonFormField<int>(
                        value: _semester,
                        decoration: InputDecoration(
                          labelText: 'Semester',
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                          filled: true,
                          fillColor: Colors.white,
                        ),
                        items: _semesters
                            .map((s) => DropdownMenuItem(value: s, child: Text('Sem $s')))
                            .toList(),
                        onChanged: (v) => setState(() => _semester = v!),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),

                TextFormField(
                  controller: _subjectNameController,
                  decoration: InputDecoration(
                    labelText: 'Subject Name',
                    hintText: 'e.g. Operating Systems',
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    filled: true,
                    fillColor: Colors.white,
                  ),
                  validator: (v) => (isAcademic && (v == null || v.trim().isEmpty)) ? 'Enter subject name' : null,
                ),
                const SizedBox(height: 14),

                if (_category == 'question_paper')
                  TextFormField(
                    controller: _examYearController,
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(
                      labelText: 'Examination Year',
                      hintText: 'e.g. 2024',
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      filled: true,
                      fillColor: Colors.white,
                    ),
                  ),
                const SizedBox(height: 16),
              ],

              // Upload Button
              ElevatedButton.icon(
                onPressed: _isUploading ? null : _handleUpload,
                icon: _isUploading
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                      )
                    : const Icon(Icons.upload_file),
                label: Text(
                  _isUploading ? 'Processing with AI...' : 'Upload & Process with AI',
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blueAccent,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangle.circular(12),
                  elevation: 0,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
