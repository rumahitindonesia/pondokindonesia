<x-guest-layout title='Verifikasi Ganti Password - Pondok Indonesia'>
    <div class='min-h-screen flex flex-col sm:justify-center items-center pt-6 sm:pt-0 bg-gray-100'>
        <div class='w-full sm:max-w-md mt-6 px-6 py-4 bg-white shadow-md overflow-hidden sm:rounded-lg'>
            <div class='mb-4 text-center'>
                <h2 class='text-2xl font-bold text-gray-900'>Konfirmasi OTP</h2>
                <p class='text-sm text-gray-600'>Kode OTP telah dikirim ke WhatsApp Lembaga Anda.</p>
            </div>

            @if ($errors->any())
                <div class='mb-4 font-medium text-sm text-red-600'>
                    <ul>
                        @foreach ($errors->all() as $error)
                            <li>{{ $error }}</li>
                        @endforeach
                    </ul>
                </div>
            @endif

            <form method='POST' action='{{ route('password.first-login.verify.process') }}'>
                @csrf

                <div class='mt-4'>
                    <label for='otp' class='block font-medium text-sm text-gray-700'>Kode OTP (6 Digit)</label>
                    <input id='otp' class='block mt-1 w-full border-gray-300 focus:border-indigo-500 focus:ring-indigo-500 rounded-md shadow-sm text-center text-2xl tracking-widest' type='text' name='otp' required maxlength='6' autofocus />
                </div>

                <div class='flex items-center justify-end mt-4'>
                    <button type='submit' class='w-full inline-flex items-center justify-center px-4 py-2 bg-indigo-600 border border-transparent rounded-md font-semibold text-xs text-white uppercase tracking-widest hover:bg-indigo-700 focus:bg-indigo-700 active:bg-indigo-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition ease-in-out duration-150'>
                        Konfirmasi & Masuk
                    </button>
                </div>
            </form>
        </div>
    </div>
</x-guest-layout>
