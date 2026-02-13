<x-guest-layout title='Pendaftaran Gratis - Pondok Indonesia'>
    <style type="text/tailwindcss">
        @layer base {
            body { @apply bg-white; }
        }
        .text-gradient { @apply bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-cyan-500; }
        .glass-card { @apply bg-white/80 backdrop-blur-xl border border-white shadow-2xl shadow-indigo-100/50; }
    </style>

    <div class='min-h-screen relative overflow-hidden flex items-center py-12 lg:py-20'>
        <!-- Animated Background Elements -->
        <div class="absolute inset-0 pointer-events-none overflow-hidden">
            <div class="absolute -top-24 -left-24 w-96 h-96 bg-indigo-50 rounded-full mix-blend-multiply filter blur-3xl opacity-70 animate-blob"></div>
            <div class="absolute -bottom-24 -right-24 w-96 h-96 bg-cyan-50 rounded-full mix-blend-multiply filter blur-3xl opacity-70 animate-blob animation-delay-2000"></div>
        </div>

        <div class='container mx-auto px-4 relative z-10'>
            <div class='max-w-6xl mx-auto'>
                <div class='grid lg:grid-cols-12 gap-16 items-center'>
                    
                    <!-- Left Side: Content & Trust -->
                    <div class='lg:col-span-5 space-y-12'>
                        <div>
                            <div class="inline-flex items-center px-3 py-1 rounded-full bg-emerald-50 border border-emerald-100 mb-6 font-bold text-emerald-700 text-[10px] uppercase tracking-widest leading-none">
                                <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-2"></span>
                                Pendaftaran 100% Gratis
                            </div>
                            <h1 class='text-5xl md:text-6xl font-black text-slate-900 mb-6 leading-[1.1] tracking-tight'>
                                Mulai Langkah <span class='text-gradient'>Digital</span> Pesantren Anda.
                            </h1>
                            <p class='text-lg text-slate-600 font-medium leading-relaxed mb-8'>
                                Wujudkan kemandirian ekonomi dan silaturahmi yang lebih erat dengan santri serta donatur melalui teknologi AI.
                            </p>
                            
                            <div class="flex items-center gap-4 text-sm font-bold text-slate-400">
                                <div class="flex -space-x-2">
                                    <div class="w-8 h-8 rounded-full bg-slate-200 border-2 border-white flex items-center justify-center text-[10px] text-slate-600">AH</div>
                                    <div class="w-8 h-8 rounded-full bg-indigo-100 border-2 border-white flex items-center justify-center text-[10px] text-indigo-600">ZA</div>
                                    <div class="w-8 h-8 rounded-full bg-emerald-100 border-2 border-white flex items-center justify-center text-[10px] text-emerald-600">+50</div>
                                </div>
                                <p>Telah bergabung di berbagai kota</p>
                            </div>
                        </div>

                        <!-- Benefits List -->
                        <div class="space-y-8">
                            <div class="flex gap-5">
                                <div class="w-12 h-12 rounded-2xl bg-white shadow-lg border border-slate-50 flex items-center justify-center text-indigo-600 flex-shrink-0">
                                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path></svg>
                                </div>
                                <div>
                                    <h4 class="font-bold text-slate-900 mb-1">WhatsApp Automation</h4>
                                    <p class="text-sm text-slate-500 leading-relaxed">Kirim laporan, OTP, dan pesan kasih sayang otomatis ke wali santri.</p>
                                </div>
                            </div>
                            <div class="flex gap-5">
                                <div class="w-12 h-12 rounded-2xl bg-white shadow-lg border border-slate-50 flex items-center justify-center text-cyan-500 flex-shrink-0">
                                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                                </div>
                                <div>
                                    <h4 class="font-bold text-slate-900 mb-1">Personal AI Assistant</h4>
                                    <p class="text-sm text-slate-500 leading-relaxed">Setiap pesan silaturahmi terasa personal dan hangat berkat kecerdasan buatan.</p>
                                </div>
                            </div>
                            <div class="flex gap-5">
                                <div class="w-12 h-12 rounded-2xl bg-white shadow-lg border border-slate-50 flex items-center justify-center text-emerald-500 flex-shrink-0">
                                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                                </div>
                                <div>
                                    <h4 class="font-bold text-slate-900 mb-1">Cepat & Transparan</h4>
                                    <p class="text-sm text-slate-500 leading-relaxed">Monitor donasi dan database pesantren kapan saja dalam hitungan detik.</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Right Side: Registration Form -->
                    <div class='lg:col-span-7 flex justify-center lg:justify-end'>
                        <div class='w-full max-w-xl glass-card rounded-[3rem] p-10 lg:p-12 border-2 border-slate-50'>
                            <div class='mb-10'>
                                <h2 class='text-3xl font-black text-slate-900 mb-3'>Form Pendaftaran</h2>
                                <p class='text-slate-500 font-medium'>Siapkan data pesantren Anda untuk memulai pengalaman baru.</p>
                            </div>

                            <form method='POST' action='{{ route('registration.process') }}' class='space-y-6'>
                                @csrf
                                <div class="grid md:grid-cols-2 gap-6">
                                    <div class="col-span-2">
                                        <label class='block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2 ml-1'>Nama Pesantren / Lembaga</label>
                                        <input class='w-full px-6 py-4 rounded-2xl bg-slate-50 border-transparent focus:bg-white focus:ring-4 focus:ring-indigo-100 transition-all text-slate-700 font-semibold' type='text' name='institution_name' value='{{ old("institution_name") }}' required placeholder='Contoh: Ponpes Al-Amanah' />
                                        @error('institution_name') <p class='mt-2 text-xs text-rose-500'>{{ $message }}</p> @enderror
                                    </div>

                                    <div>
                                        <label class='block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2 ml-1'>Nama Admin</label>
                                        <input class='w-full px-6 py-4 rounded-2xl bg-slate-50 border-transparent focus:bg-white focus:ring-4 focus:ring-indigo-100 transition-all text-slate-700 font-semibold' type='text' name='name' value='{{ old("name") }}' required placeholder='Ustadz/Hj. ...' />
                                        @error('name') <p class='mt-2 text-xs text-rose-500'>{{ $message }}</p> @enderror
                                    </div>

                                    <div>
                                        <label class='block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2 ml-1'>Email Aktif</label>
                                        <input class='w-full px-6 py-4 rounded-2xl bg-slate-50 border-transparent focus:bg-white focus:ring-4 focus:ring-indigo-100 transition-all text-slate-700 font-semibold' type='email' name='email' value='{{ old("email") }}' required placeholder='admin@ponpes.id' />
                                        @error('email') <p class='mt-2 text-xs text-rose-500'>{{ $message }}</p> @enderror
                                    </div>

                                    <div class="col-span-2">
                                        <label class='block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2 ml-1'>Nomor WhatsApp (Wajib Aktif)</label>
                                        <div class="relative">
                                            <span class="absolute left-6 top-1/2 -translate-y-1/2 font-bold text-slate-400">+62</span>
                                            <input class='w-full pl-16 pr-6 py-4 rounded-2xl bg-slate-50 border-transparent focus:bg-white focus:ring-4 focus:ring-indigo-100 transition-all text-slate-700 font-semibold' type='text' name='whatsapp' value='{{ old("whatsapp") }}' required placeholder='8123456789' />
                                        </div>
                                        <p class="mt-2 text-[10px] text-slate-400 ml-1 italic">*Kami akan mengirimkan kode verifikasi (OTP) ke nomor ini.</p>
                                        @error('whatsapp') <p class='mt-2 text-xs text-rose-500'>{{ $message }}</p> @enderror
                                    </div>
                                </div>

                                <div class='pt-6'>
                                    <button type='submit' class='w-full py-5 bg-indigo-600 hover:bg-slate-900 text-white font-bold rounded-[1.25rem] transition-all shadow-2xl shadow-indigo-100 transform hover:-translate-y-1 active:scale-95'>
                                        Daftar Sekarang - Gratis 100%
                                    </button>
                                </div>

                                <div class='pt-8 border-t border-slate-100 mt-6'>
                                    <div class="flex items-start gap-4 p-4 rounded-2xl bg-slate-50/50">
                                        <div class="w-8 h-8 rounded-full bg-white flex items-center justify-center flex-shrink-0 shadow-sm">
                                            <svg class="w-4 h-4 text-emerald-500" fill="currentColor" viewBox="0 0 20 20"><path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z"></path><path fill-rule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clip-rule="evenodd"></path></svg>
                                        </div>
                                        <p class='text-[10px] text-slate-400 italic leading-relaxed'>
                                            "Pendaftaran ini sangat membantu keuangan pondok kami. Transparan dan otomatis." - <strong>Hj. Maryam</strong>, Bendahara Ponpes Modern.
                                        </p>
                                    </div>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</x-guest-layout>
