import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'usability_test_framework.dart';

/// User feedback collection for the FlipSync mobile application
///
/// This class provides tools for collecting and analyzing user feedback
/// during usability testing sessions.
class UserFeedbackCollection {
  final UsabilityTestFramework _framework = UsabilityTestFramework();

  /// Initialize the feedback collection system
  Future<void> initialize() async {
    await _framework.initialize();
  }

  /// Record feedback from a user
  void recordFeedback({
    required String userId,
    required String userType,
    required String screen,
    required int rating,
    required String comment,
  }) {
    _framework.recordUserFeedback(
      UserFeedback(
        userId: userId,
        userType: userType,
        screen: screen,
        rating: rating,
        comment: comment,
      ),
    );
  }

  /// Get all recorded feedback
  List<UserFeedback> getAllFeedback() {
    return _framework.userFeedback;
  }

  /// Calculate average rating for a specific screen
  double getAverageRatingForScreen(String screen) {
    final screenFeedback = _framework.userFeedback
        .where((feedback) => feedback.screen == screen)
        .toList();

    if (screenFeedback.isEmpty) {
      return 0.0;
    }

    final sum =
        screenFeedback.fold<int>(0, (sum, feedback) => sum + feedback.rating);
    return sum / screenFeedback.length;
  }

  /// Generate a feedback report
  String generateFeedbackReport() {
    return _framework.generateReport();
  }

  /// Populate with sample feedback data for demonstration
  void populateSampleData() {
    // Sample user feedback for demonstration
    recordFeedback(
      userId: 'user001',
      userType: 'New User',
      screen: 'Onboarding',
      rating: 4,
      comment:
          'The onboarding process was smooth and informative. I liked the visual guides.',
    );

    recordFeedback(
      userId: 'user002',
      userType: 'Experienced User',
      screen: 'Dashboard',
      rating: 3,
      comment:
          'The dashboard is informative but feels cluttered. Could use more spacing between elements.',
    );

    recordFeedback(
      userId: 'user003',
      userType: 'Power User',
      screen: 'Inventory Management',
      rating: 5,
      comment:
          'The inventory management screen is excellent. Very efficient workflow.',
    );

    recordFeedback(
      userId: 'user004',
      userType: 'New User',
      screen: 'Settings',
      rating: 4,
      comment:
          'The settings are well organized. I particularly liked the theme options.',
    );

    recordFeedback(
      userId: 'user005',
      userType: 'Experienced User',
      screen: 'Order Processing',
      rating: 2,
      comment:
          'The order processing workflow is confusing. Too many steps to complete a simple task.',
    );

    recordFeedback(
      userId: 'user001',
      userType: 'New User',
      screen: 'Analytics',
      rating: 3,
      comment:
          'The charts are nice but I had trouble understanding some of the metrics without explanations.',
    );

    recordFeedback(
      userId: 'user006',
      userType: 'Accessibility User',
      screen: 'Accessibility Settings',
      rating: 5,
      comment:
          'The accessibility options are comprehensive and work well with my screen reader.',
    );

    recordFeedback(
      userId: 'user007',
      userType: 'New User',
      screen: 'Theme Switcher',
      rating: 5,
      comment:
          'The theme switcher is intuitive and I love the quantum theme option!',
    );
  }
}

/// Widget for collecting user feedback in the app
class FeedbackForm extends StatefulWidget {
  final Function(String, int, String) onSubmit;
  final String screenName;

  const FeedbackForm({
    super.key,
    required this.onSubmit,
    required this.screenName,
  });

  @override
  State<FeedbackForm> createState() => _FeedbackFormState();
}

class _FeedbackFormState extends State<FeedbackForm> {
  int _rating = 3;
  final TextEditingController _commentController = TextEditingController();

  @override
  void dispose() {
    _commentController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'Your Feedback',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            Text(
              'How would you rate your experience with this screen?',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 16),

            // Rating
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(5, (index) {
                return IconButton(
                  icon: Icon(
                    index < _rating ? Icons.star : Icons.star_border,
                    color: index < _rating ? Colors.amber : null,
                    size: 32,
                  ),
                  onPressed: () {
                    setState(() {
                      _rating = index + 1;
                    });
                  },
                );
              }),
            ),

            const SizedBox(height: 16),

            // Comment
            TextField(
              controller: _commentController,
              decoration: const InputDecoration(
                labelText: 'Comments',
                hintText: 'Please share your thoughts about this screen',
                border: OutlineInputBorder(),
              ),
              maxLines: 3,
            ),

            const SizedBox(height: 16),

            // Submit Button
            Center(
              child: ElevatedButton(
                onPressed: () {
                  widget.onSubmit(
                    widget.screenName,
                    _rating,
                    _commentController.text,
                  );

                  // Clear form
                  setState(() {
                    _rating = 3;
                    _commentController.clear();
                  });

                  // Show confirmation
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('Thank you for your feedback!'),
                      duration: Duration(seconds: 2),
                    ),
                  );
                },
                child: const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  child: Text('Submit Feedback'),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
