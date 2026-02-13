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
        Schema::table('campaigns', function (Blueprint $table) {
            $table->enum('type', ['ppdb', 'fundraising'])->default('ppdb')->after('tenant_id');
            $table->decimal('target_amount', 15, 2)->default(0)->after('education_fee');
            $table->decimal('current_amount', 15, 2)->default(0)->after('target_amount');
            $table->string('image')->nullable()->after('current_amount');
            $table->enum('status', ['draft', 'active', 'completed'])->default('active')->after('is_active');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('campaigns', function (Blueprint $table) {
            $table->dropColumn(['type', 'target_amount', 'current_amount', 'image', 'status']);
        });
    }
};
