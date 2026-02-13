<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Relations\BelongsToMany;
use Spatie\Permission\Models\Role as SpatieRole;

class Role extends SpatieRole
{
    public function tenants(): BelongsToMany
    {
        return $this->belongsToMany(Tenant::class, 'model_has_roles', 'role_id', 'model_id')
            ->where('model_type', Tenant::class);
    }

    public function tenant(): BelongsToMany
    {
        return $this->tenants();
    }
}
