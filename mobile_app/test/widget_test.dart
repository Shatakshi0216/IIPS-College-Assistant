
import 'package:flutter_test/flutter_test.dart';
import 'package:college_assistant/main.dart';

void main() {
  testWidgets('College Assistant app builds', (tester) async {
    await tester.pumpWidget(const CollegeAssistantApp());

    expect(find.byType(CollegeAssistantApp), findsOneWidget);
  });
}
