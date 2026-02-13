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
            // Drop foreign key and primary key first to allow changing column type
            $table->dropForeign(['tenant_id']);
            $table->dropPrimary(['tenant_id', 'key']);
            
            // Change column type to char(36) for UUID
            $table->char('tenant_id', 36)->change();
            
            // Re-add primary key and foreign key
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
            $table->dropPrimary(['tenant_id', 'key']);
            
            $table->unsignedBigInteger('tenant_id')->change();
            
            $table->primary(['tenant_id', 'key']);
            $table->foreign('tenant_id')->references('id')->on('tenants')->onDelete('cascade');
        });
    }
};
