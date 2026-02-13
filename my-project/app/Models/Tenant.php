<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsToMany;
use Illuminate\Support\Facades\Storage;

class Tenant extends Model
{
    use HasUuids;

    protected $fillable = [
        'name',
        'slug',
        'description',
        'address',
        'logo_path',
        'whatsapp_number',
        'whatsapp_api_key',
        'whatsapp_enabled',
        'plan',
        'plan_expires_at',
    ];

    protected $casts = [
        'whatsapp_enabled' => 'boolean',
        'plan_expires_at' => 'datetime',
    ];

    public function isPremium(): bool
    {
        if ($this->plan === 'premium') {
            return is_null($this->plan_expires_at) || $this->plan_expires_at->isFuture();
        }
        return false;
    }

    public function canCreateCampaign(): bool
    {
        if ($this->isPremium()) {
            return true;
        }

        return $this->campaigns()->where('status', 'active')->count() < 1;
    }

    public function getLogoUrlAttribute(): ?string
    {
        return $this->logo_path ? Storage::url($this->logo_path) : null;
    }

    public function users(): BelongsToMany
    {
        return $this->belongsToMany(User::class);
    }

    public function posts(): \Illuminate\Database\Eloquent\Relations\HasMany
    {
        return $this->hasMany(Post::class);
    }

    public function campaigns(): \Illuminate\Database\Eloquent\Relations\HasMany
    {
        return $this->hasMany(Campaign::class);
    }

    public function donations(): \Illuminate\Database\Eloquent\Relations\HasMany
    {
        return $this->hasMany(Donation::class);
    }
}
