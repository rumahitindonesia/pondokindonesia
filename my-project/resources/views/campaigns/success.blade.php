<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pendaftaran Berhasil - {{ $tenant->name }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>body { font-family: 'Inter', sans-serif; }</style>
</head>
<body class="bg-gray-50 flex items-center justify-center min-h-screen">
    <div class="max-w-md w-full bg-white rounded-2xl shadow-xl overflow-hidden p-8 text-center">
        <div class="mb-6 inline-flex items-center justify-center w-20 h-20 bg-green-100 rounded-full text-green-600">
            <svg class="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg>
        </div>
        
        <h1 class="text-2xl font-bold text-gray-800 mb-4">Pendaftaran Berhasil!</h1>
        <p class="text-gray-600 mb-8">
            Terima kasih telah mendaftar di <strong>{{ $tenant->name }}</strong> untuk campaign <strong>{{ $campaign->title }}</strong>.
        </p>

        <div class="bg-indigo-50 rounded-xl p-6 mb-8 text-left border border-indigo-100">
            <h3 class="font-bold text-indigo-700 mb-2 flex items-center">
                <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20"><path d="M2 11.5a.5.5 0 01.5-.5h.758C3.676 10.33 4.5 9.232 4.5 8V6a6 6 0 1112 0v2c0 1.232.824 2.33 1.242 3h.758a.5.5 0 010 1H2.5a.5.5 0 01-.5-.5zM12 18a2 2 0 11-4 0h4z"></path></svg>
                Tahap Selanjutnya:
            </h3>
            <ul class="text-sm text-gray-700 space-y-3">
                <li class="flex items-start">
                    <span class="bg-indigo-600 text-white rounded-full w-5 h-5 flex items-center justify-center text-[10px] mr-2 mt-0.5 shrink-0">1</span>
                    <span>Admin kami akan menghubungi Anda melalui WhatsApp untuk verifikasi data.</span>
                </li>
                <li class="flex items-start">
                    <span class="bg-indigo-600 text-white rounded-full w-5 h-5 flex items-center justify-center text-[10px] mr-2 mt-0.5 shrink-0">2</span>
                    <span>Anda akan diminta melengkapi data pendaftaran santri secara detail.</span>
                </li>
                <li class="flex items-start">
                    <span class="bg-indigo-600 text-white rounded-full w-5 h-5 flex items-center justify-center text-[10px] mr-2 mt-0.5 shrink-0">3</span>
                    <span>Jadwal interview akan diinformasikan setelah verifikasi pendaftaran selesai.</span>
                </li>
            </ul>
        </div>

        <a href="{{ route('campaign.show', [$tenant->slug, $campaign->slug]) }}" class="inline-block text-indigo-600 font-semibold hover:text-indigo-800 transition">
            &larr; Kembali ke halaman utama
        </a>
    </div>
</body>
</html>
