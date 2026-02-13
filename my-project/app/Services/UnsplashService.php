<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use App\Models\Setting;

class UnsplashService
{
    protected $accessKey;
    protected $baseUrl = 'https://api.unsplash.com';

    public function __construct()
    {
        $this->accessKey = Setting::get('unsplash_access_key');
    }

    /**
     * Search for photos
     */
    public function search(string $query, int $perPage = 10): array
    {
        if (!$this->accessKey) {
            return [
                'success' => false,
                'message' => 'Unsplash access key not configured'
            ];
        }

        try {
            $response = Http::withHeaders([
                'Authorization' => 'Client-ID ' . $this->accessKey,
            ])->get($this->baseUrl . '/search/photos', [
                'query' => $query,
                'per_page' => $perPage,
                'orientation' => 'landscape',
            ]);

            if ($response->successful()) {
                return [
                    'success' => true,
                    'photos' => $response->json()['results'] ?? [],
                    'data' => $response->json()
                ];
            }

            return [
                'success' => false,
                'message' => 'Unsplash API request failed',
                'error' => $response->body()
            ];

        } catch (\Exception $e) {
            Log::error('UnsplashService: ' . $e->getMessage());
            return [
                'success' => false,
                'message' => 'Unsplash service error'
            ];
        }
    }
}
