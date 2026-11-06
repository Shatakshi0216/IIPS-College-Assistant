/// ==============================================================================
/// FILE: lib/screens/ai_chat_screen.dart
/// PURPOSE: RAG-based AI College Assistant chat screen powered by Google Gemini.
///          Features markdown answers and verifiable document source citations.
/// ==============================================================================

import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../models/user_model.dart';
import '../models/chat_message_model.dart';
import '../services/chat_service.dart';

class AiChatScreen extends StatefulWidget {
  final UserModel user;

  const AiChatScreen({super.key, required this.user});

  @override
  State<AiChatScreen> createState() => _AiChatScreenState();
}

class _AiChatScreenState extends State<AiChatScreen> {
  final ChatService _chatService = ChatService();
  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  final List<ChatMessageModel> _messages = [];
  bool _isSending = false;

  final List<String> _quickPrompts = [
    "What is the attendance requirement?",
    "When is the TCS placement deadline?",
    "Who is eligible for campus recruitment?",
    "What are the mid-term exam rules?",
  ];

  @override
  void initState() {
    super.initState();
    // Welcome message from the college assistant
    _messages.add(
      ChatMessageModel(
        text: "Hello **${widget.user.fullName}**! 👋\n\nI am your official **IIPS DAVV** AI Assistant. I answer questions strictly grounded in official documents of International Institute of Professional Studies, DAVV.\n\nHow can I help you today?",
        isUser: false,
        timestamp: DateTime.now(),
      ),
    );
  }

  @override
  void dispose() {
    _textController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _sendMessage(String query) async {
    if (query.trim().isEmpty || _isSending) return;

    final userMessage = ChatMessageModel(
      text: query.trim(),
      isUser: true,
      timestamp: DateTime.now(),
    );

    // Placeholder loading message for AI
    final loadingMessage = ChatMessageModel(
      text: "Searching official college documents...",
      isUser: false,
      timestamp: DateTime.now(),
      isLoading: true,
    );

    setState(() {
      _messages.add(userMessage);
      _messages.add(loadingMessage);
      _isSending = true;
    });

    _textController.clear();
    _scrollToBottom();

    // Call RAG API
    final result = await _chatService.askQuestion(query);

    setState(() {
      _messages.removeLast(); // remove loading message
      _messages.add(
        ChatMessageModel(
          text: result['answer'] ?? 'Sorry, I could not process your query.',
          isUser: false,
          timestamp: DateTime.now(),
          sources: (result['sources'] as List<SourceCitationModel>?) ?? [],
        ),
      );
      _isSending = false;
    });

    _scrollToBottom();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade100,
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: Colors.blueAccent.withOpacity(0.12),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.smart_toy, color: Colors.blueAccent, size: 20),
            ),
            const SizedBox(width: 10),
            const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'AI College Assistant',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
                Text(
                  'RAG • Grounded in Official Documents',
                  style: TextStyle(fontSize: 11, color: Colors.green),
                ),
              ],
            ),
          ],
        ),
        backgroundColor: Colors.white,
        elevation: 0,
      ),
      body: Column(
        children: [
          // Quick Prompts Bar
          Container(
            color: Colors.white,
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: Row(
                children: _quickPrompts.map((p) {
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ActionChip(
                      label: Text(p, style: const TextStyle(fontSize: 12)),
                      backgroundColor: Colors.grey.shade50,
                      side: BorderSide(color: Colors.grey.shade300),
                      onPressed: () => _sendMessage(p),
                    ),
                  );
                }).toList(),
              ),
            ),
          ),

          // Messages List
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length,
              itemBuilder: (context, idx) {
                final msg = _messages[idx];
                return _buildMessageBubble(msg);
              },
            ),
          ),

          // Message Input Bar
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.04),
                  offset: const Offset(0, -2),
                  blurRadius: 4,
                ),
              ],
            ),
            child: SafeArea(
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _textController,
                      textInputAction: TextInputAction.send,
                      onSubmitted: _sendMessage,
                      decoration: InputDecoration(
                        hintText: 'Ask anything about rules, notices, deadlines...',
                        hintStyle: TextStyle(color: Colors.grey.shade400, fontSize: 14),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(24),
                          borderSide: BorderSide(color: Colors.grey.shade300),
                        ),
                        filled: true,
                        fillColor: Colors.grey.shade50,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filled(
                    onPressed: _isSending ? null : () => _sendMessage(_textController.text),
                    icon: _isSending
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                          )
                        : const Icon(Icons.send_rounded, size: 20),
                    style: IconButton.styleFrom(
                      backgroundColor: Colors.blueAccent,
                      foregroundColor: Colors.white,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(ChatMessageModel msg) {
    final isUser = msg.isUser;

    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        mainAxisAlignment: isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!isUser) ...[
            Container(
              margin: const EdgeInsets.only(right: 8, top: 4),
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: Colors.blueAccent.withOpacity(0.12),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.smart_toy, size: 16, color: Colors.blueAccent),
            ),
          ],
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: isUser ? Colors.blueAccent : Colors.white,
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(16),
                  topRight: const Radius.circular(16),
                  bottomLeft: isUser ? const Radius.circular(16) : const Radius.circular(4),
                  bottomRight: isUser ? const Radius.circular(4) : const Radius.circular(16),
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.04),
                    blurRadius: 4,
                    offset: const Offset(0, 1),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (msg.isLoading)
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const SizedBox(
                          width: 14,
                          height: 14,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.blueAccent),
                        ),
                        const SizedBox(width: 10),
                        Text(
                          msg.text,
                          style: TextStyle(color: Colors.grey.shade600, fontSize: 13, fontStyle: FontStyle.italic),
                        ),
                      ],
                    )
                  else if (isUser)
                    Text(
                      msg.text,
                      style: const TextStyle(color: Colors.white, fontSize: 14),
                    )
                  else
                    MarkdownBody(
                      data: msg.text,
                      styleSheet: MarkdownStyleSheet(
                        p: const TextStyle(fontSize: 14, height: 1.4, color: Color(0xFF1E293B)),
                        strong: const TextStyle(fontWeight: FontWeight.bold, color: Colors.black),
                      ),
                    ),

                  // Source Citations
                  if (!isUser && msg.sources.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    const Divider(height: 1),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        const Icon(Icons.verified_outlined, size: 14, color: Colors.blueAccent),
                        const SizedBox(width: 4),
                        Text(
                          'OFFICIAL SOURCES CITED (${msg.sources.length})',
                          style: const TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 0.5,
                            color: Colors.blueAccent,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    ...msg.sources.map((s) {
                      return Container(
                        margin: const EdgeInsets.only(top: 4),
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: Colors.blue.shade50.withOpacity(0.5),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '• ${s.documentTitle}',
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 12,
                                color: Color(0xFF1E293B),
                              ),
                            ),
                            if (s.snippet.isNotEmpty)
                              Padding(
                                padding: const EdgeInsets.only(top: 2, left: 6),
                                child: Text(
                                  '"${s.snippet}"',
                                  style: TextStyle(fontSize: 11, color: Colors.grey.shade700, fontStyle: FontStyle.italic),
                                ),
                              ),
                          ],
                        ),
                      );
                    }),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
