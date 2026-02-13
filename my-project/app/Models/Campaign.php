<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Support\Str;

class Campaign extends Model
{
    protected $fillable = [
        'tenant_id',
        'type',
        'title',
        'slug',
        'description',
        'landing_page_content',
        'registration_fee',
        'education_fee',
        'target_amount',
        'current_amount',
        'image',
        'meta_title',
        'meta_description',
        'seo_keywords',
        'aff_id',
        'is_active',
        'status',
        'start_date',
        'end_date',
        'created_by',
    ];

    protected $casts = [
        'is_active' => 'boolean',
        'start_date' => 'date',
        'end_date' => 'date',
        'registration_fee' => 'decimal:2',
        'education_fee' => 'decimal:2',
    ];

    // Relationships
    public function tenant(): BelongsTo
    {
        return $this->belongsTo(Tenant::class);
    }

    public function leads(): HasMany
    {
        return $this->hasMany(Lead::class);
    }

    public function creator(): BelongsTo
    {
        return $this->belongsTo(User::class, 'created_by');
    }

    // Analytics Methods
    public function getTotalLeadsAttribute(): int
    {
        return $this->leads()->count();
    }

    public function getRegisteredLeadsAttribute(): int
    {
        return $this->leads()->whereIn('status', ['registered', 'interviewed', 'accepted', 'santri'])->count();
    }

    public function getConversionRateAttribute(): float
    {
        $total = $this->total_leads;
        if ($total === 0) return 0;
        
        return round(($this->registered_leads / $total) * 100, 2);
    }

    public function getTotalRevenueAttribute(): float
    {
        return $this->leads()
            ->whereNotNull('paid_amount')
            ->sum('paid_amount');
    }

    public function getLeadsByAffiliateAttribute(): array
    {
        return $this->leads()
            ->whereNotNull('aff_id')
            ->selectRaw('aff_id, count(*) as count')
            ->groupBy('aff_id')
            ->pluck('count', 'aff_id')
            ->toArray();
    }

    // Auto-generate slug
    protected static function boot()
    {
        parent::boot();

        static::creating(function ($campaign) {
            if (empty($campaign->slug)) {
                $campaign->slug = Str::slug($campaign->title);
            }
        });
    }
}
