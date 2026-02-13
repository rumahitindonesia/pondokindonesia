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
        Schema::table('settings', function (Blueprint $table) {
            $table->dropPrimary();
            $table->unsignedBigInteger('tenant_id')->after('key');
            $table->primary(['tenant_id', 'key']);
            $table->foreign('tenant_id')->references('id')->on('tenants')->onDelete('cascade');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('settings', function (Blueprint $table) {
            $table->dropForeign(['tenant_id']);
            $table->dropPrimary();
            $table->dropColumn('tenant_id');
            $table->primary('key');
        });
    }
};
