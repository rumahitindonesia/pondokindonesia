<?php

namespace App\Http\Responses;

use Filament\Http\Responses\Auth\Contracts\LoginResponse as Responsable;
use Illuminate\Http\RedirectResponse;
use Livewire\Features\SupportRedirects\Redirector;

class LoginResponse implements Responsable
{
    public function toResponse($request): RedirectResponse|Redirector
    {
        $user = auth()->user();

        if ($user->hasRole('super_admin')) {
            return redirect()->to('/central');
        }

        $tenants = $user->tenants;

        if ($tenants->count() === 1) {
            return redirect()->to('/admin/' . $tenants->first()->slug);
        }

        // Jika user memiliki banyak tenant, biarkan Filament menangani pemilihan tenant default
        return redirect()->to('/admin');
    }
}
