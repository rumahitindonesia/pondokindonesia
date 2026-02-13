<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::table('tenants', function (Blueprint $table) {
            $table->string('whatsapp_number')->nullable()->after('slug');
            $table->string('whatsapp_api_key')->nullable()->after('whatsapp_number');
            $table->boolean('whatsapp_enabled')->default(true)->after('whatsapp_api_key');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('tenants', function (Blueprint $table) {
            $table->dropColumn(['whatsapp_number', 'whatsapp_api_key', 'whatsapp_enabled']);
        });
    }
};
