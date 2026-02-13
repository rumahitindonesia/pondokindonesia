<?php
require __DIR__ . '/vendor/autoload.php';
$app = require_once __DIR__ . '/bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();

use App\Models\Setting;
use App\Services\GeminiService;

// Test Settings
echo "Testing Setting model...\n";
Setting::set('gemini_api_key', 'test_key_123');
$retrieved = Setting::get('gemini_api_key');
echo "Set/Get Gemini Key: " . ($retrieved === 'test_key_123' ? 'PASS' : 'FAIL') . "\n";

// Test Service
echo "Testing GeminiService...\n";
$service = new GeminiService();
$reflection = new ReflectionClass($service);
$property = $reflection->getProperty('apiKey');
$property->setAccessible(true);
$apiKey = $property->getValue($service);

echo "Service uses Setting Key: " . ($apiKey === 'test_key_123' ? 'PASS' : 'FAIL') . "\n";
