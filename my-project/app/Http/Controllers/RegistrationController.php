<?php

namespace App\Http\Controllers;

use App\Models\Lead;
use App\Models\User;
use App\Models\Tenant;
use App\Services\StarSenderService;
use Carbon\Carbon;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Str;

class RegistrationController extends Controller
{
    public function showRegistrationForm()
    {
        return view('auth.register-lead');
    }

    public function processRegistration(Request $request, StarSenderService $starSender)
    {
        $validated = $request->validate([
            'name' => 'required|string|max:255',
            'email' => 'required|email|max:255|unique:users,email',
            'whatsapp' => 'required|string|max:20',
            'institution_name' => 'required|string|max:255',
        ]);

        $otp = StarSenderService::generateOTP();
        $expiresAt = Carbon::now()->addMinutes(10);

        $lead = Lead::create([
            'name' => $validated['name'],
            'email' => $validated['email'],
            'whatsapp' => $validated['whatsapp'],
            'institution_name' => $validated['institution_name'],
            'status' => 'new',
            'otp_code' => $otp,
            'otp_expires_at' => $expiresAt,
            'is_verified' => false,
        ]);

        // Send OTP via WhatsApp
        $starSender->sendOTP($lead->whatsapp, $otp, $lead->institution_name);

        return redirect()->route('registration.verify', $lead);
    }

    public function showOTPForm(Lead $lead)
    {
        return view('auth.verify-otp', compact('lead'));
    }

    public function verifyOTP(Request $request, Lead $lead, StarSenderService $starSender)
    {
        $request->validate([
            'otp' => 'required|string|size:6',
        ]);

        if ($request->otp !== $lead->otp_code) {
            return back()->withErrors(['otp' => 'Kode OTP salah.']);
        }

        if (Carbon::now()->isAfter($lead->otp_expires_at)) {
            return back()->withErrors(['otp' => 'Kode OTP telah kadaluarsa. Silakan daftar ulang.']);
        }

        DB::transaction(function () use ($lead, $starSender) {
            // Update Lead Status
            $lead->update([
                'is_verified' => true,
                'status' => 'verified',
                'otp_code' => null, // Clear OTP after usage
            ]);

            // Create Tenant
            $tenant = Tenant::create([
                'name' => $lead->institution_name,
                'slug' => Str::slug($lead->institution_name),
                'whatsapp_number' => $lead->whatsapp,
                'whatsapp_enabled' => true,
            ]);

            // Generate Random Password
            $plainPassword = Str::random(8);

            // Create User (Admin)
            $user = User::create([
                'name' => $lead->name,
                'email' => $lead->email,
                'password' => Hash::make($plainPassword),
                'must_change_password' => true,
            ]);
            
            // Attach User to Tenant
            $user->tenants()->attach($tenant);
            
            // Assign Role (using Spatie assignRole)
            if (method_exists($user, 'assignRole')) {
                // Try 'Admin Tenant' first as it exists in DB, then 'admin'
                if (\Spatie\Permission\Models\Role::where('name', 'Admin Tenant')->exists()) {
                    $user->assignRole('Admin Tenant');
                } else {
                    $role = \Spatie\Permission\Models\Role::firstOrCreate(['name' => 'admin', 'guard_name' => 'web']);
                    $user->assignRole($role->name);
                }
            }

            // Send Credentials via WhatsApp
            $message = "Selamat! Pendaftaran *{$lead->institution_name}* berhasil.\n\n";
            $message .= "Berikut akses login Anda:\n";
            $message .= "Email: *{$lead->email}*\n";
            $message .= "Password: *{$plainPassword}*\n\n";
            $message .= "Silakan login di: " . route('filament.admin.auth.login') . "\n";
            $message .= "Anda akan diminta mengganti password saat login pertama.";
            
            $starSender->sendMessage($lead->whatsapp, $message);
        });

        return redirect()->route('filament.admin.auth.login')
            ->with('success', 'Verifikasi berhasil! Detail login telah dikirim ke WhatsApp Anda.');
    }
}
