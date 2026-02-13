<?php

return [
    'api_key' => env('STARSENDER_API_KEY'),
    'api_url' => env('STARSENDER_API_URL', 'https://api.starsender.online/api/send'),

    // OTP Settings
    'otp_expiry_minutes' => env('STARSENDER_OTP_EXPIRY', 5),
    'max_otp_attempts' => env('STARSENDER_MAX_OTP_ATTEMPTS', 3),
    'max_resend_attempts' => env('STARSENDER_MAX_RESEND_ATTEMPTS', 3),
    'resend_cooldown_seconds' => env('STARSENDER_RESEND_COOLDOWN', 60),
];
