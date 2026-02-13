<?php
require __DIR__ . '/vendor/autoload.php';
$app = require_once __DIR__ . '/bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();

use App\Services\GeminiService;

echo "Testing GeminiService Logging...\n";
try {
    $service = new GeminiService();
    $result = $service->generatePostContent('Test Prompt for Logging');
    echo "Service Call Completed.\n";
    print_r($result);
} catch (\Throwable $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
