<?php
require __DIR__ . '/vendor/autoload.php';
$app = require_once __DIR__ . '/bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();

use App\Models\Setting;
use Illuminate\Support\Facades\Http;

echo "Listing Gemini Models...\n";
$apiKey = Setting::get('gemini_api_key') ?? config('services.gemini.key');

if (!$apiKey) {
    die("API Key is missing.\n");
}

$url = 'https://generativelanguage.googleapis.com/v1beta/models?key=' . $apiKey;

try {
    $response = Http::get($url);
    if ($response->successful()) {
        $data = $response->json();
        if (isset($data['models'])) {
            foreach ($data['models'] as $model) {
                if (in_array('generateContent', $model['supportedGenerationMethods'])) {
                    echo "Model: " . $model['name'] . "\n";
                }
            }
        } else {
            print_r($data);
        }
    } else {
        echo "Error: " . $response->status() . "\n";
        echo $response->body() . "\n";
    }
} catch (\Throwable $e) {
    echo "Exception: " . $e->getMessage() . "\n";
}
