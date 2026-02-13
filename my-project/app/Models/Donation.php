<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Donation extends Model
{
    protected $fillable = [
        'tenant_id',
        'campaign_id',
        'donor_id',
        'donor_name',
        'amount',
        'payment_method',
        'status',
        'wa_number',
        'message',
    ];

    public static function boot()
    {
        parent::boot();

        static::creating(function ($donation) {
            if (empty($donation->tenant_id) && $donation->campaign_id) {
                $donation->tenant_id = $donation->campaign->tenant_id;
            }

            // Link to donor or create one
            if ($donation->wa_number) {
                $donor = Donor::firstOrCreate(
                    ['whatsapp' => $donation->wa_number, 'tenant_id' => $donation->tenant_id],
                    ['name' => $donation->donor_name]
                );
                $donation->donor_id = $donor->id;
            }
        });

        static::created(function ($donation) {
            if ($donation->status === 'success') {
                $donation->campaign->increment('current_amount', $donation->amount);
                
                if ($donation->donor) {
                    $donation->donor->increment('total_donations', $donation->amount);
                    $donation->donor->update(['last_donation_date' => now()]);
                }

                if ($donation->wa_number) {
                    $service = new \App\Services\StarSenderService($donation->tenant);
                    $message = "Halo *{$donation->donor_name}*, terima kasih atas donasinya sebesar *IDR " . number_format($donation->amount, 0, ',', '.') . "* untuk kampanye *{$donation->campaign->title}*.\n\nSemoga menjadi amal jariyah yang terus mengalir pahalanya. Aamiin.";
                    $service->sendMessage($donation->wa_number, $message);
                }
            }
        });

        static::updated(function ($donation) {
            if ($donation->wasChanged('status') && $donation->status === 'success') {
                $donation->campaign->increment('current_amount', $donation->amount);
                
                if ($donation->wa_number) {
                    $service = new \App\Services\StarSenderService($donation->tenant);
                    $message = "Halo *{$donation->donor_name}*, terima kasih atas donasinya sebesar *IDR " . number_format($donation->amount, 0, ',', '.') . "* untuk kampanye *{$donation->campaign->title}*.\n\nSemoga menjadi amal jariyah yang terus mengalir pahalanya. Aamiin.";
                    $service->sendMessage($donation->wa_number, $message);
                }
            }
        });
    }

    public function tenant()
    {
        return $this->belongsTo(Tenant::class);
    }

    public function campaign()
    {
        return $this->belongsTo(Campaign::class);
    }

    public function donor()
    {
        return $this->belongsTo(Donor::class);
    }
}
