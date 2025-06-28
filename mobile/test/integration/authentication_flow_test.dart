import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:mocktail/mocktail.dart';

import 'package:flipsync/app.dart';
import 'package:flipsync/core/auth/auth_service.dart';
import 'package:flipsync/core/auth/auth_guard.dart';
import 'package:flipsync/core/state/auth_state.dart';
import 'package:flipsync/features/welcome/welcome_screen.dart';
import 'package:flipsync/features/onboarding/how_flipsync_works_screen.dart';
import 'package:flipsync/features/auth/login_screen.dart';
import 'package:flipsync/features/dashboard/presentation/screens/sales_optimization_dashboard.dart';
import 'package:flipsync/features/navigation/navigation_service.dart';

// Mock classes
class MockAuthService extends Mock implements AuthService {}

class MockAuthState extends Mock implements AuthState {}

class MockNavigationService extends Mock implements NavigationService {}

void main() {
  group('Authentication Flow Integration Tests', () {
    late MockAuthService mockAuthService;
    late MockAuthState mockAuthState;
    late MockNavigationService mockNavigationService;

    setUp(() {
      // Reset GetIt before each test
      GetIt.instance.reset();

      mockAuthService = MockAuthService();
      mockAuthState = MockAuthState();
      mockNavigationService = MockNavigationService();

      // Register mocks
      GetIt.instance.registerSingleton<AuthService>(mockAuthService);
      GetIt.instance.registerSingleton<AuthState>(mockAuthState);
      GetIt.instance.registerSingleton<NavigationService>(mockNavigationService);

      // Setup default mock behaviors
      when(() => mockAuthState.isAuthenticated).thenReturn(false);
      when(() => mockAuthState.authToken).thenReturn(null);
      when(() => mockAuthState.clearAllAuthData()).thenAnswer((_) async {});
      when(() => mockAuthState.silentLogin()).thenAnswer((_) async => false);
      when(() => mockAuthService.login(any(), any()))
          .thenAnswer((_) async => ApiResult.success(AuthData(
                accessToken: 'test_token',
                refreshToken: 'test_refresh',
                userId: 'test_user',
              )));
      when(() => mockAuthService.getAccessToken()).thenAnswer((_) async => 'test_token');

      // Setup NavigationService mock
      when(() => mockNavigationService.navigateToAndClearStack(any())).thenAnswer((_) async {});
    });

    tearDown(() {
      GetIt.instance.reset();
    });

    testWidgets('Welcome screen shows Get Started and Sign In buttons',
        (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: const WelcomeScreen(),
        ),
      );

      // Verify welcome screen elements
      expect(find.text('FlipSync'), findsOneWidget);
      expect(find.text('Get Started'), findsOneWidget);
      expect(find.text('Sign In'), findsOneWidget);
    });

    testWidgets('Onboarding flow navigates to login screen after completion',
        (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: const HowFlipSyncWorksScreen(),
          routes: {
            '/login': (context) => const LoginScreen(),
          },
        ),
      );

      // Navigate through onboarding pages
      while (true) {
        final nextButton = find.text('Next');
        final getStartedButton = find.text('Get Started');

        if (getStartedButton.evaluate().isNotEmpty) {
          // This is the last page, tap Get Started
          await tester.tap(getStartedButton);
          await tester.pumpAndSettle();
          break;
        } else if (nextButton.evaluate().isNotEmpty) {
          // Navigate to next page
          await tester.tap(nextButton);
          await tester.pumpAndSettle();
        } else {
          fail('Could not find Next or Get Started button');
        }
      }

      // Verify we're now on the login screen
      expect(find.text('Welcome back to FlipSync'), findsOneWidget);
    });

    testWidgets('AuthGuard shows login screen when not authenticated', (WidgetTester tester) async {
      // Setup unauthenticated state
      when(() => mockAuthState.isAuthenticated).thenReturn(false);

      await tester.pumpWidget(
        MaterialApp(
          home: AuthGuard(
            child: const Scaffold(
              body: Text('Protected Content'),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Should show login screen instead of protected content
      expect(find.text('Welcome back to FlipSync'), findsOneWidget);
      expect(find.text('Protected Content'), findsNothing);
    });

    testWidgets('AuthGuard shows protected content when authenticated',
        (WidgetTester tester) async {
      // Setup authenticated state
      when(() => mockAuthState.isAuthenticated).thenReturn(true);

      await tester.pumpWidget(
        MaterialApp(
          home: AuthGuard(
            child: const Scaffold(
              body: Text('Protected Content'),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Should show protected content
      expect(find.text('Protected Content'), findsOneWidget);
      expect(find.text('Welcome back to FlipSync'), findsNothing);
    });

    testWidgets('Login screen validates email and password fields', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: const LoginScreen(),
        ),
      );

      // Find the sign in button and tap it without entering credentials
      final signInButton = find.byType(ElevatedButton);
      await tester.tap(signInButton);
      await tester.pumpAndSettle();

      // Should show validation errors
      expect(find.text('Please enter your email'), findsOneWidget);
      expect(find.text('Please enter your password'), findsOneWidget);
    });

    testWidgets('Complete authentication flow: Welcome → Onboarding → Login → Dashboard',
        (WidgetTester tester) async {
      // Setup successful authentication
      when(() => mockAuthService.login(any(), any()))
          .thenAnswer((_) async => ApiResult.success(AuthData(
                accessToken: 'test_token',
                refreshToken: 'test_refresh',
                userId: 'test_user',
              )));
      when(() => mockAuthService.getAccessToken()).thenAnswer((_) async => 'test_token');

      await tester.pumpWidget(
        MaterialApp(
          initialRoute: '/',
          routes: {
            '/': (context) => const WelcomeScreen(),
            '/how-it-works': (context) => const HowFlipSyncWorksScreen(),
            '/login': (context) => const LoginScreen(),
            '/dashboard': (context) => AuthGuard(child: const SalesOptimizationDashboard()),
          },
        ),
      );

      // Step 1: Start from welcome screen
      expect(find.text('FlipSync'), findsOneWidget);

      // Step 2: Tap "Get Started" to go to onboarding
      await tester.tap(find.text('Get Started'));
      await tester.pumpAndSettle();

      // Step 3: Complete onboarding (navigate through all pages)
      while (true) {
        final nextButton = find.text('Next');
        final getStartedButton = find.text('Get Started');

        if (getStartedButton.evaluate().isNotEmpty) {
          // This is the last page, tap Get Started
          await tester.tap(getStartedButton);
          await tester.pumpAndSettle();
          break;
        } else if (nextButton.evaluate().isNotEmpty) {
          // Navigate to next page
          await tester.tap(nextButton);
          await tester.pumpAndSettle();
        } else {
          fail('Could not find Next or Get Started button');
        }
      }

      // Step 4: Should now be on login screen
      expect(find.text('Welcome back to FlipSync'), findsOneWidget);

      // Step 5: Enter credentials and login
      await tester.enterText(find.byType(TextFormField).first, 'test@example.com');
      await tester.enterText(find.byType(TextFormField).last, 'password123');

      // Update auth state to authenticated after login
      when(() => mockAuthState.isAuthenticated).thenReturn(true);
      when(() => mockAuthState.authToken).thenReturn('test_token');

      await tester.tap(find.byType(ElevatedButton)); // Tap the login button
      await tester.pumpAndSettle();

      // Step 6: Should navigate to dashboard
      // Note: In a real test, we'd verify the dashboard content
      // For now, we verify that login was attempted
      verify(() => mockAuthService.login('test@example.com', 'password123')).called(1);
    });
  });
}
