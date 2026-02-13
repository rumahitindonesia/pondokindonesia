<?php

namespace App\Http\Controllers;

use App\Models\Campaign;
use App\Models\Lead;
use App\Models\Tenant;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;

class CampaignController extends Controller
{
    public function show(string $tenant_slug, string $campaign_slug)
    {
        $tenant = Tenant::where('slug', $tenant_slug)->firstOrFail();
        $campaign = $tenant->campaigns()
            ->where('slug', $campaign_slug)
            ->where('is_active', true)
            ->firstOrFail();

        // Capture affiliate ID from session or URL
        if (request()->has('aff_id')) {
            session(['aff_id' => request('aff_id')]);
        }

        return view('campaigns.show', compact('tenant', 'campaign'));
    }

    public function register(Request $request, string $tenant_slug, string $campaign_slug)
    {
        $tenant = Tenant::where('slug', $tenant_slug)->firstOrFail();
        $campaign = $tenant->campaigns()
            ->where('slug', $campaign_slug)
            ->where('is_active', true)
            ->firstOrFail();

        $validator = Validator::make($request->all(), [
            'name' => 'required|string|max:255',
            'email' => 'required|email|max:255',
            'whatsapp' => 'required|string|max:20',
            'institution_name' => 'nullable|string|max:255',
            'message' => 'nullable|string',
        ]);

        if ($validator->fails()) {
            return back()->withErrors($validator)->withInput();
        }

        $lead = Lead::create([
            'campaign_id' => $campaign->id,
            'aff_id' => session('aff_id') ?? $request->aff_id ?? $campaign->aff_id,
            'name' => $request->name,
            'email' => $request->email,
            'whatsapp' => $request->whatsapp,
            'institution_name' => $request->institution_name,
            'message' => $request->message,
            'status' => 'new',
        ]);

        // Trigger WhatsApp Notification
        $service = new \App\Services\StarSenderService($tenant);
        if ($service->isEnabled()) {
            $service->sendRegistrationConfirmation($lead);
        }

        return redirect()->route('campaign.success', [$tenant_slug, $campaign_slug])
            ->with('success', 'Pendaftaran Anda berhasil! Tim kami akan segera menghubungi Anda melalui WhatsApp.');
    }

    public function success(string $tenant_slug, string $campaign_slug)
    {
        $tenant = Tenant::where('slug', $tenant_slug)->firstOrFail();
        $campaign = $tenant->campaigns()->where('slug', $campaign_slug)->firstOrFail();

        return view('campaigns.success', compact('tenant', 'campaign'));
    }
}
