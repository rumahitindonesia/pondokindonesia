<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class Interview extends Model
{
    protected $fillable = [
        'tenant_id',
        'lead_id',
        'scheduled_date',
        'interviewer_id',
        'location',
        'notes',
        'result',
        'created_by',
    ];

    protected $casts = [
        'scheduled_date' => 'datetime',
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

    public function interviewer(): BelongsTo
    {
        return $this->belongsTo(User::class, 'interviewer_id');
    }

    public function creator(): BelongsTo
    {
        return $this->belongsTo(User::class, 'created_by');
    }

    // Auto-update lead interview status
    protected static function boot()
    {
        parent::boot();

        static::creating(function ($interview) {
            if (empty($interview->tenant_id) && $interview->lead_id) {
                $interview->tenant_id = $interview->lead->tenant_id;
            }
        });

        static::created(function ($interview) {
            $interview->lead->update([
                'interview_date' => $interview->scheduled_date,
                'interview_status' => 'scheduled',
                'status' => 'interviewed',
            ]);

            // Send WhatsApp Notification
            $tenant = $interview->lead->campaign->tenant;
            $service = new \App\Services\StarSenderService($tenant);
            if ($service->isEnabled()) {
                $service->sendInterviewSchedule($interview);
            }
        });

        static::updated(function ($interview) {
            if ($interview->wasChanged('result')) {
                $tenant = $interview->lead->campaign->tenant;
                $service = new \App\Services\StarSenderService($tenant);

                if ($interview->result === 'passed') {
                    $interview->lead->update([
                        'interview_status' => 'passed',
                        'status' => 'accepted',
                    ]);

                    if ($service->isEnabled()) {
                        $service->sendAcceptanceNotification($interview->lead);
                    }
                } elseif ($interview->result === 'failed') {
                    $interview->lead->update([
                        'interview_status' => 'failed',
                        'status' => 'rejected',
                    ]);
                }
            }
        });
    }
}
