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
        Schema::table('leads', function (Blueprint $table) {
            // Campaign & Affiliate tracking
            if (!Schema::hasColumn('leads', 'campaign_id')) {
                $table->foreignId('campaign_id')->nullable()->after('id')->constrained()->nullOnDelete();
            }
            
            if (!Schema::hasColumn('leads', 'aff_id')) {
                $table->string('aff_id')->nullable()->after('campaign_id');
            }
            
            // Status workflow (Change existing status column to enum)
            $table->enum('status', [
                'new', 
                'contacted', 
                'closing', 
                'registered', 
                'interviewed', 
                'accepted', 
                'rejected', 
                'santri'
            ])->default('new')->change();
            
            // Registration data
            if (!Schema::hasColumn('leads', 'registration_data')) {
                $table->json('registration_data')->nullable()->after('status');
            }
            
            // Interview tracking
            if (!Schema::hasColumn('leads', 'interview_date')) {
                $table->dateTime('interview_date')->nullable()->after('registration_data');
            }
            if (!Schema::hasColumn('leads', 'interview_status')) {
                $table->enum('interview_status', ['scheduled', 'completed', 'passed', 'failed'])->nullable()->after('interview_date');
            }
            
            // Payment tracking
            if (!Schema::hasColumn('leads', 'payment_status')) {
                $table->enum('payment_status', ['unpaid', 'partial', 'paid'])->nullable()->after('interview_status');
            }
            if (!Schema::hasColumn('leads', 'total_amount')) {
                $table->decimal('total_amount', 12, 2)->nullable()->after('payment_status');
            }
            if (!Schema::hasColumn('leads', 'paid_amount')) {
                $table->decimal('paid_amount', 12, 2)->default(0)->after('total_amount');
            }
            if (!Schema::hasColumn('leads', 'remaining_amount')) {
                $table->decimal('remaining_amount', 12, 2)->nullable()->after('paid_amount');
            }
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('leads', function (Blueprint $table) {
            $table->dropForeign(['campaign_id']);
            $table->dropColumn([
                'campaign_id',
                'aff_id',
                'status',
                'registration_data',
                'interview_date',
                'interview_status',
                'payment_status',
                'total_amount',
                'paid_amount',
                'remaining_amount',
            ]);
        });
    }
};
