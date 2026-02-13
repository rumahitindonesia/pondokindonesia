<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use App\Models\Setting;

class GeminiService
{
    protected $apiKey;
    protected $baseUrl = 'https://generativelanguage.googleapis.com/v1beta/models';
    protected $model = 'gemini-1.5-flash';

    public function __construct()
    {
        $this->apiKey = Setting::get('gemini_api_key');
    }

    /**
     * Generate content
     */
    public function generate(string $prompt): array
    {
        if (!$this->apiKey) {
            return [
                'success' => false,
                'message' => 'Gemini API key not configured'
            ];
        }

        try {
            $url = "{$this->baseUrl}/{$this->model}:generateContent?key={$this->apiKey}";
            
            $response = Http::post($url, [
                'contents' => [
                    [
                        'parts' => [
                            ['text' => $prompt]
                        ]
                    ]
                ]
            ]);

            if ($response->successful()) {
                return [
                    'success' => true,
                    'content' => $response->json()['candidates'][0]['content']['parts'][0]['text'] ?? '',
                    'data' => $response->json()
                ];
            }

            return [
                'success' => false,
                'message' => 'Gemini API request failed',
                'error' => $response->body()
            ];

        } catch (\Exception $e) {
            Log::error('GeminiService: ' . $e->getMessage());
            return [
                'success' => false,
                'message' => 'Gemini service error'
            ];
        }
    }
}
