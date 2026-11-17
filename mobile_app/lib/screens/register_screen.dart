
import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import '../constants/academic_programs.dart';
import 'main_navigation_screen.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();

  final _fullNameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();

  String _branch = academicPrograms.first;
  int _year = 2;
  int _semester = 3;

  final _sectionController = TextEditingController(text: "A");
  final _cgpaController = TextEditingController(text: "8.0");
  final _rollNumberController = TextEditingController();

  final AuthService _authService = AuthService();

  bool _isLoading = false;
  bool _obscurePassword = true;
  bool _obscureConfirmPassword = true;
  String? _errorMessage;

  final List<String> _branches = academicPrograms;

  final List<int> _years = [1, 2, 3, 4, 5];
  final List<int> _semesters = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

  @override
  void dispose() {
    _fullNameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _sectionController.dispose();
    _cgpaController.dispose();
    _rollNumberController.dispose();
    super.dispose();
  }

  Future<void> _handleRegister() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final studentProfile = {
      'branch': _branch,
      'year': _year,
      'semester': _semester,
      'section': _sectionController.text.trim(),
      'cgpa': double.tryParse(_cgpaController.text.trim()) ?? 0.0,
      'roll_number': _rollNumberController.text.trim().isNotEmpty
          ? _rollNumberController.text.trim()
          : null,
    };

    final result = await _authService.register(
      email: _emailController.text.trim(),
      password: _passwordController.text,
      fullName: _fullNameController.text.trim(),
      role: "student",
      studentProfile: studentProfile,
      facultyProfile: null,
    );

    if (!mounted) return;

    setState(() => _isLoading = false);

    if (result['success'] == true) {
      final user = result['user'];
      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(
          builder: (_) => MainNavigationScreen(user: user),
        ),
        (route) => false,
      );
    } else {
      setState(() {
        _errorMessage = result['message'] ?? 'Registration failed.';
      });
    }
  }

  InputDecoration _decoration(String label, IconData icon) {
    return InputDecoration(
      labelText: label,
      prefixIcon: Icon(icon),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      filled: true,
      fillColor: Colors.white,
    );
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
          padding: const EdgeInsets.symmetric(
            horizontal: 24,
            vertical: 16,
          ),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  'STUDENT REGISTRATION',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1,
                    color: Colors.grey.shade600,
                  ),
                ),
                const SizedBox(height: 20),

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
                      style: const TextStyle(
                        color: Colors.red,
                        fontSize: 13,
                      ),
                    ),
                  ),

                TextFormField(
                  controller: _fullNameController,
                  decoration: _decoration(
                    'Full Name',
                    Icons.person_outline,
                  ),
                  validator: (v) =>
                      (v == null || v.trim().isEmpty)
                          ? 'Enter your full name'
                          : null,
                ),
                const SizedBox(height: 14),

                TextFormField(
                  controller: _emailController,
                  keyboardType: TextInputType.emailAddress,
                  decoration: _decoration(
                    'College Email',
                    Icons.email_outlined,
                  ),
                  validator: (v) {
                    if (v == null || v.trim().isEmpty) {
                      return 'Enter your email';
                    }
                    if (!v.contains('@') || !v.contains('.')) {
                      return 'Enter a valid email';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 14),

                TextFormField(
                  controller: _passwordController,
                  obscureText: _obscurePassword,
                  decoration: _decoration(
                    'Password (min 6 chars)',
                    Icons.lock_outline,
                  ).copyWith(
                    suffixIcon: IconButton(
                      icon: Icon(
                        _obscurePassword
                            ? Icons.visibility_outlined
                            : Icons.visibility_off_outlined,
                      ),
                      onPressed: () {
                        setState(() {
                          _obscurePassword = !_obscurePassword;
                        });
                      },
                    ),
                  ),
                  validator: (v) =>
                      (v == null || v.length < 6)
                          ? 'Password must be at least 6 characters'
                          : null,
                ),
                const SizedBox(height: 14),

                TextFormField(
                  controller: _confirmPasswordController,
                  obscureText: _obscureConfirmPassword,
                  decoration: _decoration(
                    'Confirm Password',
                    Icons.lock_outline,
                  ).copyWith(
                    suffixIcon: IconButton(
                      icon: Icon(
                        _obscureConfirmPassword
                            ? Icons.visibility_outlined
                            : Icons.visibility_off_outlined,
                      ),
                      onPressed: () {
                        setState(() {
                          _obscureConfirmPassword =
                              !_obscureConfirmPassword;
                        });
                      },
                    ),
                  ),
                  validator: (v) {
                    if (v == null || v.isEmpty) {
                      return 'Please confirm your password';
                    }
                    if (v != _passwordController.text) {
                      return 'Passwords do not match';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 20),

                Text(
                  'ACADEMIC PROFILE (FOR NOTICES)',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1,
                    color: Colors.grey.shade600,
                  ),
                ),
                const SizedBox(height: 12),

                Row(
                  children: [
                    Expanded(
                      flex: 3,
                      child: DropdownButtonFormField<String>(
                        value: _branch,
                        decoration: _decoration(
                          'Branch',
                          Icons.school_outlined,
                        ),
                        items: _branches
                            .map((b) => DropdownMenuItem(
                                  value: b,
                                  child: Text(b),
                                ))
                            .toList(),
                        onChanged: (val) {
                          if (val != null) {
                            setState(() => _branch = val);
                          }
                        },
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      flex: 2,
                      child: DropdownButtonFormField<int>(
                        value: _year,
                        decoration: _decoration(
                          'Year',
                          Icons.calendar_today_outlined,
                        ),
                        items: _years
                            .map((y) => DropdownMenuItem(
                                  value: y,
                                  child: Text('$y Yr'),
                                ))
                            .toList(),
                        onChanged: (val) {
                          if (val != null) {
                            setState(() => _year = val);
                          }
                        },
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),

                Row(
                  children: [
                    Expanded(
                      child: DropdownButtonFormField<int>(
                        value: _semester,
                        decoration: _decoration(
                          'Semester',
                          Icons.menu_book_outlined,
                        ),
                        items: _semesters
                            .map((s) => DropdownMenuItem(
                                  value: s,
                                  child: Text('Sem $s'),
                                ))
                            .toList(),
                        onChanged: (val) {
                          if (val != null) {
                            setState(() => _semester = val);
                          }
                        },
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: TextFormField(
                        controller: _cgpaController,
                        keyboardType:
                            const TextInputType.numberWithOptions(
                          decimal: true,
                        ),
                        decoration: _decoration(
                          'CGPA (0 - 10)',
                          Icons.grade_outlined,
                        ),
                        validator: (v) {
                          final n = double.tryParse(v ?? '');
                          if (n == null || n < 0 || n > 10) {
                            return 'Enter 0.0 - 10.0';
                          }
                          return null;
                        },
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),

                TextFormField(
                  controller: _rollNumberController,
                  decoration: _decoration(
                    'Roll Number / Enrollment No (Optional)',
                    Icons.badge_outlined,
                  ),
                ),
                const SizedBox(height: 28),

                ElevatedButton(
                  onPressed: _isLoading ? null : _handleRegister,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blueAccent,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    elevation: 0,
                  ),
                  child: _isLoading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(
                            color: Colors.white,
                            strokeWidth: 2,
                          ),
                        )
                      : const Text(
                          'Create Student Account',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
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
