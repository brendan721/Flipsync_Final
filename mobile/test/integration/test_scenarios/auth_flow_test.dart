import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/material.dart';
import '../test_utils/test_data.dart';
import '../test_utils/test_helpers.dart';

Future<void> runAuthenticationTests(WidgetTester tester) async {
  group('Authentication Flow Tests', () {
    testWidgets('Login flow', (tester) async {
      // Find login form
      final emailField = find.byKey(const Key('email_field'));
      final passwordField = find.byKey(const Key('password_field'));
      final loginButton = find.byKey(const Key('login_button'));

      // Enter credentials
      await tester.enterText(emailField, TestData.validEmail);
      await tester.enterText(passwordField, TestData.validPassword);
      await tester.pumpAndSettle();

      // Tap login button
      await tester.tap(loginButton);
      await tester.pumpAndSettle();

      // Verify successful login
      expect(find.text('Dashboard'), findsOneWidget);
      expect(find.text('Welcome back'), findsOneWidget);
    });

    testWidgets('Invalid login attempt', (tester) async {
      // Find login form
      final emailField = find.byKey(const Key('email_field'));
      final passwordField = find.byKey(const Key('password_field'));
      final loginButton = find.byKey(const Key('login_button'));

      // Enter invalid credentials
      await tester.enterText(emailField, TestData.invalidEmail);
      await tester.enterText(passwordField, TestData.invalidPassword);
      await tester.pumpAndSettle();

      // Tap login button
      await tester.tap(loginButton);
      await tester.pumpAndSettle();

      // Verify error message
      expect(find.text('Invalid credentials'), findsOneWidget);
    });

    testWidgets('Password reset flow', (tester) async {
      // Find reset password link
      final resetLink = find.byKey(const Key('reset_password_link'));

      // Tap reset link
      await tester.tap(resetLink);
      await tester.pumpAndSettle();

      // Find email field
      final emailField = find.byKey(const Key('reset_email_field'));
      final submitButton = find.byKey(const Key('reset_submit_button'));

      // Enter email
      await tester.enterText(emailField, TestData.validEmail);
      await tester.pumpAndSettle();

      // Tap submit
      await tester.tap(submitButton);
      await tester.pumpAndSettle();

      // Verify confirmation message
      expect(find.text('Reset instructions sent'), findsOneWidget);
    });

    testWidgets('Logout flow', (tester) async {
      // Ensure logged in
      await TestHelpers.loginUser(tester);

      // Find logout button
      final menuButton = find.byKey(const Key('menu_button'));
      await tester.tap(menuButton);
      await tester.pumpAndSettle();

      final logoutButton = find.byKey(const Key('logout_button'));
      await tester.tap(logoutButton);
      await tester.pumpAndSettle();

      // Verify logged out state
      expect(find.text('Login'), findsOneWidget);
    });

    testWidgets('Session persistence', (tester) async {
      // Login
      await TestHelpers.loginUser(tester);

      // Restart app
      await TestHelpers.restartApp(tester);

      // Verify still logged in
      expect(find.text('Dashboard'), findsOneWidget);
    });

    testWidgets('Token refresh', (tester) async {
      // Login
      await TestHelpers.loginUser(tester);

      // Simulate token expiration
      await TestHelpers.simulateTokenExpiration();

      // Perform authenticated action
      final profileButton = find.byKey(const Key('profile_button'));
      await tester.tap(profileButton);
      await tester.pumpAndSettle();

      // Verify token refresh
      expect(find.text('Profile'), findsOneWidget);
    });
  });
}
