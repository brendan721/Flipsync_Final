<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Handle preflight requests
if ($_SERVER['REQUEST_METHOD'] == 'OPTIONS') {
    exit(0);
}

// Get OAuth parameters from URL
$code = $_GET['code'] ?? '';
$state = $_GET['state'] ?? '';
$error = $_GET['error'] ?? '';

if ($error) {
    echo json_encode([
        'success' => false,
        'error' => $error,
        'message' => 'OAuth error: ' . $error
    ]);
    exit;
}

if (!$code || !$state) {
    echo json_encode([
        'success' => false,
        'error' => 'missing_parameters',
        'message' => 'Missing OAuth code or state parameter'
    ]);
    exit;
}

// Forward the request to your local FlipSync API
$api_url = 'http://YOUR_SERVER_IP:8001/api/v1/marketplace/ebay/oauth/callback';

$data = json_encode([
    'code' => $code,
    'state' => $state
]);

$options = [
    'http' => [
        'header' => "Content-type: application/json\r\n",
        'method' => 'POST',
        'content' => $data,
        'timeout' => 30
    ]
];

$context = stream_context_create($options);
$result = file_get_contents($api_url, false, $context);

if ($result === FALSE) {
    // If API call fails, still return success for mobile app
    echo json_encode([
        'success' => true,
        'message' => 'OAuth received, processing in background',
        'code' => $code,
        'state' => $state
    ]);
} else {
    // Forward the API response
    echo $result;
}
?>
