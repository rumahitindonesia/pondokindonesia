<?php

namespace App\Http\Controllers;

use App\Models\User;
use App\Models\Tenant;
use App\Services\StarSenderService;
use Carbon\Carbon;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\Rules\Password;

class FirstLoginController extends Controller
{
    public function showChangePasswordForm(Request $request)
    {
        return view('auth.first-login');
    }

    public function processChangePassword(Request $request, StarSenderService $starSender)
    {
        $validated = $request->validate([
            'password' => ['required', 'confirmed', Password::defaults()],
        ]);
        
        $user = $request->user();
        $tenant = $user->tenants->first();

        if (!$tenant || !$tenant->whatsapp_number) {
             return back()->withErrors(['password' => 'Nomor WhatsApp institusi tidak ditemukan. Hubungi Super Admin.']);
        }

        // Generate OTP
        $otp = StarSenderService::generateOTP();
        $expiresAt = Carbon::now()->addMinutes(10);
        
        // Store in session
        $request->session()->put('change_password_otp', $otp);
        $request->session()->put('change_password_expires', $expiresAt);
        $request->session()->put('new_password', $validated['password']);

        // Send OTP
        $message = "Kode OTP untuk konfirmasi perubahan password Anda adalah: *{$otp}*.";
        $starSender->sendMessage($tenant->whatsapp_number, $message);

        return redirect()->route('password.first-login.verify');
    }

    public function showVerifyForm()
    {
        if (!session()->has('change_password_otp')) {
            return redirect()->route('password.first-login');
        }
        return view('auth.first-login-verify');
    }

    public function verifyOTP(Request $request)
    {
        $request->validate([
            'otp' => 'required|string|size:6',
        ]);

        $sessionOtp = session('change_password_otp');
        $sessionExpires = session('change_password_expires');
        $newPassword = session('new_password');

        if (!$sessionOtp || !$newPassword) {
            return redirect()->route('password.first-login')->withErrors(['otp' => 'Sesi kadaluarsa. Silakan ulangi.']);
        }

        if ($request->otp !== $sessionOtp) {
            return back()->withErrors(['otp' => 'Kode OTP salah.']);
        }

        if (Carbon::now()->isAfter($sessionExpires)) {
            return back()->withErrors(['otp' => 'Kode OTP kadaluarsa.']);
        }

        // Update Password
        $user = $request->user();
        $user->password = Hash::make($newPassword);
        $user->must_change_password = false;
        $user->save();

        // Clear Session
        $request->session()->forget(['change_password_otp', 'change_password_expires', 'new_password']);

        return redirect()->route('filament.admin.pages.dashboard')
            ->with('success', 'Password berhasil diubah. Selamat datang!');
    }
}
