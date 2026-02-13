<?php

namespace App\Policies;

use App\Models\Tenant;
use App\Models\User;
use Illuminate\Auth\Access\HandlesAuthorization;

class TenantPolicy
{
    use HandlesAuthorization;

    public function viewAny(User $user): bool
    {
        return $user->hasPermissionTo('view_any_tenant');
    }

    public function view(User $user, Tenant $model): bool
    {
        return $user->hasPermissionTo('view_tenant');
    }

    public function create(User $user): bool
    {
        return $user->hasPermissionTo('create_tenant');
    }

    public function update(User $user, Tenant $model): bool
    {
        return $user->hasPermissionTo('update_tenant');
    }

    public function delete(User $user, Tenant $model): bool
    {
        return $user->hasPermissionTo('delete_tenant');
    }
}
