<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Donor extends Model
{
    protected $fillable = [
        'tenant_id',
        'name',
        'email',
        'whatsapp',
        'total_donations',
        'last_donation_date',
        'type',
    ];

    protected $casts = [
        'total_donations' => 'decimal:2',
        'last_donation_date' => 'date',
    ];

    public function tenant(): BelongsTo
    {
        return $this->belongsTo(Tenant::class);
    }

    public function donations(): HasMany
    {
        return $this->hasMany(Donation::class);
    }

    public function invoices(): HasMany
    {
        return $this->hasMany(CrmInvoice::class);
    }
}
