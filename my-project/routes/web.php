<?php

use App\Http\Controllers\RegistrationController;
use Illuminate\Support\Facades\Route;

Route::get('/', function () {
    return view('welcome');
});

// 5. Registration & First Login Routes
Route::get('/register-lead', [RegistrationController::class, 'showRegistrationForm'])->name('registration.form');
Route::post('/register-lead', [RegistrationController::class, 'processRegistration'])->name('registration.process');

Route::get('/verify-otp/{lead}', [RegistrationController::class, 'showOTPForm'])->name('registration.verify');
Route::post('/verify-otp/{lead}', [RegistrationController::class, 'verifyOTP'])->name('registration.verify.process');

use App\Http\Controllers\FirstLoginController;

Route::middleware(['auth', 'ensure.password.changed'])->group(function () {
    Route::get('/first-login', [FirstLoginController::class, 'showChangePasswordForm'])->name('password.first-login')->withoutMiddleware('ensure.password.changed');
    Route::post('/first-login', [FirstLoginController::class, 'processChangePassword'])->name('password.first-login.process')->withoutMiddleware('ensure.password.changed');
    Route::get('/first-login/verify', [FirstLoginController::class, 'showVerifyForm'])->name('password.first-login.verify')->withoutMiddleware('ensure.password.changed');
    Route::post('/first-login/verify', [FirstLoginController::class, 'verifyOTP'])->name('password.first-login.verify.process')->withoutMiddleware('ensure.password.changed');
});


use App\Http\Controllers\BlogController;

Route::get('/blog', [BlogController::class, 'index'])->name('blog.index');
Route::get('/blog/{slug}', [BlogController::class, 'show'])->name('blog.show');

use App\Http\Controllers\TenantLandingController;
use App\Http\Controllers\CampaignController;

Route::get('/ppdb/{tenant_slug}/{campaign_slug}', [CampaignController::class, 'show'])->name('campaign.show');
Route::post('/ppdb/{tenant_slug}/{campaign_slug}/register', [CampaignController::class, 'register'])->name('campaign.register');
Route::get('/ppdb/{tenant_slug}/{campaign_slug}/success', [CampaignController::class, 'success'])->name('campaign.success');

Route::get('/{slug}', [TenantLandingController::class, 'show'])->name('tenant.landing');
