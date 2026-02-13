<?php
use Illuminate\Contracts\Console\Kernel;
require __DIR__ . '/vendor/autoload.php';
$app = require_once __DIR__ . '/bootstrap/app.php';
$app->make(Kernel::class)->bootstrap();
try {
    $campaign = App\Models\Campaign::updateOrCreate(
        ['slug' => 'ppdb-2026-gel-1'],
        [
            'tenant_id' => '019c45d6-8e31-7052-884d-dddcd107f4d1',
            'title' => 'PPDB 2026 Gelombang 1',
            'description' => 'Pendaftaran Santri Baru Gelombang 1 untuk tahun ajaran 2026/2027.',
            'landing_page_content' => '<h1>Selamat Datang di PPDB Pondok IT</h1><p>Ayo daftar sekarang!</p>',
            'registration_fee' => 150000,
            'education_fee' => 5000000,
            'is_active' => true,
        ]
    );
    echo "Campaign created/updated: " . $campaign->slug . "\n";
} catch (\Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
