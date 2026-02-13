<?php

namespace App\Http\Controllers;

use App\Models\Tenant;
use Illuminate\Http\Request;

class TenantLandingController extends Controller
{
    public function show($slug)
    {
        $tenant = Tenant::where('slug', $slug)->firstOrFail();

        return view('tenants.landing', compact('tenant'));
    }
}
