/// ==============================================================================
/// FILE: lib/screens/register_screen.dart
/// PURPOSE: Registration screen with dynamic Student and Faculty profile fields.
/// ==============================================================================

import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import 'main_navigation_screen.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();

  // Role toggle: "student" or "faculty"
  String _role = "student";

  // Common Fields
  final _fullNameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  // Student Fields
  String _branch = "MCA";
  int _year = 2;
  int _semester = 3;
  final _sectionController = TextEditingController(text: "A");
  final _cgpaController = TextEditingController(text: "8.0");
  final _rollNumberController = TextEditingController();

  // Faculty Fields
  final _deptController = TextEditingController(text: "International Institute of Professional Studies");
  final _designationController = TextEditingController(text: "Faculty Member");
  final _employeeIdController = TextEditingController();

  final AuthService _authService = AuthService();
  bool _isLoading = false;
  String? _errorMessage;

  final List<String> _branches = ["MCA", "M.Tech", "MBA (MS)", "MBA (TA)", "BCA", "B.Com (Hons)", "IT", "CSE"];
  final List<int> _years = [1, 2, 3, 4, 5];
  final List<int> _semesters = [1, 2, 3, 4, 5, 6, 7, 8];

  @override
  void dispose() {
    _fullNameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _sectionController.dispose();
    _cgpaController.dispose();
    _rollNumberController.dispose();
    _deptController.dispose();
    _designationController.dispose();
    _employeeIdController.dispose();
    super.dispose();
  }

  Future<void> _handleRegister() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    Map<String, dynamic>? studentProfile;
    Map<String, dynamic>? facultyProfile;

    if (_role == "student") {
      final cgpaVal = double.tryParse(_cgpaController.text.trim()) ?? 0.0;
      studentProfile = {
        'branch': _branch,
        'year': _year,
        'semester': _semester,
        'section': _sectionController.text.trim(),
        'cgpa': cgpaVal,
        'roll_number': _rollNumberController.text.trim().isNotEmpty
            ? _rollNumberController.text.trim()
            : null,
      };
    } else {
      facultyProfile = {
        'department': _deptController.text.trim(),
        'designation': _designationController.text.trim(),
        'employee_id': _employeeIdController.text.trim().isNotEmpty
            ? _employeeIdController.text.trim()
            : null,
      };
    }

    final result = await _authService.register(
      email: _emailController.text,
      password: _passwordController.text,
      fullName: _fullNameController.text,
      role: _role,
      studentProfile: studentProfile,
      facultyProfile: facultyProfile,
    );

    setState(() => _isLoading = false);

    if (!mounted) return;

    if (result['success'] == true) {
      final user = result['user'];
      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(builder: (_) => MainNavigationScreen(user: user)),
        (route) => false,
      );
    } else {
      setState(() {
        _errorMessage = result['message'] ?? 'Registration failed.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade50,
      appBar: AppBar(
        title: const Text('Create Account'),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black87,
        elevation: 0,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Role Selector Segmented Control
                Container(
                  decoration: BoxDecoration(
                    color: Colors.grey.shade200,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  padding: const EdgeInsets.all(4),
                  child: Row(
                    children: [
                      Expanded(
                        child: GestureDetector(
                          onTap: () => setState(() => _role = "student"),
                          child: Container(
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            decoration: BoxDecoration(
                              color: _role == "student" ? Colors.white : Colors.transparent,
                              borderRadius: BorderRadius.circular(10),
                              boxShadow: _role == "student"
                                  ? [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 4)]
                                  : null,
                            ),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(
                                  Icons.school_outlined,
                                  size: 18,
                                  color: _role == "student" ? Colors.blueAccent : Colors.grey,
                                ),
                                const SizedBox(width: 8),
                                Text(
                                  'Student',
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    color: _role == "student" ? Colors.blueAccent : Colors.grey.shade700,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                      Expanded(
                        child: GestureDetector(
                          onTap: () => setState(() => _role = "faculty"),
                          child: Container(
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            decoration: BoxDecoration(
                              color: _role == "faculty" ? Colors.white : Colors.transparent,
                              borderRadius: BorderRadius.circular(10),
                              boxShadow: _role == "faculty"
                                  ? [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 4)]
                                  : null,
                            ),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(
                                  Icons.person_pin_outlined,
                                  size: 18,
                                  color: _role == "faculty" ? Colors.purple : Colors.grey,
                                ),
                                const SizedBox(width: 8),
                                Text(
                                  'Faculty / Admin',
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    color: _role == "faculty" ? Colors.purple : Colors.grey.shade700,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),

                // Error Banner
                if (_errorMessage != null)
                  Container(
                    padding: const EdgeInsets.all(12),
                    margin: const EdgeInsets.only(bottom: 16),
                    decoration: BoxDecoration(
                      color: Colors.red.shade50,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.red.shade200),
                    ),
                    child: Text(
                      _errorMessage!,
                      style: const TextStyle(color: Colors.red, fontSize: 13),
                    ),
                  ),

                // Common: Full Name
                TextFormField(
                  controller: _fullNameController,
                  decoration: InputDecoration(
                    labelText: 'Full Name',
                    prefixIcon: const Icon(Icons.person_outline),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    filled: true,
                    fillColor: Colors.white,
                  ),
                  validator: (v) => (v == null || v.trim().isEmpty) ? 'Enter your full name' : null,
                ),
                const SizedBox(height: 14),

                // Common: Email
                TextFormField(
                  controller: _emailController,
                  keyboardType: TextInputType.emailAddress,
                  decoration: InputDecoration(
                    labelText: 'College Email',
                    hintText: 'name@college.edu',
                    prefixIcon: const Icon(Icons.email_outlined),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    filled: true,
                    fillColor: Colors.white,
                  ),
                  validator: (v) {
                    if (v == null || v.trim().isEmpty) return 'Enter your email';
                    if (!v.contains('@')) return 'Enter a valid email';
                    return null;
                  },
                ),
                const SizedBox(height: 14),

                // Common: Password
                TextFormField(
                  controller: _passwordController,
                  obscureText: true,
                  decoration: InputDecoration(
                    labelText: 'Password (min 6 chars)',
                    prefixIcon: const Icon(Icons.lock_outline),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    filled: true,
                    fillColor: Colors.white,
                  ),
                  validator: (v) => (v == null || v.length < 6) ? 'Password must be at least 6 characters' : null,
                ),
                const SizedBox(height: 20),

                // Role Specific Fields Header
                Text(
                  _role == "student" ? "ACADEMIC PROFILE (FOR NOTICES)" : "FACULTY DETAILS",
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1,
                    color: Colors.grey.shade600,
                  ),
                ),
                const SizedBox(height: 12),

                // STUDENT SPECIFIC INPUTS
                if (_role == "student") ...[
                  Row(
                    children: [
                      // Branch Dropdown
                      Expanded(
                        flex: 3,
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
                          onChanged: (val) => setState(() => _branch = val!),
                        ),
                      ),
                      const SizedBox(width: 10),

                      // Year Dropdown
                      Expanded(
                        flex: 2,
                        child: DropdownButtonFormField<int>(
                          value: _year,
                          decoration: InputDecoration(
                            labelText: 'Year',
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                            filled: true,
                            fillColor: Colors.white,
                          ),
                          items: _years
                              .map((y) => DropdownMenuItem(value: y, child: Text('$y Yr')))
                              .toList(),
                          onChanged: (val) => setState(() => _year = val!),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),

                  Row(
                    children: [
                      // Semester Dropdown
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
                          onChanged: (val) => setState(() => _semester = val!),
                        ),
                      ),
                      const SizedBox(width: 10),

                      // CGPA Field
                      Expanded(
                        child: TextFormField(
                          controller: _cgpaController,
                          keyboardType: const TextInputType.numberWithOptions(decimal: true),
                          decoration: InputDecoration(
                            labelText: 'CGPA (0 - 10)',
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                            filled: true,
                            fillColor: Colors.white,
                          ),
                          validator: (v) {
                            final n = double.tryParse(v ?? '');
                            if (n == null || n < 0.0 || n > 10.0) return '0.0 - 10.0';
                            return null;
                          },
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),

                  // Roll Number
                  TextFormField(
                    controller: _rollNumberController,
                    decoration: InputDecoration(
                      labelText: 'Roll Number / Enrollment No (Optional)',
                      hintText: 'e.g. 21CS104',
                      prefixIcon: const Icon(Icons.badge_outlined),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      filled: true,
                      fillColor: Colors.white,
                    ),
                  ),
                ],

                // FACULTY SPECIFIC INPUTS
                if (_role == "faculty") ...[
                  TextFormField(
                    controller: _deptController,
                    decoration: InputDecoration(
                      labelText: 'Department',
                      hintText: 'e.g. Computer Science',
                      prefixIcon: const Icon(Icons.apartment_outlined),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      filled: true,
                      fillColor: Colors.white,
                    ),
                    validator: (v) => (v == null || v.trim().isEmpty) ? 'Enter department' : null,
                  ),
                  const SizedBox(height: 14),

                  TextFormField(
                    controller: _designationController,
                    decoration: InputDecoration(
                      labelText: 'Designation',
                      hintText: 'e.g. Assistant Professor',
                      prefixIcon: const Icon(Icons.work_outline),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      filled: true,
                      fillColor: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 14),

                  TextFormField(
                    controller: _employeeIdController,
                    decoration: InputDecoration(
                      labelText: 'Employee ID (Optional)',
                      hintText: 'e.g. FAC-CS-101',
                      prefixIcon: const Icon(Icons.badge_outlined),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      filled: true,
                      fillColor: Colors.white,
                    ),
                  ),
                ],

                const SizedBox(height: 28),

                // Register Button
                ElevatedButton(
                  onPressed: _isLoading ? null : _handleRegister,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blueAccent,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangle.circular(12),
                    elevation: 0,
                  ),
                  child: _isLoading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                        )
                      : const Text(
                          'Create Account',
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                        ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
