<?php
require __DIR__ . '/vendor/autoload.php';
$app = require_once __DIR__ . '/bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();

use App\Services\GroqService;
use App\Models\Setting;

echo "Testing GroqService...\n";

// Ensure a dummy key is set for testing if not already present
if (!Setting::get('groq_api_key')) {
    echo "Warning: No Groq API Key found in Settings. Please set it in the admin panel first.\n";
    // We can't really test without a key, so we'll stop here.
    exit(1);
}

try {
    $service = new GroqService();
    $result = $service->generatePostContent('Benefits of Open Source Software');
    
    echo "Service Call Completed.\n";
    if ($result) {
        echo "Success!\n";
        print_r($result);
    } else {
        echo "Failed. Check logs.\n";
    }
} catch (\Throwable $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
