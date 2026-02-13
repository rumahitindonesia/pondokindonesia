<?php

namespace App\Services;

use App\Models\Tenant;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class StarSenderService
{
    protected $apiKey;
    protected $apiUrl;
    protected $tenant;

    public function __construct(?Tenant $tenant = null)
    {
        $this->tenant = $tenant;

        // Priority 1: Tenant specific API Key
        if ($tenant && $tenant->whatsapp_api_key) {
            $this->apiKey = $tenant->whatsapp_api_key;
        } else {
            // Priority 2: Global setting from database (inputted by Super Admin)
            $globalKey = \App\Models\Setting::get('starsender_api_key');
            // Priority 3: Fallback to .env config
            $this->apiKey = $globalKey ?: config('starsender.api_key');
        }

        $this->apiUrl = config('starsender.api_url');
    }

    /**
     * Check if WhatsApp is enabled for this tenant
     */
    public function isEnabled()
    {
        if (!$this->tenant) {
            return !empty($this->apiKey);
        }

        return $this->tenant->whatsapp_enabled && !empty($this->apiKey);
    }

    /**
     * Send OTP code via WhatsApp
     */
    public function sendOTP($phoneNumber, $otpCode, $institutionName)
    {
        $formattedPhone = $this->formatPhoneNumber($phoneNumber);

        $message = "Halo! Kode OTP Anda untuk verifikasi di *{$institutionName}* adalah:\n\n";
        $message .= "*{$otpCode}*\n\n";
        $message .= "Kode berlaku selama 5 menit.\n";
        $message .= "Jangan bagikan kode ini kepada siapapun.";

        return $this->sendMessage($formattedPhone, $message);
    }

    /**
     * Send message via StarSender API
     */
    public function sendMessage($phoneNumber, $message)
    {
        try {
            $phoneNumber = $this->formatPhoneNumber($phoneNumber);
            // Based on StarSender documentation example: https://api.starsender.online/api/send
            $url = $this->apiUrl; 

            $payload = [
                "messageType" => "text",
                "to" => $phoneNumber,
                "body" => $message,
                "delay" => 1, // small delay as in example
            ];

            Log::info('StarSender attempt', [
                'url' => $url,
                'phone' => $phoneNumber,
                'api_key_last_4' => substr($this->apiKey, -4)
            ]);

            $response = Http::withHeaders([
                'Content-Type' => 'application/json',
                'Authorization' => $this->apiKey,
            ])->post($url, $payload);

            if ($response->successful()) {
                Log::info('StarSender success', [
                    'phone' => $phoneNumber,
                    'response' => $response->json()
                ]);
                return [
                    'success' => true,
                    'data' => $response->json()
                ];
            }

            Log::error('StarSender API error', [
                'phone' => $phoneNumber,
                'status' => $response->status(),
                'response' => $response->body()
            ]);

            return [
                'success' => false,
                'error' => 'Failed to send message: ' . $response->body()
            ];

        }
        catch (\Exception $e) {
            Log::error('StarSender exception', [
                'phone' => $phoneNumber,
                'error' => $e->getMessage()
            ]);

            return [
                'success' => false,
                'error' => $e->getMessage()
            ];
        }
    }

    /**
     * Format phone number to international format (62xxx)
     */
    public function formatPhoneNumber($phone)
    {
        $phone = preg_replace('/[^0-9]/', '', $phone);
        if (substr($phone, 0, 1) === '0') {
            $phone = '62' . substr($phone, 1);
        }
        if (substr($phone, 0, 2) !== '62') {
            $phone = '62' . $phone;
        }
        return $phone;
    }

    /**
     * Generate random 6-digit OTP code
     */
    public static function generateOTP()
    {
        return str_pad(random_int(0, 999999), 6, '0', STR_PAD_LEFT);
    }

    /**
     * PPDB: Send Registration Confirmation
     */
    public function sendRegistrationConfirmation($lead)
    {
        $campaign = $lead->campaign;
        $tenantName = $this->tenant ? $this->tenant->name : 'Kami';
        
        $message = "Halo *{$lead->name}*!\n\n";
        $message .= "Terima kasih telah mendaftar di *{$tenantName}* untuk campaign: *{$campaign->title}*.\n\n";
        $message .= "Tim kami akan segera menghubungi Anda untuk tahap selanjutnya. Mohon pastikan nomor ini tetap aktif.\n\n";
        $message .= "Salam hangat,\n*{$tenantName}*";

        return $this->sendMessage($lead->whatsapp, $message);
    }

    /**
     * PPDB: Send Interview Schedule
     */
    public function sendInterviewSchedule($interview)
    {
        $lead = $interview->lead;
        $tenantName = $this->tenant ? $this->tenant->name : 'Kami';
        $date = $interview->scheduled_date->format('d M Y, H:i');
        
        $message = "Halo *{$lead->name}*!\n\n";
        $message .= "Jadwal interview Anda telah ditetapkan:\n";
        $message .= "📅 *{$date} WIB*\n";
        $message .= "📍 *{$interview->location}*\n\n";
        $message .= "Mohon hadir tepat waktu. Jika berhalangan, silakan hubungi admin kami.\n\n";
        $message .= "Salam,\n*{$tenantName}*";

        return $this->sendMessage($lead->whatsapp, $message);
    }

    /**
     * PPDB: Send Acceptance Notification
     */
    public function sendAcceptanceNotification($lead)
    {
        $tenantName = $this->tenant ? $this->tenant->name : 'Kami';
        
        $message = "🎉 *SELAMAT!* 🎉\n\n";
        $message .= "Halo *{$lead->name}*, Anda dinyatakan *LULUS* seleksi di *{$tenantName}*.\n\n";
        $message .= "Silakan lakukan pelunasan biaya pendidikan untuk mengaktifkan status santri Anda.\n\n";
        $message .= "Tim admin kami akan mengirimkan rincian pembayaran sesaat lagi.\n\n";
        $message .= "Selamat bergabung!\n*{$tenantName}*";

        return $this->sendMessage($lead->whatsapp, $message);
    }

    /**
     * PPDB: Send Payment Reminder
     */
    public function sendPaymentReminder($lead)
    {
        $tenantName = $this->tenant ? $this->tenant->name : 'Kami';
        $remaining = number_format($lead->remaining_amount);
        
        $message = "🔔 *PENGINGAT PEMBAYARAN* 🔔\n\n";
        $message .= "Halo *{$lead->name}*,\n";
        $message .= "Kami informasikan bahwa terdapat sisa kewajiban pembayaran sebesar:\n";
        $message .= "*Rp {$remaining}*\n\n";
        $message .= "Mohon segera melakukan pembayaran. Abaikan pesan ini jika Anda sudah melunasi.\n\n";
        $message .= "Terima kasih,\n*{$tenantName}*";

        return $this->sendMessage($lead->whatsapp, $message);
    }

    /**
     * PPDB: Send Payment Confirmation
     */
    public function sendPaymentConfirmation($lead, $amount)
    {
        $tenantName = $this->tenant ? $this->tenant->name : 'Kami';
        $formattedAmount = number_format($amount);
        
        $message = "✅ *PEMBAYARAN DITERIMA* ✅\n\n";
        $message .= "Halo *{$lead->name}*,\n";
        $message .= "Kami telah menerima pembayaran sebesar *Rp {$formattedAmount}*.\n\n";
        $message .= "Sisa tagihan Anda: *Rp " . number_format($lead->remaining_amount) . "*\n\n";
        $message .= "Terima kasih atas kepercayaannya.\n*{$tenantName}*";

        return $this->sendMessage($lead->whatsapp, $message);
    }

    /**
     * PPDB: Send Welcome Message
     */
    public function sendWelcomeMessage($lead)
    {
        $tenantName = $this->tenant ? $this->tenant->name : 'Kami';
        
        $message = "🎊 *SELAMAT DATANG SANTRI BARU* 🎊\n\n";
        $message .= "Ahlan wa Sahlan *{$lead->name}* di keluarga besar *{$tenantName}*!\n\n";
        $message .= "Status Anda sekarang telah resmi menjadi *SANTRI*. Informasi mengenai jadwal masuk dan seragam akan kami kirimkan kemudian.\n\n";
        $message .= "Semoga berkah dan sukses dalam menuntut ilmu.\n\n";
        $message .= "Salam,\n*{$tenantName}*";

        return $this->sendMessage($lead->whatsapp, $message);
    }

    /**
     * CRM: Send SPP Reminder
     */
    public function sendSPPReminder($invoice)
    {
        $santri = $invoice->santri;
        $tenantName = $this->tenant ? $this->tenant->name : 'Kami';
        $amount = number_format($invoice->amount);
        
        $message = "🔔 *PENGINGAT PEMBAYARAN SPP* 🔔\n\n";
        $message .= "Halo Orang Tua dari *{$santri->name}*,\n";
        $message .= "Kami menginformasikan tagihan SPP untuk periode *{$invoice->period}* sebesar:\n";
        $message .= "*Rp {$amount}*\n\n";
        $message .= "Mohon segera melakukan pembayaran sebelum tanggal *{$invoice->due_date->format('d M Y')}*.\n\n";
        $message .= "Terima kasih,\n*{$tenantName}*";

        return $this->sendMessage($santri->whatsapp, $message);
    }

    /**
     * CRM: Send Donor Reminder
     */
    public function sendDonorReminder($invoice)
    {
        $donor = $invoice->donor;
        $tenantName = $this->tenant ? $this->tenant->name : 'Kami';
        $amount = number_format($invoice->amount);
        
        $message = "💖 *PENGINGAT DONASI RUTIN* 💖\n\n";
        $message .= "Halo *{$donor->name}*,\n";
        $message .= "Terima kasih atas komitmen Anda untuk terus mendukung program kami.\n";
        $message .= "Berikut adalah informasi donasi rutin untuk periode *{$invoice->period}* sebesar:\n";
        $message .= "*Rp {$amount}*\n\n";
        $message .= "Semoga menjadi amal jariyah yang terus mengalir pahalanya. Aamiin.\n\n";
        $message .= "Salam hangat,\n*{$tenantName}*";

        return $this->sendMessage($donor->whatsapp, $message);
    }

    /**
     * CRM: Send Broadcast to Donors
     */
    public function sendDonorBroadcast($message)
    {
        $donors = \App\Models\Donor::where('tenant_id', $this->tenant->id)->get();
        $results = [];

        foreach ($donors as $donor) {
            if ($donor->whatsapp) {
                $personalizedMessage = str_replace('{name}', $donor->name, $message);
                $results[] = $this->sendMessage($donor->whatsapp, $personalizedMessage);
            }
        }

        return $results;
    }
}
