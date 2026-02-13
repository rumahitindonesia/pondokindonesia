<x-guest-layout title='Verifikasi OTP - Pondok Indonesia'>
    <div class='min-h-screen bg-slate-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden'>
        <div class="absolute inset-0 opacity-5 pointer-events-none">
            <div class="absolute top-0 left-0 w-96 h-96 bg-indigo-600 rounded-full filter blur-3xl"></div>
            <div class="absolute bottom-0 right-0 w-96 h-96 bg-cyan-500 rounded-full filter blur-3xl"></div>
        </div>

        <div class='max-w-md w-full space-y-8 relative z-10'>
            <div class='bg-white rounded-[2.5rem] p-10 shadow-2xl shadow-indigo-100 border border-slate-100'>
                <div class='text-center mb-10'>
                    <div class='w-20 h-20 bg-indigo-50 text-indigo-600 rounded-3xl flex items-center justify-center mx-auto mb-6'>
                        <svg class='w-10 h-10' fill='none' stroke='currentColor' viewBox='0 0 24 24'><path stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z'></path></svg>
                    </div>
                    <h2 class='text-3xl font-black text-slate-900 mb-2'>Verifikasi Akun</h2>
                    <p class='text-slate-500 font-medium'>Kami telah mengirimkan kode OTP ke nomor WhatsApp <strong>{{ $lead->whatsapp }}</strong></p>
                </div>

                @if (session('error'))
                    <div class='mb-6 p-4 bg-rose-50 border border-rose-100 rounded-2xl'>
                        <p class='text-sm text-rose-600 font-bold'>{{ session('error') }}</p>
                    </div>
                @endif

                <form method='POST' action='{{ route('registration.verify.process', $lead) }}' class='space-y-8'>
                    @csrf
                    <div>
                        <label class='block text-xs font-bold text-slate-400 uppercase tracking-widest text-center mb-6'>Masukkan 6 Digit Kode OTP</label>
                        <input class='w-full px-6 py-5 rounded-2xl bg-slate-50 border-transparent focus:bg-white focus:ring-4 focus:ring-indigo-100 transition-all text-center text-3xl font-black tracking-[1em] text-indigo-600' 
                               type='text' 
                               name='otp_code' 
                               maxlength='6' 
                               required 
                               autofocus 
                               autocomplete="one-time-code"
                               placeholder='000000' />
                        @error('otp_code') <p class='mt-3 text-xs text-rose-500 text-center'>{{ $message }}</p> @enderror
                    </div>

                    <button type='submit' class='w-full py-5 bg-indigo-600 hover:bg-slate-900 text-white font-bold rounded-2xl transition-all shadow-xl shadow-indigo-200 transform hover:-translate-y-1'>
                        Verifikasi Sekarang
                    </button>
                </form>

                <div class='mt-10 text-center'>
                    <p class='text-xs text-slate-400'>
                        Tidak menerima kode? 
                        <a href='#' class='text-indigo-600 font-bold hover:underline'>Kirim Ulang</a>
                    </p>
                </div>
            </div>
            
            <div class="text-center">
                <a href="/" class="text-sm font-bold text-slate-400 hover:text-indigo-600 transition-colors">← Kembali ke Beranda</a>
            </div>
        </div>
    </div>
</x-guest-layout>
