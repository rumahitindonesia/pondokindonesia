<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Lead extends Model
{
    protected $fillable = [
        'tenant_id',
        'campaign_id',
        'aff_id',
        'name',
        'email',
        'whatsapp',
        'institution_name',
        'message',
        'status',
        'otp_code',
        'otp_expires_at',
        'is_verified',
        'registration_data',
        'interview_date',
        'interview_status',
        'payment_status',
        'total_amount',
        'paid_amount',
        'remaining_amount',
    ];

    protected $casts = [
        'otp_expires_at' => 'datetime',
        'is_verified' => 'boolean',
        'registration_data' => 'array',
        'interview_date' => 'datetime',
        'total_amount' => 'decimal:2',
        'paid_amount' => 'decimal:2',
        'remaining_amount' => 'decimal:2',
    ];

    // Relationships
    public function tenant(): BelongsTo
    {
        return $this->belongsTo(Tenant::class);
    }

    public function campaign(): BelongsTo
    {
        return $this->belongsTo(Campaign::class);
    }

    public function payments(): HasMany
    {
        return $this->hasMany(Payment::class);
    }

    public function interviews(): HasMany
    {
        return $this->hasMany(Interview::class);
    }

    // Business Logic Methods
    public function updatePaymentStatus(): void
    {
        $totalPaid = $this->payments()->sum('amount');
        $this->paid_amount = $totalPaid;
        
        if ($this->total_amount) {
            $this->remaining_amount = $this->total_amount - $totalPaid;
            
            if ($this->remaining_amount <= 0) {
                $this->payment_status = 'paid';
                $this->remaining_amount = 0;
            } elseif ($totalPaid > 0) {
                $this->payment_status = 'partial';
            } else {
                $this->payment_status = 'unpaid';
            }
        }
        
        $this->saveQuietly(); // Prevent infinite loop
    }

    public function calculateRemainingAmount(): float
    {
        if (!$this->total_amount) return 0;
        return max(0, $this->total_amount - $this->paid_amount);
    }

    public function sendPaymentReminder(): void
    {
        if ($this->payment_status !== 'paid' && $this->whatsapp) {
            app(\App\Services\StarSenderService::class)->sendPaymentReminder($this);
        }
    }

    public function santri(): \Illuminate\Database\Eloquent\Relations\HasOne
    {
        return $this->hasOne(Santri::class);
    }

    public function convertToSantri(): bool
    {
        if ($this->santri()->exists()) return true;

        $santri = Santri::create([
            'tenant_id' => $this->tenant_id,
            'lead_id' => $this->id,
            'name' => $this->name,
            'email' => $this->email,
            'whatsapp' => $this->whatsapp,
            'status' => 'active',
            'registration_date' => now(),
            'spp_amount' => $this->campaign->education_fee ?? 0,
        ]);

        $this->status = 'santri';
        $this->save();
        
        // Send welcome message
        $tenant = $this->tenant;
        $service = new \App\Services\StarSenderService($tenant);
        $service->sendWelcomeMessage($this);
        
        return true;
    }

    public function convertToDonor(): bool
    {
        $donor = Donor::firstOrCreate(
            ['whatsapp' => $this->whatsapp, 'tenant_id' => $this->tenant_id],
            [
                'name' => $this->name,
                'email' => $this->email,
                'type' => 'regular',
            ]
        );

        $this->status = 'santri'; // Using 'santri' as a generic 'closed' status for now, or maybe add 'donor' status
        $this->save();

        return true;
    }

    protected static function boot()
    {
        parent::boot();

        static::creating(function ($lead) {
            if (empty($lead->tenant_id) && $lead->campaign_id) {
                $lead->tenant_id = $lead->campaign->tenant_id;
            }
        });
    }
}
