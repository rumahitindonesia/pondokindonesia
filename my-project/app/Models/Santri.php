<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Santri extends Model
{
    protected $fillable = [
        'tenant_id',
        'lead_id',
        'name',
        'email',
        'whatsapp',
        'status',
        'registration_date',
        'spp_amount',
        'address',
    ];

    protected $casts = [
        'registration_date' => 'date',
        'spp_amount' => 'decimal:2',
    ];

    public function tenant(): BelongsTo
    {
        return $this->belongsTo(Tenant::class);
    }

    public function lead(): BelongsTo
    {
        return $this->belongsTo(Lead::class);
    }

    public function invoices(): HasMany
    {
        return $this->hasMany(CrmInvoice::class);
    }
}
