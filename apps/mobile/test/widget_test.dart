import 'package:flutter_test/flutter_test.dart';
import 'package:terraforge_mobile/main.dart';

void main() {
  testWidgets('app boots to login route', (tester) async {
    await tester.pumpWidget(const TerraforgeApp());
    expect(find.text('Terraforge Labs'), findsOneWidget);
  });
}