<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use App\Models\Setting;

class GroqService
{
    protected $apiKey;
    protected $baseUrl = 'https://api.groq.com/openai/v1';
    protected $model = 'llama3-8b-8192';

    public function __construct()
    {
        $this->apiKey = Setting::get('groq_api_key');
    }

    /**
     * Generate text completion
     */
    public function complete(string $prompt, array $options = []): array
    {
        if (!$this->apiKey) {
            return [
                'success' => false,
                'message' => 'Groq API key not configured'
            ];
        }

        try {
            $response = Http::withHeaders([
                'Authorization' => 'Bearer ' . $this->apiKey,
                'Content-Type' => 'application/json',
            ])->post($this->baseUrl . '/chat/completions', [
                'model' => $options['model'] ?? $this->model,
                'messages' => [
                    ['role' => 'user', 'content' => $prompt]
                ],
                'temperature' => $options['temperature'] ?? 0.7,
                'max_tokens' => $options['max_tokens'] ?? 1000,
            ]);

            if ($response->successful()) {
                return [
                    'success' => true,
                    'content' => $response->json()['choices'][0]['message']['content'] ?? '',
                    'data' => $response->json()
                ];
            }

            return [
                'success' => false,
                'message' => 'Groq API request failed',
                'error' => $response->body()
            ];

        } catch (\Exception $e) {
            Log::error('GroqService: ' . $e->getMessage());
            return [
                'success' => false,
                'message' => 'Groq service error'
            ];
        }
    }
}
