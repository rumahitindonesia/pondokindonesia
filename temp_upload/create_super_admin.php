<?php

use App\Models\User;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\Schema;

require __DIR__ . '/vendor/autoload.php';
$app = require_once __DIR__ . '/bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();

try {
    $user = User::updateOrCreate(
        ['email' => 'triyono@mail.com'],
        [
            'name' => 'Triyono Super Admin',
            'password' => Hash::make('password'),
            'email_verified_at' => now(),
        ]
    );

    if (Schema::hasTable('roles')) {
        $user->assignRole('super_admin');
        echo "SUCCESS: User triyono@mail.com created and role super_admin assigned.\n";
    } else {
        echo "WARNING: User created, but roles table not found.\n";
    }
} catch (\Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
}
