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
        Schema::create('crm_invoices', function (Blueprint $table) {
            $table->id();
            $table->foreignUuid('tenant_id')->constrained()->cascadeOnDelete();
            $table->foreignId('santri_id')->nullable()->constrained()->cascadeOnDelete();
            $table->foreignId('donor_id')->nullable()->constrained()->cascadeOnDelete();
            $table->string('type'); // spp, recurring_donation, one_time_donation
            $table->decimal('amount', 15, 2);
            $table->date('due_date');
            $table->timestamp('paid_at')->nullable();
            $table->string('status')->default('pending'); // pending, paid, cancelled
            $table->string('period')->nullable(); // e.g., "2026-02"
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('crm_invoices');
    }
};
