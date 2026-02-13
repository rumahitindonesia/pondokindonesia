<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class TenantSetting extends Model
{
    protected $table = 'settings';
    
    protected $primaryKey = null;
    
    public $incrementing = false;

    protected $fillable = [
        'tenant_id',
        'key',
        'value',
    ];

    public function tenant(): BelongsTo
    {
        return $this->belongsTo(Tenant::class);
    }

    /**
     * Get setting value by key and tenant
     */
    public static function get(string $key, $default = null)
    {
        $tenant = \Filament\Facades\Filament::getTenant();
        if (!$tenant) return $default;

        $setting = static::where('tenant_id', $tenant->id)
            ->where('key', $key)
            ->first();

        return $setting ? $setting->value : $default;
    }

    /**
     * Set setting value
     */
    public static function set(string $key, $value)
    {
        $tenant = \Filament\Facades\Filament::getTenant();
        if (!$tenant) return null;

        return static::updateOrCreate(
            ['tenant_id' => $tenant->id, 'key' => $key],
            ['value' => $value]
        );
    }
}
