import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/material.dart';
import '../test_utils/test_data.dart';
import '../test_utils/test_helpers.dart';

Future<void> runListingTests(WidgetTester tester) async {
  group('Listing Management Tests', () {
    setUp(() async {
      // Ensure logged in
      await TestHelpers.loginUser(tester);

      // Navigate to listings
      final listingsTab = find.byKey(const Key('listings_tab'));
      await tester.tap(listingsTab);
      await tester.pumpAndSettle();
    });

    testWidgets('Create listing', (tester) async {
      // Tap add button
      final addButton = find.byKey(const Key('add_listing_button'));
      await tester.tap(addButton);
      await tester.pumpAndSettle();

      // Fill form
      await tester.enterText(
        find.byKey(const Key('title_field')),
        TestData.listingTitle,
      );
      await tester.enterText(
        find.byKey(const Key('description_field')),
        TestData.listingDescription,
      );
      await tester.enterText(
        find.byKey(const Key('price_field')),
        TestData.listingPrice,
      );
      await tester.enterText(
        find.byKey(const Key('quantity_field')),
        TestData.listingQuantity,
      );

      // Add image
      await TestHelpers.addListingImage(tester);

      // Submit form
      final submitButton = find.byKey(const Key('submit_listing_button'));
      await tester.tap(submitButton);
      await tester.pumpAndSettle();

      // Verify listing created
      expect(find.text(TestData.listingTitle), findsOneWidget);
    });

    testWidgets('Edit listing', (tester) async {
      // Create test listing
      await TestHelpers.createTestListing(tester);

      // Find and tap edit button
      final editButton = find.byKey(const Key('edit_listing_button'));
      await tester.tap(editButton);
      await tester.pumpAndSettle();

      // Update title
      await tester.enterText(
        find.byKey(const Key('title_field')),
        TestData.updatedListingTitle,
      );

      // Submit changes
      final submitButton = find.byKey(const Key('submit_listing_button'));
      await tester.tap(submitButton);
      await tester.pumpAndSettle();

      // Verify changes
      expect(find.text(TestData.updatedListingTitle), findsOneWidget);
    });

    testWidgets('Delete listing', (tester) async {
      // Create test listing
      await TestHelpers.createTestListing(tester);

      // Find and tap delete button
      final deleteButton = find.byKey(const Key('delete_listing_button'));
      await tester.tap(deleteButton);
      await tester.pumpAndSettle();

      // Confirm deletion
      final confirmButton = find.byKey(const Key('confirm_delete_button'));
      await tester.tap(confirmButton);
      await tester.pumpAndSettle();

      // Verify deletion
      expect(find.text(TestData.listingTitle), findsNothing);
    });

    testWidgets('Filter listings', (tester) async {
      // Create test listings
      await TestHelpers.createMultipleTestListings(tester);

      // Open filter
      final filterButton = find.byKey(const Key('filter_button'));
      await tester.tap(filterButton);
      await tester.pumpAndSettle();

      // Apply price filter
      await tester.enterText(
        find.byKey(const Key('min_price_field')),
        TestData.minPrice,
      );
      await tester.enterText(
        find.byKey(const Key('max_price_field')),
        TestData.maxPrice,
      );

      // Apply filter
      final applyButton = find.byKey(const Key('apply_filter_button'));
      await tester.tap(applyButton);
      await tester.pumpAndSettle();

      // Verify filtered results
      expect(find.byKey(const Key('listing_card')), findsNWidgets(2));
    });

    testWidgets('Search listings', (tester) async {
      // Create test listings
      await TestHelpers.createMultipleTestListings(tester);

      // Perform search
      await tester.enterText(
        find.byKey(const Key('search_field')),
        TestData.searchQuery,
      );
      await tester.testTextInput.receiveAction(TextInputAction.search);
      await tester.pumpAndSettle();

      // Verify search results
      expect(find.byKey(const Key('listing_card')), findsOneWidget);
      expect(find.text(TestData.searchResultTitle), findsOneWidget);
    });

    testWidgets('Offline functionality', (tester) async {
      // Create test listing
      await TestHelpers.createTestListing(tester);

      // Enable offline mode
      await TestHelpers.setOfflineMode(true);

      // Verify listing still visible
      expect(find.text(TestData.listingTitle), findsOneWidget);

      // Try to edit
      final editButton = find.byKey(const Key('edit_listing_button'));
      await tester.tap(editButton);
      await tester.pumpAndSettle();

      await tester.enterText(
        find.byKey(const Key('title_field')),
        TestData.offlineUpdateTitle,
      );

      final submitButton = find.byKey(const Key('submit_listing_button'));
      await tester.tap(submitButton);
      await tester.pumpAndSettle();

      // Verify offline indicator
      expect(find.byKey(const Key('offline_indicator')), findsOneWidget);

      // Restore online mode
      await TestHelpers.setOfflineMode(false);
      await tester.pumpAndSettle();

      // Verify changes synced
      expect(find.text(TestData.offlineUpdateTitle), findsOneWidget);
    });
  });
}
