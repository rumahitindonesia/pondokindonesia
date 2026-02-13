<?php

namespace App\Http\Responses;

use Filament\Http\Responses\Auth\Contracts\LogoutResponse as Responsable;
use Illuminate\Http\RedirectResponse;
use Symfony\Component\HttpFoundation\Response;

class LogoutResponse implements Responsable
{
    public function toResponse($request): Response | RedirectResponse
    {
        return redirect('/');
    }
}
