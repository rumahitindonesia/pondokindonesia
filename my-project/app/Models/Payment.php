<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class Payment extends Model
{
    protected $fillable = [
        'tenant_id',
        'lead_id',
        'amount',
        'payment_method',
        'payment_date',
        'proof_image',
        'notes',
        'recorded_by',
    ];

    protected $casts = [
        'amount' => 'decimal:2',
        'payment_date' => 'date',
    ];

    // Relationships
    public function tenant(): BelongsTo
    {
        return $this->belongsTo(Tenant::class);
    }

    public function lead(): BelongsTo
    {
        return $this->belongsTo(Lead::class);
    }

    public function recorder(): BelongsTo
    {
        return $this->belongsTo(User::class, 'recorded_by');
    }

    // Auto-update lead payment status after payment recorded
    protected static function boot()
    {
        parent::boot();

        static::creating(function ($payment) {
            if (empty($payment->tenant_id) && $payment->lead_id) {
                $payment->tenant_id = $payment->lead->tenant_id;
            }
        });

        static::created(function ($payment) {
            $payment->lead->updatePaymentStatus();
            
            // Send WhatsApp Confirmation
            $tenant = $payment->lead->campaign->tenant;
            $service = new \App\Services\StarSenderService($tenant);
            if ($service->isEnabled()) {
                $service->sendPaymentConfirmation($payment->lead, $payment->amount);
            }
        });

        static::updated(function ($payment) {
            $payment->lead->updatePaymentStatus();
        });

        static::deleted(function ($payment) {
            $payment->lead->updatePaymentStatus();
        });
    }
}
